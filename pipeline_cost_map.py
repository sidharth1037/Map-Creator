"""Cost map generation utilities for floor plan processing.

This module generates movement cost heuristics for pathfinding algorithms.
The costs are pre-computed and saved as PNG + JSON metadata for efficient
mobile/API processing, eliminating runtime calculation overhead.
"""

import cv2
import numpy as np
import json


def generate_cost_map(image_path):
    """
    Generate a cost map from a floor plan image using distance transform.
    
    Args:
        image_path: Path to the floor plan image
    
    Returns:
        Tuple: (cost_map, original_image) or (None, None) on failure
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return None, None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image (walls = white, empty space = black)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Calculate distance transform
        # For each pixel, this gives the distance to the nearest black pixel (wall)
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        
        # Calculate cost: 200 / (distance + 0.1)
        # Higher cost near walls, lower cost far from walls
        cost_map = 200.0 / (dist_transform + 0.1)
        
        # Normalize to 0-255 for visualization
        cost_normalized = cv2.normalize(cost_map, None, 0, 255, cv2.NORM_MINMAX)
        cost_normalized = cost_normalized.astype(np.uint8)
        
        return cost_map, cost_normalized
        
    except Exception as e:
        return None, None


def calculate_movement_cost_heuristic(image_path, grid_size=20.0, blocked_threshold=0.5):
    """
    Calculate movement cost heuristic for each pixel using Kotlin-compatible formula.
    
    Formula matches NavigationRepository.getMovementCost():
    - If distance <= blocked_threshold: cost = 1000.0 (blocked)
    - Else: cost = 200.0 / (0.1 + distance)
    
    Pre-computes all costs for efficient mobile/API processing.
    
    Args:
        image_path: Path to the floor plan image
        grid_size: Grid cell size in pixels (default 20.0)
        blocked_threshold: Distance threshold for blocking (default 0.5)
    
    Returns:
        Tuple: (cost_map_float32, metadata_dict) or (None, None) on failure
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return None, None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image (walls = white, empty space = black)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Calculate distance transform
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        
        # Apply movement cost formula (Kotlin-compatible)
        h, w = dist_transform.shape
        cost_map = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                distance = dist_transform[y, x]
                if distance <= blocked_threshold:
                    cost_map[y, x] = 1000.0  # Blocked
                else:
                    cost_map[y, x] = 200.0 / (0.1 + distance)  # Open space
        
        # Calculate metadata for scaling
        cost_min = np.min(cost_map)
        cost_max = np.max(cost_map)
        
        metadata = {
            "floor": None,  # Will be set during save
            "grid_size": float(grid_size),
            "image_width": int(w),
            "image_height": int(h),
            "cost_min": float(cost_min),
            "cost_max": float(cost_max),
            "blocked_threshold": float(blocked_threshold),
            "format": "PNG with linear scaling to 0-255"
        }
        
        return cost_map, metadata
        
    except Exception as e:
        return None, None


def create_heatmap(cost_normalized):
    """
    Convert normalized cost map to a grayscale heatmap for visualization.
    
    Args:
        cost_normalized: Normalized cost map (0-255)
                        where 255 = highest cost (closest to walls)
    
    Returns:
        Grayscale heatmap where:
        - Dark grey/black = high cost (closest to walls)
        - White = low cost (furthest from walls)
    """
    try:
        # Invert the cost map so high cost shows as dark, low cost as white
        grayscale = 255 - cost_normalized
        
        # Convert to BGR format (3 channels) for consistency with other visualizations
        heatmap = cv2.cvtColor(grayscale, cv2.COLOR_GRAY2BGR)
        
        return heatmap
    except Exception as e:
        return None


def save_cost_heuristic(cost_map_float32, metadata, floor_number, output_dir="outputs"):
    """
    Save the movement cost heuristic as PNG + JSON with LUT for mobile/API processing.
    
    Saves two files:
    1. PNG: Each pixel's grayscale intensity (0-255) indexes into the LUT
       - Compact due to PNG compression
       - Fast to load on mobile devices
       - Easily queried during pathfinding
    
    2. JSON: Metadata including Look-Up Table (LUT)
       - lut: 256-entry array mapping pixel values (0-255) directly to movement costs
       - grid_size, image dimensions
       - blocked_threshold
    
    Mobile pathfinding is O(1) per pixel query: just LUT[pixel_value]
    No divisions, no multiplications - direct array indexing.
    
    Args:
        cost_map_float32: Float32 cost map from calculate_movement_cost_heuristic()
        metadata: Metadata dict from calculate_movement_cost_heuristic()
        floor_number: Floor number for filename
        output_dir: Output directory
    
    Returns:
        Tuple: (success: bool, png_path: str, json_path: str)
    """
    try:
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Format floor string
        if isinstance(floor_number, str):
            try:
                floor_num = float(floor_number)
            except ValueError:
                floor_num = floor_number
        else:
            floor_num = float(floor_number)
        
        if isinstance(floor_num, float) and floor_num == int(floor_num):
            floor_str = str(int(floor_num))
        else:
            floor_str = str(floor_num)
        
        # Scale cost values to 0-255 for PNG storage
        cost_min = np.min(cost_map_float32)
        cost_max = np.max(cost_map_float32)
        
        if cost_max > cost_min:
            cost_normalized = ((cost_map_float32 - cost_min) / (cost_max - cost_min) * 255).astype(np.uint8)
        else:
            cost_normalized = np.zeros_like(cost_map_float32, dtype=np.uint8)
        
        # Save PNG
        png_path = f"{output_dir}/floor_{floor_str}_cost_heuristic.png"
        cv2.imwrite(png_path, cost_normalized)
        
        # Build Look-Up Table (LUT): maps pixel value (0-255) to actual movement cost
        # This eliminates all computation on mobile - just array indexing
        lut = []
        for pixel_val in range(256):
            # Inverse of normalization: pixel_val (0-255) -> cost value
            cost_value = (pixel_val / 255.0) * (cost_max - cost_min) + cost_min
            lut.append(float(cost_value))
        
        # Update metadata
        metadata["floor"] = floor_str
        metadata["cost_min"] = float(cost_min)
        metadata["cost_max"] = float(cost_max)
        metadata["lut"] = lut  # 256-entry lookup table
        metadata["lut_note"] = "Mobile: cost = lut[pixel_value] - O(1) direct lookup, no computation"
        
        # Save JSON metadata with LUT
        json_path = f"{output_dir}/floor_{floor_str}_cost_heuristic.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True, png_path, json_path
        
    except Exception as e:
        return False, str(e), str(e)


