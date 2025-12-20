import json
import math

# --- TUNING ---
# Snapping threshold (pixels). Points within this range will fuse to a single grid line.
GLOBAL_ALIGN_THRESHOLD = 20 

def align_walls_globally(input_path, output_path):
    try:
        with open(input_path, 'r') as f:
            lines = json.load(f)
    except FileNotFoundError:
        print("Error: Input file not found.")
        return

    # 1. Collect Coordinates from ALL Orthogonal Lines
    # We now collect X and Y from BOTH Vertical and Horizontal lines.
    # This ensures wall ENDPOINTS align with other wall POSITIONS.
    v_x_coords = []
    h_y_coords = []

    for line in lines:
        x1, y1, x2, y2 = line['x1'], line['y1'], line['x2'], line['y2']
        
        # Check if Vertical (allow small skew)
        if abs(x1 - x2) < 5: 
            # Add X to Vertical Grid (Wall Position)
            v_x_coords.extend([x1, x2])
            # Add Y to Horizontal Grid (Wall Endpoints) - THIS IS THE FIX
            h_y_coords.extend([y1, y2])
            
        # Check if Horizontal
        elif abs(y1 - y2) < 5: 
            # Add Y to Horizontal Grid (Wall Position)
            h_y_coords.extend([y1, y2])
            # Add X to Vertical Grid (Wall Endpoints) - THIS IS THE FIX
            v_x_coords.extend([x1, x2])

    # 2. Logic to Cluster Coordinates and Create Snap Rules
    def get_snap_rules(coords, threshold):
        if not coords: return []
        unique_coords = sorted(list(set(coords)))
        
        clusters = []
        if not unique_coords: return []
        
        current_cluster = [unique_coords[0]]
        
        for i in range(1, len(unique_coords)):
            val = unique_coords[i]
            if val - current_cluster[-1] <= threshold:
                current_cluster.append(val)
            else:
                clusters.append(current_cluster)
                current_cluster = [val]
        clusters.append(current_cluster)
        
        rules = []
        for clust in clusters:
            # Calculate average (Master Coordinate)
            avg_val = int(round(sum(clust) / len(clust)))
            
            # Create a rule: "If coord is within range [min, max], snap to avg"
            rules.append({
                'min': min(clust) - 2, # Buffer
                'max': max(clust) + 2,
                'target': avg_val
            })
        return rules

    # Generate the Grid Rules from the expanded pools
    x_rules = get_snap_rules(v_x_coords, GLOBAL_ALIGN_THRESHOLD)
    y_rules = get_snap_rules(h_y_coords, GLOBAL_ALIGN_THRESHOLD)

    print(f"Generated {len(x_rules)} X-Grid Lines (Verticals & Ends).")
    print(f"Generated {len(y_rules)} Y-Grid Lines (Horizontals & Ends).")

    # 3. Apply Rules to ALL lines
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

    # 4. Save
    with open(output_path, 'w') as f:
        json.dump(lines, f, indent=2)
        
    print(f"Globally Aligned {corrected_count} lines.")
    print(f"Saved to: {output_path}")

# Run
align_walls_globally('floorplan_master_fused.json', 'floorplan_aligned.json')