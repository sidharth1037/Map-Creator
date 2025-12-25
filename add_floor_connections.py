import json

def add_floor_connections(input_file, config_file, output_file):
    """
    Add floor connection information to stair polygons using a config file.
    Also removes unnecessary 'original_*' fields from stair segments.
    
    Args:
        input_file: Path to JSON with polygon IDs
        config_file: Path to JSON config file with floor connections
        output_file: Path to save updated JSON with floor connections
    """
    
    with open(input_file, 'r') as f:
        segments = json.load(f)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    print(f"Loaded {len(segments)} segments")
    
    # Find all stair polygon IDs
    polygon_ids = set()
    for seg in segments:
        if 'stair_polygon_id' in seg:
            polygon_ids.add(seg['stair_polygon_id'])
    
    polygon_ids = sorted(list(polygon_ids))
    print(f"Found {len(polygon_ids)} stair polygons: {polygon_ids}")
    
    # Get floor connections from config
    floor_connections = {}
    for poly_id_str, connection in config.get('floor_connections', {}).items():
        poly_id = int(poly_id_str)
        floor_connections[poly_id] = connection
    
    print(f"Loaded floor connections for {len(floor_connections)} polygons from config\n")
    
    # Update segments: add floor connections and remove original coordinates
    updated_segments = []
    
    for seg in segments:
        seg_copy = seg.copy()
        
        # Remove original coordinate fields for stairs
        if seg_copy.get('type') == 'stair':
            seg_copy.pop('original_x1', None)
            seg_copy.pop('original_y1', None)
            seg_copy.pop('original_x2', None)
            seg_copy.pop('original_y2', None)
            
            # Add floor connection if this is a stair polygon segment
            if 'stair_polygon_id' in seg_copy:
                poly_id = seg_copy['stair_polygon_id']
                if poly_id in floor_connections:
                    seg_copy['floor_connection'] = floor_connections[poly_id]
        
        updated_segments.append(seg_copy)
    
    # Save updated JSON
    with open(output_file, 'w') as f:
        json.dump(updated_segments, f, indent=2)
    
    print("\n" + "="*60)
    print(f"Saved updated JSON to {output_file}")
    print(f"- Removed original_* fields from stairs")
    print(f"- Added floor_connection data to {len(floor_connections)} polygons")
    print("="*60)

if __name__ == "__main__":
    input_file = "first_floor_combined_with_polygon_ids.json"
    config_file = "floor_connections_config.json"
    output_file = "first_floor_combined_with_floors.json"
    
    add_floor_connections(input_file, config_file, output_file)
    print("\nDone!")
