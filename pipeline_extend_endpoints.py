import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional

def line_intersection(x1: float, y1: float, x2: float, y2: float, 
                     x3: float, y3: float, x4: float, y4: float) -> Optional[Tuple[float, float]]:
    """
    Find intersection point of two infinite lines.
    Line 1: (x1,y1)-(x2,y2)
    Line 2: (x3,y3)-(x4,y4)
    
    Returns:
        Tuple (x, y) of intersection point, or None if lines are parallel
    """
    x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
    x3, y3, x4, y4 = float(x3), float(y3), float(x4), float(y4)
    
    # Line 1 direction
    dx1 = x2 - x1
    dy1 = y2 - y1
    
    # Line 2 direction
    dx2 = x4 - x3
    dy2 = y4 - y3
    
    # Check if lines are parallel
    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < 1e-10:
        return None  # Lines are parallel
    
    # Find intersection using parametric form
    t = ((x3 - x1) * dy2 - (y3 - y1) * dx2) / denom
    
    ix = x1 + t * dx1
    iy = y1 + t * dy1
    
    return (ix, iy)

def distance_point_to_line_segment(point: Tuple[float, float], 
                                    line_start: Tuple[float, float], 
                                    line_end: Tuple[float, float]) -> float:
    """
    Calculate the minimum distance from a point to a line segment.
    
    Returns:
        Distance to the line segment (shortest distance to the segment itself, not the infinite line)
    """
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        # Line segment is a point
        return distance_point_to_point(point, line_start)
    
    # Parameter t of the projection of point onto the line
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    # Clamp t to [0, 1] to stay within the segment
    t = max(0, min(1, t))
    
    # Find the closest point on the segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    return distance_point_to_point(point, (closest_x, closest_y))

