import json
import math

# --- TUNING ---
# 1. Grid Fusion Threshold: Points within this range fuse to one grid line
GLOBAL_ALIGN_THRESHOLD = 20 

# 2. Skew Correction: Lines with this much slant are forced straight
# You asked for 15 units.
SKEW_TOLERANCE = 15 

def align_walls_globally(input_path, output_path):
    try:
        with open(input_path, 'r') as f:
            lines = json.load(f)
    except FileNotFoundError:
        print("Error: Input file not found.")
        return

    # --- STEP 1: GENERATE MASTER GRID ---
    # We collect X and Y coordinates from any line that looks "roughly" straight.
    v_x_coords = []
    h_y_coords = []

    skewed_lines_detected = 0

    for line in lines:
        x1, y1, x2, y2 = line['x1'], line['y1'], line['x2'], line['y2']
        
        # Check Vertical (Relaxed Tolerance)
        if abs(x1 - x2) < SKEW_TOLERANCE: 
            # It's a Vertical wall (or skewed vertical).
            # Add X to Vertical Grid (Position)
            v_x_coords.extend([x1, x2])
            # Add Y to Horizontal Grid (Endpoints)
            h_y_coords.extend([y1, y2])
            
            if abs(x1 - x2) > 0: skewed_lines_detected += 1
            
        # Check Horizontal (Relaxed Tolerance)
        elif abs(y1 - y2) < SKEW_TOLERANCE: 
            # It's a Horizontal wall.
            # Add Y to Horizontal Grid (Position)
            h_y_coords.extend([y1, y2])
            # Add X to Vertical Grid (Endpoints)
            v_x_coords.extend([x1, x2])
            
            if abs(y1 - y2) > 0: skewed_lines_detected += 1

    print(f"Detected {skewed_lines_detected} skewed lines to be straightened.")

    # --- STEP 2: CLUSTER COORDINATES INTO GRID LINES ---
    def get_snap_rules(coords, threshold):
        if not coords: return []
        unique_coords = sorted(list(set(coords)))
        
        clusters = []
        if not unique_coords: return []
        
        current_cluster = [unique_coords[0]]
        
        for i in range(1, len(unique_coords)):
            val = unique_coords[i]
            # If close to previous, add to cluster
            if val - current_cluster[-1] <= threshold:
                current_cluster.append(val)
            else:
                clusters.append(current_cluster)
                current_cluster = [val]
        clusters.append(current_cluster)
        
        rules = []
        for clust in clusters:
            # The "Master Coordinate" is the average of the cluster
            avg_val = int(round(sum(clust) / len(clust)))
            
            # Create a rule: "If coord is within cluster range, snap to avg"
            # We add a small buffer to min/max to ensure edge cases are caught
            rules.append({
                'min': min(clust) - 2, 
                'max': max(clust) + 2,
                'target': avg_val
            })
        return rules

    x_rules = get_snap_rules(v_x_coords, GLOBAL_ALIGN_THRESHOLD)
    y_rules = get_snap_rules(h_y_coords, GLOBAL_ALIGN_THRESHOLD)

    print(f"Generated Grid: {len(x_rules)} X-Lines, {len(y_rules)} Y-Lines.")

    # --- STEP 3: APPLY GRID SNAPS TO ALL LINES ---
    corrected_count = 0
    
    for line in lines:
        orig_x1, orig_y1 = line['x1'], line['y1']
        orig_x2, orig_y2 = line['x2'], line['y2']
        
        new_x1, new_y1 = orig_x1, orig_y1
        new_x2, new_y2 = orig_x2, orig_y2
        
        # Apply X Snaps
        for r in x_rules:
            if r['min'] <= orig_x1 <= r['max']: new_x1 = r['target']
            if r['min'] <= orig_x2 <= r['max']: new_x2 = r['target']
            
        # Apply Y Snaps
        for r in y_rules:
            if r['min'] <= orig_y1 <= r['max']: new_y1 = r['target']
            if r['min'] <= orig_y2 <= r['max']: new_y2 = r['target']
            
        # Update line if changed
        if (new_x1 != orig_x1) or (new_y1 != orig_y1) or \
           (new_x2 != orig_x2) or (new_y2 != orig_y2):
            line['x1'], line['y1'] = new_x1, new_y1
            line['x2'], line['y2'] = new_x2, new_y2
            corrected_count += 1

    # --- STEP 4: SAVE ---
    with open(output_path, 'w') as f:
        json.dump(lines, f, indent=2)
        
    print(f"Globally Aligned {corrected_count} lines.")
    print(f"Saved to: {output_path}")

# Run
align_walls_globally('second_floor_fused.json', 'second_floor_aligned.json')