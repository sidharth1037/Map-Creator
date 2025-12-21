import cv2
import numpy as np
import json

def verify_json_coordinates(json_path, output_img_path):
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
    
    for l in lines:
        all_x.extend([l['x1'], l['x2']])
        all_y.extend([l['y1'], l['y2']])

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

    # 4. Draw Vertices and Coordinate Labels
    unique_points = set()
    for l in lines:
        unique_points.add((l['x1'], l['y1']))
        unique_points.add((l['x2'], l['y2']))
        
    sorted_points = sorted(list(unique_points), key=lambda p: (p[1], p[0]))
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    print(f"Found {len(sorted_points)} unique vertices.")

    for pt in sorted_points:
        x, y = pt
        
        # Draw Vertex (Red Dot)
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        
        # Draw Coordinate Label (Black, slightly offset)
        coord_text = f"({x},{y})"
        cv2.putText(img, coord_text, (x + 8, y - 8), font, 0.35, (0, 0, 0), 1, cv2.LINE_AA)

    # 5. Legend
    cv2.putText(img, "Vertical (Blue)", (20, h - 80), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "Horizontal (Green)", (20, h - 60), font, 0.5, (0, 180, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "Diagonal (Magenta)", (20, h - 40), font, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
    cv2.putText(img, "Coordinates (x,y) in Black", (20, h - 20), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # 6. Save
    cv2.imwrite(output_img_path, img)
    print(f"Verification image saved to: {output_img_path}")

# Run
verify_json_coordinates('second_floor_aligned.json', 'verification_coords.jpg')