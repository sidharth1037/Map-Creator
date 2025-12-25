import json
import cv2
import numpy as np

def group_stair_polygons(input_file, output_file, visualize=True, vis_output="stair_polygons_visualization.jpg"):
    """
    Group stair segments that form polygons together and assign polygon IDs.
    
    Args:
        input_file: Path to combined JSON with walls and stairs
        output_file: Path to output JSON with stair polygon IDs
    """
    
    with open(input_file, 'r') as f:
        segments = json.load(f)
    
    print(f"Loaded {len(segments)} segments")
    
    # Extract stair segments
    stair_segments = {}
    stair_indices = []
    
    for idx, seg in enumerate(segments):
        if seg.get('type') == 'stair':
            stair_segments[idx] = seg
            stair_indices.append(idx)
    
    print(f"Found {len(stair_segments)} stair segments")
    
    # Build adjacency graph
    # Map (x,y) to list of segment indices that have this as start or end point
    vertex_to_segments = {}
    
    for idx in stair_indices:
        seg = segments[idx]
        start = (seg['x1'], seg['y1'])
        end = (seg['x2'], seg['y2'])
        
        if start not in vertex_to_segments:
            vertex_to_segments[start] = []
        if end not in vertex_to_segments:
            vertex_to_segments[end] = []
        
        vertex_to_segments[start].append((idx, 'start'))
        vertex_to_segments[end].append((idx, 'end'))
    
    # Group connected stair segments into polygons
    polygon_id = 0
    assigned = set()
    polygon_assignments = {}  # Maps segment index to polygon ID
    
    for start_idx in stair_indices:
        if start_idx in assigned:
            continue
        
        # BFS to find all connected segments
        polygon_segments = []
        queue = [start_idx]
        polygon_id += 1
        
        while queue:
            idx = queue.pop(0)
            
            if idx in assigned:
                continue
            
            assigned.add(idx)
            polygon_segments.append(idx)
            polygon_assignments[idx] = polygon_id
            
            seg = segments[idx]
            start = (seg['x1'], seg['y1'])
            end = (seg['x2'], seg['y2'])
            
            # Find adjacent segments
            for adjacent_idx, _ in vertex_to_segments[start]:
                if adjacent_idx not in assigned and adjacent_idx in stair_segments:
                    queue.append(adjacent_idx)
            
            for adjacent_idx, _ in vertex_to_segments[end]:
                if adjacent_idx not in assigned and adjacent_idx in stair_segments:
                    queue.append(adjacent_idx)
        
        print(f"  Polygon {polygon_id}: {len(polygon_segments)} segments")
    
    # Add polygon IDs to segments
    output_segments = []
    
    for idx, seg in enumerate(segments):
        seg_copy = seg.copy()
        
        if idx in polygon_assignments:
            seg_copy['stair_polygon_id'] = polygon_assignments[idx]
        
        output_segments.append(seg_copy)
    
    # Save output
    with open(output_file, 'w') as f:
        json.dump(output_segments, f, indent=2)
    
    print(f"\nGrouped {len(stair_segments)} stair segments into {polygon_id} polygons")
    print(f"Saved to {output_file}")
    
    # Generate visualization if requested
    if visualize:
        visualize_stair_polygons(segments, polygon_assignments, vis_output)

def visualize_stair_polygons(segments, polygon_assignments, output_img_path):
    """
    Create an image visualization of the floor plan with stair polygon IDs.
    
    Args:
        segments: List of all segments with type information
        polygon_assignments: Dict mapping segment index to polygon ID
        output_img_path: Path to save the visualization image
    """
    
    # Setup canvas
    all_x = []
    all_y = []
    
    for seg in segments:
        all_x.extend([seg['x1'], seg['x2']])
        all_y.extend([seg['y1'], seg['y2']])
    
    max_x, max_y = max(all_x), max(all_y)
    h, w = max_y + 150, max_x + 150
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background
    
    print(f"\nGenerating visualization: {w}x{h} pixels")
    
    # Draw all segments
    for idx, seg in enumerate(segments):
        pt1 = (seg['x1'], seg['y1'])
        pt2 = (seg['x2'], seg['y2'])
        
        if seg.get('type') == 'wall':
            color = (0, 150, 255)  # Orange for walls
        else:  # stair
            color = (0, 255, 0)    # Green for stairs
        
        cv2.line(img, pt1, pt2, color, 2)
    
    # Draw vertices
    all_points = set()
    for seg in segments:
        all_points.add((seg['x1'], seg['y1']))
        all_points.add((seg['x2'], seg['y2']))
    
    for pt in all_points:
        cv2.circle(img, pt, 4, (0, 0, 255), -1)  # Red dots
    
    # Draw polygon IDs for stairs
    font = cv2.FONT_HERSHEY_SIMPLEX
    polygon_centroids = {}
    
    for idx, seg in enumerate(segments):
        if idx in polygon_assignments:
            poly_id = polygon_assignments[idx]
            
            if poly_id not in polygon_centroids:
                polygon_centroids[poly_id] = {'x_sum': 0, 'y_sum': 0, 'count': 0}
            
            polygon_centroids[poly_id]['x_sum'] += seg['x1'] + seg['x2']
            polygon_centroids[poly_id]['y_sum'] += seg['y1'] + seg['y2']
            polygon_centroids[poly_id]['count'] += 2
    
    # Draw polygon ID labels at centroids
    for poly_id, centroid_data in polygon_centroids.items():
        cx = int(centroid_data['x_sum'] / centroid_data['count'])
        cy = int(centroid_data['y_sum'] / centroid_data['count'])
        
        label = f"ID {poly_id}"
        cv2.putText(img, label, (cx - 20, cy), font, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
    
    # Legend
    legend_y = h - 80
    cv2.putText(img, "Legend:", (20, legend_y), font, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    
    cv2.line(img, (20, legend_y + 25), (80, legend_y + 25), (0, 150, 255), 3)
    cv2.putText(img, "Walls (Orange)", (90, legend_y + 30), font, 0.5, (0, 150, 255), 1, cv2.LINE_AA)
    
    cv2.line(img, (20, legend_y + 50), (80, legend_y + 50), (0, 255, 0), 3)
    cv2.putText(img, "Stairs (Green)", (90, legend_y + 55), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    
    cv2.circle(img, (50, legend_y + 75), 4, (0, 0, 255), -1)
    cv2.putText(img, "Vertices (Red)", (90, legend_y + 80), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    
    # Save image
    cv2.imwrite(output_img_path, img)
    print(f"Visualization saved to: {output_img_path}")

if __name__ == "__main__":
    group_stair_polygons("first_floor_combined.json", "first_floor_combined_with_polygon_ids.json", visualize=True)
    print("\nDone!")
