import json
import cv2
import numpy as np
import os
from pathlib import Path

# ===== CONFIGURATION =====
JSON_FOLDER = "C:\\Users\\sidha\\Desktop\\final_plans"  # Folder containing the JSON files
# Format: {filename: (x_offset, y_offset, scale)}
JSON_FILES = {
    "floor_1_walls.json": (0, 0, 1.0),          # x_offset, y_offset, scale
    "floor_1.5_walls.json": (0, 0, 1.0),        # Translate and scale coordinates
    "floor_2_walls.json": (-162, -90, 0.93),    # scale=1.0 means no scaling
    # Add more filenames with their offsets and scale here
}
OUTPUT_IMAGE_PATH = "C:\\Users\\sidha\\Desktop\\maps\\images\\visualization_layers.png"
# =========================

def load_json(filepath):
    """Load JSON file safely."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return None

def get_json_files(folder_path, files_dict):
    """Get JSON files from a folder based on a dictionary of filenames, offsets, and scale."""
    json_files = []
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return json_files
    
    for filename, values in files_dict.items():
        # Handle both old format (offset_x, offset_y) and new format (offset_x, offset_y, scale)
        if len(values) == 2:
            offset_x, offset_y = values
            scale = 1.0
        else:
            offset_x, offset_y, scale = values
            
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            json_files.append((filepath, offset_x, offset_y, scale))
        else:
            print(f"Warning: File not found '{filepath}'")
    
    return json_files

def visualize_multiple_layers(folder_path, files_dict, output_path):
    """
    Visualize multiple JSON files overlaid on top of each other.
    
    Each JSON file is drawn with a different color.
    Coordinates can be translated by specified x and y offsets and scaled.
    Expects JSON files to contain segments with x1, y1, x2, y2 coordinates.
    
    Args:
        folder_path: Path to folder containing JSON files
        files_dict: Dictionary of {filename: (x_offset, y_offset, scale)}
        output_path: Path to save the output visualization
    """
    
    # Get specified JSON files
    json_files = get_json_files(folder_path, files_dict)
    
    if not json_files:
        print(f"No JSON files found in '{folder_path}'")
        return
    
    print(f"Found {len(json_files)} JSON files:")
    for f, offset_x, offset_y, scale in json_files:
        print(f"  - {os.path.basename(f)} (offset: x={offset_x}, y={offset_y}, scale={scale})")
    
    # Load all data and find bounds
    all_data = []
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    for json_file, offset_x, offset_y, scale in json_files:
        data = load_json(json_file)
        if data:
            all_data.append({
                'name': os.path.splitext(os.path.basename(json_file))[0],
                'data': data,
                'offset_x': offset_x,
                'offset_y': offset_y,
                'scale': scale
            })
            
            # Find bounds (considering offsets and scale)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if 'x1' in item and 'y1' in item:
                            x1 = item['x1'] * scale + offset_x
                            x2 = item.get('x2', item['x1']) * scale + offset_x
                            y1 = item['y1'] * scale + offset_y
                            y2 = item.get('y2', item['y1']) * scale + offset_y
                            min_x = min(min_x, x1, x2)
                            max_x = max(max_x, x1, x2)
                            min_y = min(min_y, y1, y2)
                            max_y = max(max_y, y1, y2)
                        elif 'x' in item and 'y' in item:
                            x = item['x'] * scale + offset_x
                            y = item['y'] * scale + offset_y
                            min_x = min(min_x, x)
                            max_x = max(max_x, x)
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
    
    if not all_data:
        print("No valid data found in JSON files.")
        return
    
    # Create canvas
    padding = 150
    width = int(max_x - min_x + padding * 2)
    height = int(max_y - min_y + padding * 2)
    
    print(f"\nCanvas size: {width} x {height}")
    print(f"Bounds: X=[{min_x}, {max_x}], Y=[{min_y}, {max_y}]")
    
    img = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
    
    # Color palette for different layers
    colors = [
        (255, 0, 0),      # Blue
        (0, 255, 0),      # Green
        (0, 0, 255),      # Red
        (255, 255, 0),    # Cyan
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Yellow
        (128, 0, 255),    # Purple
        (255, 128, 0),    # Orange
        (128, 255, 0),    # Lime
        (0, 128, 255),    # Deep Orange
    ]
    
    # Draw each layer
    legend_items = []
    
    for idx, layer in enumerate(all_data):
        color = colors[idx % len(colors)]
        data = layer['data']
        layer_name = layer['name']
        offset_x = layer['offset_x']
        offset_y = layer['offset_y']
        scale = layer['scale']
        
        segment_count = 0
        point_count = 0
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # Handle line segments (x1, y1, x2, y2)
                    if 'x1' in item and 'y1' in item and 'x2' in item and 'y2' in item:
                        x1 = int(item['x1'] * scale + offset_x - min_x + padding)
                        y1 = int(item['y1'] * scale + offset_y - min_y + padding)
                        x2 = int(item['x2'] * scale + offset_x - min_x + padding)
                        y2 = int(item['y2'] * scale + offset_y - min_y + padding)
                        
                        cv2.line(img, (x1, y1), (x2, y2), color, 2)
                        segment_count += 1
                    
                    # Handle points (x, y)
                    if 'x' in item and 'y' in item and 'x1' not in item:
                        x = int(item['x'] * scale + offset_x - min_x + padding)
                        y = int(item['y'] * scale + offset_y - min_y + padding)
                        
                        cv2.circle(img, (x, y), 4, color, -1)
                        point_count += 1
        
        print(f"  {layer_name}: {segment_count} segments, {point_count} points")
        legend_items.append((layer_name, color))
    
    # Add legend
    legend_x = 20
    legend_y = 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    cv2.putText(img, "Layers:", (legend_x, legend_y), font, 1.0, (0, 0, 0), 2)
    legend_y += 40
    
    for layer_name, color in legend_items:
        cv2.line(img, (legend_x, legend_y), (legend_x + 40, legend_y), color, 3)
        cv2.putText(img, layer_name, (legend_x + 50, legend_y + 5), font, 0.7, (0, 0, 0), 1)
        legend_y += 30
    
    # Save image
    cv2.imwrite(output_path, img)
    print(f"\nVisualization saved to: {output_path}")

if __name__ == "__main__":
    visualize_multiple_layers(JSON_FOLDER, JSON_FILES, OUTPUT_IMAGE_PATH)
