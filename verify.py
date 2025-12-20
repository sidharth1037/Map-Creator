import cv2
import numpy as np
import json
import math

def calculate_angle(p1, center, p2):
    """Calculates the angle between vector center->p1 and center->p2"""
    # Vector 1
    v1_x = p1[0] - center[0]
    v1_y = p1[1] - center[1]
    # Vector 2
    v2_x = p2[0] - center[0]
    v2_y = p2[1] - center[1]
    
    # Angles in degrees (0 to 360)
    ang1 = math.degrees(math.atan2(v1_y, v1_x))
    ang2 = math.degrees(math.atan2(v2_y, v2_x))
    
    if ang1 < 0: ang1 += 360
    if ang2 < 0: ang2 += 360
    
    diff = abs(ang1 - ang2)
    if diff > 180:
        diff = 360 - diff
        
    return int(round(diff))

def verify_json_detailed(json_path, output_img_path):
    # 1. Load Data
    try:
        with open(json_path, 'r') as f:
            lines = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return

    if not lines: return

    # 2. Setup Canvas
    all_x = []
    all_y = []
    adjacency = {} # Map coordinate -> list of connected neighbors

    for l in lines:
        p1 = (l['x1'], l['y1'])
        p2 = (l['x2'], l['y2'])
        all_x.extend([p1[0], p2[0]])
        all_y.extend([p1[1], p2[1]])
        
        # Build adjacency graph for angle calculation
        if p1 not in adjacency: adjacency[p1] = []
        if p2 not in adjacency: adjacency[p2] = []
        adjacency[p1].append(p2)
        adjacency[p2].append(p1)

    max_x, max_y = max(all_x), max(all_y)
    h, w = max_y + 150, max_x + 150
    img = np.ones((h, w, 3), dtype=np.uint8) * 255 # White background

    # 3. Draw Lines with Color Coding
    print(f"Drawing {len(lines)} lines...")
    
    for l in lines:
        pt1 = (l['x1'], l['y1'])
        pt2 = (l['x2'], l['y2'])
        
        # Determine orientation for color
        dx = abs(pt1[0] - pt2[0])
        dy = abs(pt1[1] - pt2[1])
        
        if dx < 5: 
            color = (255, 0, 0)   # Blue (Vertical) - BGR
        elif dy < 5: 
            color = (0, 180, 0)   # Dark Green (Horizontal)
        else:
            color = (255, 0, 255) # Magenta (Diagonal)
            
        cv2.line(img, pt1, pt2, color, 2)

    # 4. Draw Vertices, Labels, and Angles
    unique_points = sorted(list(adjacency.keys()), key=lambda p: (p[1], p[0]))
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    print(f"Found {len(unique_points)} unique vertices.")

    for i, pt in enumerate(unique_points):
        x, y = pt
        neighbors = adjacency[pt]
        
        # Draw Vertex (Red Dot)
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        
        # Draw ID Label (Blue, Top-Right offset)
        cv2.putText(img, str(i), (x + 6, y - 6), font, 0.4, (255, 0, 0), 1, cv2.LINE_AA)
        
        # Calculate Angles if it's a junction (2+ lines connected)
        if len(neighbors) >= 2:
            # If 2 lines, just one angle. If 3 lines (T-junction), multiple angles.
            # For verification, checking adjacent pairs is enough.
            
            # Simple case: 2 lines (L-corner or V-shape)
            if len(neighbors) == 2:
                angle = calculate_angle(neighbors[0], pt, neighbors[1])
                angle_text = f"{angle}"
                # Draw Angle (Black, Bottom-Right offset)
                cv2.putText(img, angle_text, (x + 10, y + 15), font, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
            
            # Complex case: 3+ lines (T-junctions)
            else:
                # Just mark as "Jct" (Junction) or calculate min angle
                cv2.putText(img, "Jct", (x + 10, y + 15), font, 0.35, (50, 50, 50), 1, cv2.LINE_AA)

    # 5. Legend
    cv2.putText(img, "Vertical (Blue)", (20, h - 80), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "Horizontal (Green)", (20, h - 60), font, 0.5, (0, 180, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "Diagonal (Magenta)", (20, h - 40), font, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
    cv2.putText(img, "Vertex IDs in Blue, Angles in Black", (20, h - 20), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # 6. Save
    cv2.imwrite(output_img_path, img)
    print(f"Verification image saved to: {output_img_path}")

# Run
verify_json_detailed('floorplan_master_fused.json', 'verification_detailed.jpg')