def distance_point_to_point(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

def extend_endpoints(lines_data: List[Dict], max_iterations: int = 3, tolerance: float = 2.0, snap_distance: float = 50.0) -> List[Dict]:
    """
    Extend/shrink line endpoints to snap them to line intersections.
    
    Algorithm:
    1. Find free endpoints (used by only one line)
    2. For each free endpoint, check if it's already ON another line (within tolerance)
    3. If already on a line, skip it (don't modify)
    4. If NOT on any line, extend the line as infinite and find intersections
    5. Snap to the closest intersection
    6. Repeat until convergence
    
    Args:
        lines_data: List of line segments with x1, y1, x2, y2 keys
        max_iterations: Maximum number of passes to attempt
        tolerance: Distance threshold to consider endpoint "on" a line (pixels)
    
    Returns:
        Modified lines_data with endpoints snapped to line intersections
    """
    if not lines_data:
        return lines_data
    
    # Deep copy to avoid modifying input
    lines = [dict(line) for line in lines_data]
        
    total_modifications = 0
    
    for iteration in range(max_iterations):
        
        # ============= STEP 1: Find free endpoints =============
        endpoint_usage = {}
        
        for line_idx, line in enumerate(lines):
            p1 = (line['x1'], line['y1'])
            p2 = (line['x2'], line['y2'])
            
            if p1 not in endpoint_usage:
                endpoint_usage[p1] = []
            if p2 not in endpoint_usage:
                endpoint_usage[p2] = []
            
            endpoint_usage[p1].append((line_idx, 'start'))
            endpoint_usage[p2].append((line_idx, 'end'))
        
        # Identify free endpoints (used by exactly 1 line)
        free_endpoints = {pt: uses for pt, uses in endpoint_usage.items() if len(uses) == 1}
        
        
        # ============= STEP 2: Process each free endpoint =============
        modifications_this_iteration = 0
        
        for endpoint_pt, uses in free_endpoints.items():
            line_idx, position = uses[0]
            current_line = lines[line_idx]
            
            # Get line endpoints
            x1, y1 = current_line['x1'], current_line['y1']
            x2, y2 = current_line['x2'], current_line['y2']
            
            px, py = endpoint_pt
            
            # ============= CHECK: Is this endpoint already on another line? =============
            already_on_line = False
            
            for other_idx, other_line in enumerate(lines):
                if other_idx == line_idx:
                    continue  # Skip own line
                
                ox1, oy1 = other_line['x1'], other_line['y1']
                ox2, oy2 = other_line['x2'], other_line['y2']
                
                # Calculate distance from endpoint to other line (using projection)
                dx = ox2 - ox1
                dy = oy2 - oy1
                
                if dx == 0 and dy == 0:
                    continue
                
                # Project point onto line
                t = ((px - ox1) * dx + (py - oy1) * dy) / (dx * dx + dy * dy)
                proj_x = ox1 + t * dx
                proj_y = oy1 + t * dy
                
                # Distance to line
                dist_to_line = distance_point_to_point((px, py), (proj_x, proj_y))
                
                if dist_to_line <= tolerance:
                    already_on_line = True
                    break
            
            # If already on a line, skip this endpoint
            if already_on_line:
                continue
            
            # ============= CHECK: Does line already intersect another line? =============
            # Check if the current line segment already crosses any other line
            already_intersects = []
            
            for other_idx, other_line in enumerate(lines):
                if other_idx == line_idx:
                    continue
                
                ox1, oy1 = other_line['x1'], other_line['y1']
                ox2, oy2 = other_line['x2'], other_line['y2']
                
                # Find intersection of infinite lines
                intersection = line_intersection(x1, y1, x2, y2, ox1, oy1, ox2, oy2)
                
                if intersection is not None:
                    ix, iy = intersection
                    
                    # Check if endpoint has already passed this intersection
                    # (i.e., is on the far side of the intersection from the other endpoint)
                    # Calculate parameter t for the endpoint on the current line
                    dx_current = x2 - x1
                    dy_current = y2 - y1
                    
                    if abs(dx_current) > abs(dy_current):
                        # Use x as reference
                        if dx_current != 0:
                            t_endpoint = (px - x1) / dx_current
                            t_intersection = (ix - x1) / dx_current
                        else:
                            continue
                    else:
                        # Use y as reference
                        if dy_current != 0:
                            t_endpoint = (py - y1) / dy_current
                            t_intersection = (iy - y1) / dy_current
                        else:
                            continue
                    
                    # If endpoint parameter is beyond intersection parameter (same direction),
                    # the endpoint has already passed the intersection
                    if (t_endpoint > 0 and t_intersection > 0 and t_endpoint >= t_intersection) or \
                       (t_endpoint < 0 and t_intersection < 0 and t_endpoint <= t_intersection):
                        # Endpoint is on the far side - it has already crossed this line
                        dist_to_intersection = distance_point_to_point((px, py), (ix, iy))
                        already_intersects.append((dist_to_intersection, (ix, iy), other_idx))
            
            # If endpoint already intersects/crosses another line, snap it back to that intersection
            if already_intersects:
                already_intersects.sort(key=lambda x: x[0])
                closest_dist, snap_pt, snap_line_idx = already_intersects[0]
                
                new_x = int(round(snap_pt[0]))
                new_y = int(round(snap_pt[1]))
                
                if new_x != px or new_y != py:
                    old_pt = (px, py)
                    new_pt = (new_x, new_y)
                    
                    if position == 'start':
                        current_line['x1'] = new_x
                        current_line['y1'] = new_y
                    else:
                        current_line['x2'] = new_x
                        current_line['y2'] = new_y
                    
                    modifications_this_iteration += 1
                    total_modifications += 1
                                    
                continue  # Skip to next endpoint
            
            # ============= FIND: Intersection points of this line with other lines =============
            intersections = []
            
            for other_idx, other_line in enumerate(lines):
                if other_idx == line_idx:
                    continue  # Skip own line
                
                ox1, oy1 = other_line['x1'], other_line['y1']
                ox2, oy2 = other_line['x2'], other_line['y2']
                
                # Find intersection between current line and other line
                intersection = line_intersection(x1, y1, x2, y2, ox1, oy1, ox2, oy2)
                
                if intersection is not None:
                    ix, iy = intersection
                    
                    # VALIDATION: Check if intersection is actually on the other line segment
                    dist_to_segment = distance_point_to_line_segment((ix, iy), (ox1, oy1), (ox2, oy2))
                    
                    # Only accept if intersection is on the segment (within 2px tolerance)
                    if dist_to_segment > 2.0:
                        continue
                    
                    # Calculate distance from endpoint to this intersection
                    dist = distance_point_to_point((px, py), (ix, iy))
                    
                    # Only consider intersections within snap_distance
                    if dist <= snap_distance:
                        intersections.append((dist, (ix, iy), other_idx))
            
            # ============= STEP 3: Snap to closest intersection =============
            if intersections:
                # Sort by distance and get the closest one
                intersections.sort(key=lambda x: x[0])
                closest_dist, closest_pt, closest_line_idx = intersections[0]
                
                # Snap to the intersection point
                new_x = int(round(closest_pt[0]))
                new_y = int(round(closest_pt[1]))
                
                # Only apply if position actually changed
                if new_x != px or new_y != py:
                    old_pt = (px, py)
                    new_pt = (new_x, new_y)
                    
                    if position == 'start':
                        current_line['x1'] = new_x
                        current_line['y1'] = new_y
                    else:  # end
                        current_line['x2'] = new_x
                        current_line['y2'] = new_y
                    
                    modifications_this_iteration += 1
                    total_modifications += 1
        
        # If no changes, we've converged
        if modifications_this_iteration == 0:
            break
    
    return lines

def visualize_extended_endpoints(lines_data: List[Dict], original_lines_data: List[Dict] = None) -> np.ndarray:
    """
    Visualize the extended endpoints with optional before/after comparison.
    
    Args:
        lines_data: Modified line segments
        original_lines_data: Original line segments before snapping (optional)
    
    Returns:
        Visualization image as numpy array
    """
    if not lines_data:
        return None
    
    # Calculate canvas size
    all_x = []
    all_y = []
    
    for line in lines_data:
        all_x.extend([line['x1'], line['x2']])
        all_y.extend([line['y1'], line['y2']])
    
    if not all_x or not all_y:
        return None
    
    max_x = max(all_x)
    max_y = max(all_y)
    h, w = max_y + 150, max_x + 150
    
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background
    
    # Draw original lines in light gray if provided
    if original_lines_data:
        for line in original_lines_data:
            pt1 = (line['x1'], line['y1'])
            pt2 = (line['x2'], line['y2'])
            cv2.line(img, pt1, pt2, (200, 200, 200), 1)  # Light gray
    
    # Draw snapped lines in blue
    for line in lines_data:
        pt1 = (line['x1'], line['y1'])
        pt2 = (line['x2'], line['y2'])
        cv2.line(img, pt1, pt2, (0, 150, 200), 2)  # Blue
    
    # Draw endpoints as red circles
    all_endpoints = set()
    for line in lines_data:
        all_endpoints.add((line['x1'], line['y1']))
        all_endpoints.add((line['x2'], line['y2']))
    
    for pt in all_endpoints:
        cv2.circle(img, pt, 3, (0, 0, 255), -1)  # Red
    
    # Add legend
    font = cv2.FONT_HERSHEY_SIMPLEX
    if original_lines_data:
        cv2.putText(img, "Original (Gray)", (20, h - 40), font, 0.5, (200, 200, 200), 1)
        cv2.putText(img, "Snapped (Blue)", (20, h - 20), font, 0.5, (0, 150, 200), 1)
    else:
        cv2.putText(img, "Snapped Endpoints (Blue)", (20, h - 20), font, 0.5, (0, 150, 200), 1)
    
    return img
