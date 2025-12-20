import cv2
import numpy as np
import math
import json

# --- TUNING ---
MERGE_ALIGN_TOL = 20
MERGE_GAP_TOL = 50
STITCH_GAP_TOL = 60
STITCH_ALIGN_TOL = 10

# Diagonal Settings
PATH_WIDTH_TOL = 40.0      # Pixels
PATH_GAP_TOL = 100.0       # Pixels

# Snapping Tolerances
CORNER_SNAP_DIST = 45      # px
DIAG_SNAP_DIST = 60        # px
FUSE_DIST = 30             # px (Final cleanup for close points)

# --- HELPER MATH ---
def get_dist_point_to_line(px, py, x1, y1, x2, y2):
    line_mag = math.hypot(x2 - x1, y2 - y1)
    if line_mag < 1e-5: return math.hypot(px - x1, py - y1)
    val = (y2 - y1)*px - (x2 - x1)*py + x2*y1 - y2*x1
    return abs(val) / line_mag

def get_line_params(line):
    x1, y1, x2, y2 = line
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    if angle < 0: angle += 180
    return angle

def get_intersection(l1, l2):
    x1, y1, x2, y2 = map(float, l1)
    x3, y3, x4, y4 = map(float, l2)
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if abs(denom) < 1e-5: return None
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    return (x1 + ua * (x2 - x1), y1 + ua * (y2 - y1))

# --- 1. V/H PROCESSING ---
def merge_parallel_lines(lines, orientation='horizontal'):
    if not lines: return []
    norm_lines = [[*l] for l in lines]
    idx_align = 1 if orientation == 'horizontal' else 0
    idx_start = 0 if orientation == 'horizontal' else 1
    norm_lines.sort(key=lambda l: (l[idx_align], l[idx_start]))

    merged = []
    while norm_lines:
        current = norm_lines.pop(0)
        i = 0
        while i < len(norm_lines):
            cand = norm_lines[i]
            pos_diff = abs(current[idx_align] - cand[idx_align])
            if pos_diff <= MERGE_ALIGN_TOL:
                c_start, c_end = min(current[idx_start], current[idx_start+2]), max(current[idx_start], current[idx_start+2])
                n_start, n_end = min(cand[idx_start], cand[idx_start+2]), max(cand[idx_start], cand[idx_start+2])
                if (c_end + MERGE_GAP_TOL >= n_start) and (n_end + MERGE_GAP_TOL >= c_start):
                    new_start = min(c_start, n_start)
                    new_end = max(c_end, n_end)
                    new_pos = (current[idx_align] + cand[idx_align]) // 2
                    if orientation == 'horizontal': current = [new_start, new_pos, new_end, new_pos]
                    else:                           current = [new_pos, new_start, new_pos, new_end]
                    norm_lines.pop(i)
                    continue 
            i += 1
        merged.append(current)
    return merged

def stitch_sequential_lines(lines, orientation='horizontal'):
    if not lines: return []
    idx_align = 1 if orientation == 'horizontal' else 0
    idx_start = 0 if orientation == 'horizontal' else 1
    buckets = []
    processed = [False] * len(lines)
    for i in range(len(lines)):
        if processed[i]: continue
        bucket = [lines[i]]
        processed[i] = True
        for j in range(i + 1, len(lines)):
            if processed[j]: continue
            if abs(lines[i][idx_align] - lines[j][idx_align]) < STITCH_ALIGN_TOL:
                bucket.append(lines[j])
                processed[j] = True
        buckets.append(bucket)
    final_lines = []
    for bucket in buckets:
        bucket.sort(key=lambda l: min(l[idx_start], l[idx_start+2]))
        if not bucket: continue
        curr = bucket[0]
        c_min = min(curr[idx_start], curr[idx_start+2])
        c_max = max(curr[idx_start], curr[idx_start+2])
        avg_pos = curr[idx_align]
        count = 1
        for k in range(1, len(bucket)):
            next_l = bucket[k]
            n_min = min(next_l[idx_start], next_l[idx_start+2])
            n_max = max(next_l[idx_start], next_l[idx_start+2])
            if n_min <= c_max + STITCH_GAP_TOL:
                c_max = max(c_max, n_max)
                avg_pos += next_l[idx_align]
                count += 1
            else:
                final_pos = int(avg_pos / count)
                if orientation == 'horizontal': final_lines.append([c_min, final_pos, c_max, final_pos])
                else:                           final_lines.append([final_pos, c_min, final_pos, c_max])
                curr = next_l
                c_min, c_max = n_min, n_max
                avg_pos = curr[idx_align]
                count = 1
        final_pos = int(avg_pos / count)
        if orientation == 'horizontal': final_lines.append([c_min, final_pos, c_max, final_pos])
        else:                           final_lines.append([final_pos, c_min, final_pos, c_max])
    return final_lines