def create_heatmap_from_cost(cost_map_float32):
    """
    Create a visualization heatmap from the float cost map.
    
    Used for UI visualization only. The actual heuristic is saved via
    save_cost_heuristic() which stores the raw costs for mobile processing.
    
    Args:
        cost_map_float32: Float32 cost map from calculate_movement_cost_heuristic()
    
    Returns:
        Grayscale BGR heatmap for visualization
    """
    try:
        # Normalize to 0-255
        cost_min = np.min(cost_map_float32)
        cost_max = np.max(cost_map_float32)
        
        if cost_max > cost_min:
            cost_normalized = ((cost_map_float32 - cost_min) / (cost_max - cost_min) * 255).astype(np.uint8)
        else:
            cost_normalized = np.zeros_like(cost_map_float32, dtype=np.uint8)
        
        # Invert so high cost shows dark (intuitive visualization)
        grayscale = 255 - cost_normalized
        
        # Convert to BGR for UI consistency
        heatmap = cv2.cvtColor(grayscale, cv2.COLOR_GRAY2BGR)
        
        return heatmap
    except Exception as e:
        return None


def save_cost_map(heatmap, floor_number, output_dir="outputs"):
    """
    Legacy function: Save visualization heatmap to file.
    
    Note: For mobile/API use, prefer save_cost_heuristic() which saves
    both PNG + JSON metadata suitable for pathfinding.
    
    Args:
        heatmap: The heatmap image (visualization only)
        floor_number: Floor number for filename
        output_dir: Output directory
    
    Returns:
        Tuple: (success: bool, filepath: str)
    """
    try:
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Smart floor number formatting
        if isinstance(floor_number, str):
            try:
                floor_num = float(floor_number)
            except ValueError:
                floor_num = floor_number
        else:
            floor_num = float(floor_number)
        
        if isinstance(floor_num, float) and floor_num == int(floor_num):
            floor_str = str(int(floor_num))
        else:
            floor_str = str(floor_num)
        
        output_path = f"{output_dir}/floor_{floor_str}_cost_map.png"
        cv2.imwrite(output_path, heatmap)
        
        return True, output_path
        
    except Exception as e:
        return False, str(e)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
#
# FOR MOBILE/API DEPLOYMENT (Pre-computed Heuristics with LUT):
#
#   # 1. Generate movement cost heuristic
#   cost_map, metadata = calculate_movement_cost_heuristic("floor_1.jpg")
#
#   # 2. Save as PNG + JSON with Look-Up Table (eliminates computation)
#   success, png_path, json_path = save_cost_heuristic(cost_map, metadata, floor_number=1)
#   # Outputs:
#   #   - outputs/floor_1_cost_heuristic.png (compact, PNG-compressed pixel indices)
#   #   - outputs/floor_1_cost_heuristic.json (metadata + LUT with 256 pre-computed costs)
#
#   # 3. On mobile (Kotlin) - ZERO COMPUTATION per pixel query:
#   #   - Load PNG as grayscale image
#   #   - Load JSON metadata (especially the "lut" array)
#   #   - Query cost: cost = lut[pixel_value]  // Just array indexing, O(1)
#   #   - Use in A* pathfinding with direct LUT lookups
#
#   Example Kotlin code:
#   ```kotlin
#   val costPng = loadImage("floor_1_cost_heuristic.png")
#   val metadata = loadJson("floor_1_cost_heuristic.json")
#   val lut = metadata.lut  // 256-entry Float array
#
#   fun getMovementCost(gridX: Int, gridY: Int): Float {
#       val pixelValue = costPng.getPixel(gridX, gridY)  // 0-255
#       return lut[pixelValue]  // Direct lookup, ZERO computation
#   }
#   ```
#
# FOR UI VISUALIZATION:
#
#   # Generate and visualize
#   cost_map, metadata = calculate_movement_cost_heuristic("floor_1.jpg")
#   heatmap = create_heatmap_from_cost(cost_map)  # For UI display
#   save_cost_map(heatmap, floor_number=1)  # Save visualization
#
