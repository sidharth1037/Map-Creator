"""Boundary creation utilities for floor plan processing."""

import json


def save_boundary_json(boundary_points, floor_number, output_file=None):
    """
    Save boundary points to JSON file.
    
    Args:
        boundary_points: List of dicts with structure {id, x, y}
        floor_number: Floor number (int or float)
        output_file: Output file path (if None, auto-generates name)
    
    Returns:
        Tuple: (success: bool, filepath: str)
    """
    try:
        # Smart floor number formatting
        if isinstance(floor_number, str):
            try:
                floor_num = float(floor_number)
            except ValueError:
                floor_num = floor_number
        else:
            floor_num = float(floor_number)
        
        # Format floor string
        if isinstance(floor_num, float) and floor_num == int(floor_num):
            floor_str = str(int(floor_num))
        else:
            floor_str = str(floor_num)
        
        if output_file is None:
            output_file = f"outputs/floor_{floor_str}_boundary.json"
        
        boundary_data = {
            "floor": floor_str,
            "total_points": len(boundary_points),
            "boundary_points": boundary_points
        }
        
        with open(output_file, 'w') as f:
            json.dump(boundary_data, f, indent=2)
        
        return True, output_file
        
    except Exception as e:
        return False, str(e)