# --- 2. DIAGONAL MERGE (WOBBLE LOGIC) ---
def merge_diagonals_wobble(lines):
    if not lines: return []
    current_lines = [list(map(float, l)) for l in lines]
    changed = True
    while changed:
        changed = False
        new_lines = []
        used = [False] * len(current_lines)
        current_lines.sort(key=lambda l: math.hypot(l[2]-l[0], l[3]-l[1]), reverse=True)
        
        for i in range(len(current_lines)):
            if used[i]: continue
            base = current_lines[i]
            used[i] = True
            bx1, by1, bx2, by2 = base
            cluster_pts = [(bx1, by1), (bx2, by2)]
            
            for j in range(i + 1, len(current_lines)):
                if used[j]: continue
                cand = current_lines[j]
                cx1, cy1, cx2, cy2 = cand
                angle_base = get_line_params(base)
                angle_cand = get_line_params(cand)
                diff = abs(angle_base - angle_cand)
                if diff > 170: diff = abs(diff - 180)
                if diff > 15.0: continue 
                
                d1 = get_dist_point_to_line(cx1, cy1, bx1, by1, bx2, by2)
                d2 = get_dist_point_to_line(cx2, cy2, bx1, by1, bx2, by2)
                
                if d1 < PATH_WIDTH_TOL and d2 < PATH_WIDTH_TOL:
                    dist_gap = min(
                        math.hypot(cx1-bx1, cy1-by1), math.hypot(cx1-bx2, cy1-by2),
                        math.hypot(cx2-bx1, cy2-by1), math.hypot(cx2-bx2, cy2-by2)
                    )
                    if dist_gap < PATH_GAP_TOL:
                        cluster_pts.append((cx1, cy1))
                        cluster_pts.append((cx2, cy2))
                        used[j] = True
                        changed = True
            
            if len(cluster_pts) > 2:
                best_p1, best_p2 = cluster_pts[0], cluster_pts[0]
                max_d = 0
                for p1 in cluster_pts:
                    for p2 in cluster_pts:
                        d = (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
                        if d > max_d:
                            max_d = d
                            best_p1, best_p2 = p1, p2
                new_lines.append([best_p1[0], best_p1[1], best_p2[0], best_p2[1]])
            else:
                new_lines.append(base)
        current_lines = new_lines
    return [list(map(int, l)) for l in current_lines]

# --- 3. CONNECTION LOGIC (LOCK & KEY) ---

def connect_corners_vh_and_lock(verticals, horizontals):
    locked_points = set()
    verts = [list(l) for l in verticals]
    horzs = [list(l) for l in horizontals]
    
    for v in verts:
        vx, vy1, vy2 = v[0], min(v[1], v[3]), max(v[1], v[3])
        for h in horzs:
            hx1, hx2, hy = min(h[0], h[2]), max(h[0], h[2]), h[1]
            
            v_near_h = (abs(vy1 - hy) < CORNER_SNAP_DIST) or (abs(vy2 - hy) < CORNER_SNAP_DIST)
            h_near_v = (abs(hx1 - vx) < CORNER_SNAP_DIST) or (abs(hx2 - vx) < CORNER_SNAP_DIST)
            v_in_h = (hx1 - 10 <= vx <= hx2 + 10)
            h_in_v = (vy1 - 10 <= hy <= vy2 + 10)
            
            snap_pt = None
            
            if v_near_h and h_near_v: # L-Corner
                if abs(vy1 - hy) < abs(vy2 - hy): v[1] = hy 
                else:                             v[3] = hy
                if abs(hx1 - vx) < abs(hx2 - vx): h[0] = vx
                else:                             h[2] = vx
                snap_pt = (vx, hy)
                
            elif v_near_h and v_in_h: # T (V hits H)
                if abs(vy1 - hy) < abs(vy2 - hy): v[1] = hy
                else:                             v[3] = hy
                snap_pt = (vx, hy)
                
            elif h_near_v and h_in_v: # T (H hits V)
                if abs(hx1 - vx) < abs(hx2 - vx): h[0] = vx
                else:                             h[2] = vx
                snap_pt = (vx, hy)
                
            if snap_pt:
                locked_points.add((int(snap_pt[0]), int(snap_pt[1])))
                
    return verts, horzs, locked_points

def is_locked(pt, locked_set):
    for lp in locked_set:
        if abs(pt[0]-lp[0]) < 5 and abs(pt[1]-lp[1]) < 5: return True
    return False

def snap_diagonal_ends_to_locked_corners(diagonals, locked_set):
    # Snap diagonal ends to nearby LOCKED corners
    for d in diagonals:
        for i in [0, 2]:
            dx, dy = d[i], d[i+1]
            best_dist = DIAG_SNAP_DIST
            best_lock = None
            for lx, ly in locked_set:
                dist = math.hypot(dx - lx, dy - ly)
                if dist < best_dist:
                    best_dist = dist
                    best_lock = (lx, ly)
            if best_lock:
                d[i], d[i+1] = best_lock

def snap_free_vh_to_diagonal(orthos, diagonals, locked_set):
    for o in orthos:
        for i in [0, 2]:
            ox, oy = o[i], o[i+1]
            if is_locked((ox, oy), locked_set): continue 
            
            best_dist = DIAG_SNAP_DIST
            best_int = None
            
            for d in diagonals:
                inter = get_intersection(o, d)
                if inter:
                    ix, iy = inter
                    dist = math.hypot(ox - ix, oy - iy)
                    if dist < best_dist:
                        dx_min, dx_max = min(d[0], d[2]), max(d[0], d[2])
                        dy_min, dy_max = min(d[1], d[3]), max(d[1], d[3])
                        if (dx_min - 20 <= ix <= dx_max + 20) and (dy_min - 20 <= iy <= dy_max + 20):
                            best_dist = dist
                            best_int = (int(ix), int(iy))
            if best_int:
                o[i], o[i+1] = best_int

def fuse_close_endpoints(lines):
    # NEW FIX: Brute force snap for stubborn gaps (like your roof peak)
    # Checks every endpoint against every other endpoint
    points = []
    for i, l in enumerate(lines):
        points.append({'idx':i, 'pos':0, 'x':l[0], 'y':l[1]})
        points.append({'idx':i, 'pos':1, 'x':l[2], 'y':l[3]})
        
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            p1 = points[i]
            p2 = points[j]
            
            # Don't fuse points of the same line
            if p1['idx'] == p2['idx']: continue
            
            dist = math.hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])
            
            if dist < FUSE_DIST:
                # Snap to average
                avg_x = (p1['x'] + p2['x']) // 2
                avg_y = (p1['y'] + p2['y']) // 2
                
                # Update P1 in the points list AND the original line
                p1['x'], p1['y'] = avg_x, avg_y
                line1 = lines[p1['idx']]
                if p1['pos'] == 0: line1[0], line1[1] = avg_x, avg_y
                else:              line1[2], line1[3] = avg_x, avg_y
                
                # Update P2
                p2['x'], p2['y'] = avg_x, avg_y
                line2 = lines[p2['idx']]
                if p2['pos'] == 0: line2[0], line2[1] = avg_x, avg_y
                else:              line2[2], line2[3] = avg_x, avg_y
    return lines

