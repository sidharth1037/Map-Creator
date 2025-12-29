import json
import math

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_point_from_id(points_mapping, point_id):
    """Get coordinates for a point ID from the mapping."""
    point_str = str(point_id)
    if point_str in points_mapping['points']:
        p = points_mapping['points'][point_str]
        return (p['x'], p['y'])
    else:
        raise ValueError(f"Point ID {point_id} not found in mapping")

def calculate_quadrilateral_centroid(p1, p2, p3, p4):
    """
    Calculate the centroid (center) of a quadrilateral from 4 points.
    Uses the average of the 4 points as a simple centroid.
    """
    centroid_x = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
    centroid_y = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
    return (centroid_x, centroid_y)

def label_rooms(points_mapping_file, output_file=None):
    """
    Create rooms from 4-point quadrilaterals and store their centroids.
    """
    
    # Define rooms - each room is identified by 4 point IDs forming a quadrilateral
    rooms = {
        # Format 1 (without name): room_id: [point_id_1, point_id_2, point_id_3, point_id_4]
        # Format 2 (with name): room_id: {"point_ids": [...], "name": "Room Name"}
        1: {"point_ids": [1, 15, 104, 105], "name": "114: Gents Toilet"},
        2: {"point_ids": [16, 17, 109, 23], "name": "Lift"},
        3: {"point_ids": [104, 101, 102, 105], "name": None},
        4: {"point_ids": [31, 47, 29, 103], "name": "113: Gents Waiting Room"},
        5: {"point_ids": [101, 102, 95, 96], "name": "115: Software Computing Lab"},
        6: {"point_ids": [29, 103, 27, 100], "name": "112: Staff Room"},
        7: {"point_ids": [34, 26, 98, 46], "name": "111: HOD Office"},
        8: {"point_ids": [48, 49, 50, 53], "name": "110: HOD Office"},
        9: {"point_ids": [42, 43, 54, 55], "name": "105: Lecture Hall"},
        10: {"point_ids": [56, 59, 60, 61], "name": "109: Staff Room"},
        11: {"point_ids": [54, 55, 63, 62], "name": "106: Lecture Hall"},
        12: {"point_ids": [61, 60, 87, 67], "name": "108: Ladies Waiting Room"},
        13: {"point_ids": [62, 63, 66, 75], "name": "107: Ladies Toilet"},
    }
    
    if output_file is None:
        output_file = 'json/first_floor_rooms.json'
    
    # Load points mapping
    points_mapping = load_json(points_mapping_file)
    
    # Create rooms data structure
    rooms_data = {
        'total_rooms': len(rooms),
        'rooms': []
    }
    
    # Process each room
    for room_id, room_data in rooms.items():
        # Handle both formats: list of points or dict with point_ids and name
        if isinstance(room_data, list):
            point_ids = room_data
            room_name = None
        elif isinstance(room_data, dict):
            point_ids = room_data.get('point_ids', [])
            room_name = room_data.get('name', None)
        else:
            print(f"Warning: Room {room_id} has invalid format, skipping")
            continue
        
        if len(point_ids) != 4:
            print(f"Warning: Room {room_id} does not have exactly 4 points, skipping")
            continue
        
        try:
            # Get coordinates for each point
            p1 = get_point_from_id(points_mapping, point_ids[0])
            p2 = get_point_from_id(points_mapping, point_ids[1])
            p3 = get_point_from_id(points_mapping, point_ids[2])
            p4 = get_point_from_id(points_mapping, point_ids[3])
            
            # Calculate centroid
            centroid = calculate_quadrilateral_centroid(p1, p2, p3, p4)
            
            # Create room entry
            room_entry = {
                'id': room_id,
                'x': centroid[0],
                'y': centroid[1],
                'name': room_name,
                'point_ids': point_ids
            }
            rooms_data['rooms'].append(room_entry)
            
            print(f"Room {room_id}: Points {point_ids} -> Centroid: ({centroid[0]:.2f}, {centroid[1]:.2f}) - Name: {room_name}")
        
        except ValueError as e:
            print(f"Error processing room {room_id}: {e}")
    
    # Save rooms data
    save_json(rooms_data, output_file)
    print(f"\nSaved {len(rooms_data['rooms'])} rooms to {output_file}")

if __name__ == '__main__':
    label_rooms('json/first_floor_points_mapping.json')