def process_map_final(img_path):
    img = cv2.imread(img_path, 0)
    lines = cv2.HoughLinesP(img, 1, np.pi/180, threshold=8, minLineLength=10, maxLineGap=20)
    
    horizontal, vertical, others = [], [], []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if angle < 0: angle += 180
        if 80 <= angle <= 100:
            avg_x = (x1 + x2) // 2
            vertical.append([avg_x, y1, avg_x, y2])
        elif angle <= 10 or angle >= 170:
            avg_y = (y1 + y2) // 2
            horizontal.append([x1, avg_y, x2, avg_y])
        else:
            others.append([x1, y1, x2, y2])

    # 1. Process V/H
    final_v = merge_parallel_lines(vertical, 'vertical')
    final_h = merge_parallel_lines(horizontal, 'horizontal')
    final_v = stitch_sequential_lines(final_v, 'vertical')
    final_h = stitch_sequential_lines(final_h, 'horizontal')
    
    # 2. Connect V-H & Lock
    final_v, final_h, locked_set = connect_corners_vh_and_lock(final_v, final_h)
    
    # 3. Process Diagonals
    final_o = merge_diagonals_wobble(others)
    
    # 4. Snap Diagonals to Locked Corners
    snap_diagonal_ends_to_locked_corners(final_o, locked_set)

    # 5. Snap Free V/H Ends -> Diagonals
    snap_free_vh_to_diagonal(final_v + final_h, final_o, locked_set)
    
    # 6. FUSE (The Fix for Stubborn Gaps)
    all_lines = final_v + final_h + final_o
    all_lines = fuse_close_endpoints(all_lines)

    # Export
    vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    json_data = []

    for line in all_lines:
        x1, y1, x2, y2 = map(int, line)
        color = (0, 255, 0) if (x1==x2 or y1==y2) else (0, 0, 255)
        cv2.line(vis_img, (x1, y1), (x2, y2), color, 2)
        cv2.circle(vis_img, (x1, y1), 3, (0, 0, 255), -1)
        cv2.circle(vis_img, (x2, y2), 3, (0, 0, 255), -1)
        json_data.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})

    cv2.imwrite('floorplan_master_fused.jpg', vis_img)
    with open('floorplan_master_fused.json', 'w') as f:
        json.dump(json_data, f, indent=2)

process_map_final('skeleton.png')