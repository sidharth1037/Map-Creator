"""Processing logic for the Floor Plan Vectorizer pipeline."""

import streamlit as st
import cv2
import numpy as np
import os
import json
import tempfile
import webbrowser

from pipeline_skeleton import get_skeleton
from pipeline_vectorize import process_skeleton
from pipeline_jsonfix import align_walls_globally
from pipeline_extend_endpoints import extend_endpoints
from pipeline_verifycoord import verify_json_coordinates
from pipeline_snap import snap_stairs_to_walls
from group_stair_polygons import group_stair_polygons


def process_walls(selected_image_path):
    """
    Process wall image through the full pipeline.
    
    Args:
        selected_image_path: Path to the wall image file
    
    Returns:
        Boolean indicating success
    """
    if not selected_image_path or not os.path.exists(selected_image_path):
        st.error("Please select or upload an image first")
        return False
    
    try:
        progress_bar = st.progress(0, text="Step 1: Extracting skeleton...")
        
        # Step 1: Skeleton
        original_img, skeleton_img = get_skeleton(selected_image_path)
        if skeleton_img is None:
            st.error("Failed to extract skeleton")
            return False
        
        progress_bar.progress(25, text="Step 2: Vectorizing lines...")
        
        # Step 2: Vectorize
        wall_data = process_skeleton(skeleton_img)
        if wall_data is None or len(wall_data['walls']) == 0:
            st.error("Failed to vectorize")
            return False
        
        progress_bar.progress(50, text="Step 3: Aligning walls...")
        
        # Step 3: Align
        json_lines = [
            {"x1": int(line[0]), "y1": int(line[1]), 
             "x2": int(line[2]), "y2": int(line[3])}
            for line in wall_data['walls']
        ]
        aligned_data = align_walls_globally(json_lines)
        if not aligned_data:
            st.error("Failed to align walls")
            return False
        
        progress_bar.progress(60, text="Step 4: Extending endpoints...")
        
        # Step 4: Extend free endpoints to nearby walls
        extended_data = extend_endpoints(aligned_data, snap_distance=50.0)
        if not extended_data:
            st.error("Failed to extend endpoints")
            return False
        
        progress_bar.progress(75, text="Step 5: Generating verification...")
        
        # Step 5: Verify
        verification_img = verify_json_coordinates(extended_data)
        if verification_img is None:
            st.error("Failed to generate verification image")
            return False
        
        progress_bar.progress(100, text="Complete")
        st.success("Walls processed successfully")
        
        # Save extended data for later snapping
        st.session_state.walls_aligned_data = extended_data
        
        # Save walls JSON to outputs
        os.makedirs("outputs", exist_ok=True)
        walls_json_path = f"outputs/floor_{st.session_state.current_floor}_walls.json"
        with open(walls_json_path, 'w') as f:
            json.dump(extended_data, f, indent=2)
        st.info(f"Walls saved to {walls_json_path}")
        
        # Save verification image
        output_path = f"outputs/floor_{st.session_state.current_floor}_walls_verification.png"
        cv2.imwrite(output_path, verification_img)
        
        st.session_state.walls_processed = True
        st.session_state.walls_output_path = output_path
        
        # Display and open in browser
        st.image(verification_img, channels="BGR", caption="Walls with Extended Endpoints")
        
        file_url = os.path.abspath(output_path)
        webbrowser.open(f"file:///{file_url}")
        st.info(f"Walls image opened in browser: {output_path}")
        
        # Move to stairs step
        st.session_state.current_view = 'stairs'
        st.rerun()
        
        return True
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def process_stairs(stairs_image_path):
    """
    Process stairs image through the full pipeline.
    
    Args:
        stairs_image_path: Path to the stairs image file
    
    Returns:
        Boolean indicating success
    """
    if not stairs_image_path or not os.path.exists(stairs_image_path):
        st.error("Please select or upload a stairs image first")
        return False
    
    try:
        progress_bar = st.progress(0, text="Step 1: Extracting skeleton...")
        
        # Step 1: Skeleton
        original_img, skeleton_img = get_skeleton(stairs_image_path)
        if skeleton_img is None:
            st.error("Failed to extract skeleton")
            return False
        
        progress_bar.progress(25, text="Step 2: Vectorizing lines...")
        
        # Step 2: Vectorize
        stair_data = process_skeleton(skeleton_img)
        if stair_data is None or len(stair_data['walls']) == 0:
            st.error("Failed to vectorize")
            return False
        
        progress_bar.progress(50, text="Step 3: Aligning stairs...")
        
        # Step 3: Align
        json_lines = [
            {"x1": int(line[0]), "y1": int(line[1]), 
             "x2": int(line[2]), "y2": int(line[3])}
            for line in stair_data['walls']
        ]
        aligned_data = align_walls_globally(json_lines)
        if not aligned_data:
            st.error("Failed to align stairs")
            return False
        
        progress_bar.progress(60, text="Step 4: Extending endpoints...")
        
        # Step 4: Extend free endpoints to nearby walls
        extended_data = extend_endpoints(aligned_data, snap_distance=50.0)
        if not extended_data:
            st.error("Failed to extend endpoints")
            return False
        
        progress_bar.progress(75, text="Step 5: Generating verification...")
        
        # Step 5: Verify
        verification_img = verify_json_coordinates(extended_data)
        if verification_img is None:
            st.error("Failed to generate verification image")
            return False
        
        progress_bar.progress(100, text="Complete")
        st.success("Stairs processed successfully")
        
        # Save extended data for later snapping
        st.session_state.stairs_aligned_data = extended_data
        
        # Save and open image
        os.makedirs("outputs", exist_ok=True)
        output_path = f"outputs/floor_{st.session_state.current_floor}_stairs_verification.png"
        cv2.imwrite(output_path, verification_img)
        
        st.session_state.stairs_processed = True
        st.session_state.stairs_output_path = output_path
        
        # Display and open in browser
        st.image(verification_img, channels="BGR", caption="Stairs with Extended Endpoints")
        
        file_url = os.path.abspath(output_path)
        webbrowser.open(f"file:///{file_url}")
        st.info(f"Stairs image opened in browser: {output_path}")
        
        # Move to snap step
        st.session_state.current_view = 'snap'
        st.rerun()
        
        return True
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def process_snap():
    """
    Snap stairs to walls and generate verification.
    Reads both walls and stairs from selected JSON files.
    
    Returns:
        Boolean indicating success
    """
    try:
        progress_bar = st.progress(0, text="Reading files...")
        
        # Get JSON file paths from session state
        walls_json_path = st.session_state.get('snap_walls_json')
        stairs_json_path = st.session_state.get('snap_stairs_json')
        
        if not walls_json_path or not os.path.exists(walls_json_path):
            st.error(f"Walls file not found: {walls_json_path}")
            return False
        
        if not stairs_json_path or not os.path.exists(stairs_json_path):
            st.error(f"Stairs file not found: {stairs_json_path}")
            return False
        
        # Read walls from JSON file
        with open(walls_json_path, 'r') as f:
            walls_data = json.load(f)
        
        # Read stairs from JSON file
        with open(stairs_json_path, 'r') as f:
            stairs_data = json.load(f)
        
        progress_bar.progress(20, text="Snapping stairs to walls...")
        
        # Get thresholds from session state
        endpoint_threshold = st.session_state.get('snap_endpoint_threshold', 50.0)
        line_threshold = st.session_state.get('snap_line_threshold', 30.0)
        
        # Snap stairs to walls
        snapped_stairs = snap_stairs_to_walls(
            stairs_data,
            walls_data,
            endpoint_threshold=endpoint_threshold,
            line_threshold=line_threshold
        )
        
        progress_bar.progress(70, text="Grouping stair polygons...")
        
        # Group stair segments into polygons and assign polygon IDs
        combined_segments = [{'type': 'wall', **wall} for wall in walls_data] + \
                           [{'type': 'stair', **stair} for stair in snapped_stairs]
        
        # Create temporary files for grouping
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_input:
            json.dump(combined_segments, temp_input)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            group_stair_polygons(temp_input_path, temp_output_path, visualize=False)
            with open(temp_output_path, 'r') as f:
                grouped_segments = json.load(f)
            snapped_stairs = [seg for seg in grouped_segments if seg.get('type') == 'stair']
        finally:
            try:
                os.unlink(temp_input_path)
                os.unlink(temp_output_path)
            except:
                pass
        
        progress_bar.progress(75, text="Generating verification...")
        
        # Step 3: Verify - Show walls and stairs together
        verification_img = verify_json_coordinates(walls_data, snapped_stairs)
        if verification_img is None:
            st.error("Failed to generate verification image")
            return False
        
        progress_bar.progress(100, text="Complete")
        st.success("Stairs snapped to walls successfully")
        
        # Save snapped image
        os.makedirs("outputs", exist_ok=True)
        output_path = f"outputs/floor_{st.session_state.current_floor}_stairs_snapped_verification.png"
        cv2.imwrite(output_path, verification_img)
        
        # Save snapped stairs JSON
        stairs_json_output = f"outputs/floor_{st.session_state.current_floor}_stairs.json"
        with open(stairs_json_output, 'w') as f:
            json.dump(snapped_stairs, f, indent=2)
        st.info(f"Snapped stairs saved to {stairs_json_output}")
        
        st.session_state.snapped = True
        
        # Display the combined verification image
        st.image(verification_img, channels="BGR", caption="Final Verification: Walls (Green) + Snapped Stairs (Magenta)")
        
        # Open in browser
        file_url = os.path.abspath(output_path)
        webbrowser.open(f"file:///{file_url}")
        st.info(f"Snapped stairs image opened in browser: {output_path}")
        st.rerun()
        
        return True
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def process_visualize(uploaded_files):
    """
    Visualize multiple JSON files on a single image with different colors.
    
    Args:
        uploaded_files: List of Streamlit UploadedFile objects
    
    Returns:
        Boolean indicating success
    """
    try:
        # Validate input
        if not uploaded_files:
            st.error("Please upload at least one JSON file")
            return False
        
        # Color palette for different files (BGR format)
        colors = [
            (0, 180, 0),      # Green
            (255, 0, 255),    # Magenta
            (0, 165, 255),    # Orange
            (255, 255, 0),    # Cyan
            (0, 255, 255),    # Yellow
            (255, 0, 0),      # Blue
            (0, 0, 255),      # Red
            (255, 127, 0),    # Azure
            (0, 127, 255),    # Orange (alt)
            (127, 0, 255),    # Purple
        ]
        
        # Load all data
        all_data = []
        file_names = []
        
        for uploaded_file in uploaded_files:
            # Load JSON data from uploaded file
            try:
                content = uploaded_file.getvalue().decode("utf-8")
                data = json.loads(content)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON in {uploaded_file.name}: {str(e)}")
                return False
            except Exception as e:
                st.error(f"Failed to load {uploaded_file.name}: {str(e)}")
                return False
            
            if not data or len(data) == 0:
                st.warning(f"Skipping empty file: {uploaded_file.name}")
                continue
            
            all_data.append(data)
            file_names.append(uploaded_file.name)
        
        if not all_data:
            st.error("No valid data to visualize")
            return False
        
        # Calculate canvas size
        all_x = []
        all_y = []
        
        for data in all_data:
            for item in data:
                if isinstance(item, dict):
                    if 'x1' in item and 'y1' in item:
                        all_x.append(item['x1'])
                        all_y.append(item['y1'])
                        if 'x2' in item:
                            all_x.append(item['x2'])
                        if 'y2' in item:
                            all_y.append(item['y2'])
        
        if not all_x or not all_y:
            st.error("No coordinate data found in files")
            return False
        
        max_x, max_y = max(all_x), max(all_y)
        h, w = max_y + 150, max_x + 150
        img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background
        
        # Draw each file's data in a different color
        for file_idx, data in enumerate(all_data):
            color = colors[file_idx % len(colors)]
            
            for item in data:
                if isinstance(item, dict) and 'x1' in item and 'y1' in item:
                    x1, y1 = int(item['x1']), int(item['y1'])
                    x2 = int(item.get('x2', x1))
                    y2 = int(item.get('y2', y1))
                    
                    cv2.line(img, (x1, y1), (x2, y2), color, 2)
        
        # Collect all unique vertices
        unique_points = set()
        for data in all_data:
            for item in data:
                if isinstance(item, dict) and 'x1' in item and 'y1' in item:
                    unique_points.add((int(item['x1']), int(item['y1'])))
                    if 'x2' in item and 'y2' in item:
                        unique_points.add((int(item['x2']), int(item['y2'])))
        
        # Draw vertices
        font = cv2.FONT_HERSHEY_SIMPLEX
        for pt in unique_points:
            x, y = pt
            cv2.circle(img, (x, y), 4, (0, 0, 255), -1)  # Red dots
            coord_text = f"({x},{y})"
            cv2.putText(img, coord_text, (x + 8, y - 8), font, 0.35, (0, 0, 0), 1, cv2.LINE_AA)
        
        # Draw legend
        legend_y = h - 20 - (len(file_names) * 20)
        cv2.putText(img, "Legend:", (20, legend_y), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        
        for idx, filename in enumerate(file_names):
            y_pos = legend_y + 20 + (idx * 20)
            color = colors[idx % len(colors)]
            cv2.line(img, (20, y_pos - 5), (70, y_pos - 5), color, 2)
            cv2.putText(img, filename, (80, y_pos), font, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        
        st.success(f"Visualizing {len(file_names)} JSON files")
        st.image(img, channels="BGR", caption="Combined Visualization")
        
        # Save visualization
        os.makedirs("outputs", exist_ok=True)
        output_name = "_".join([os.path.splitext(f)[0] for f in file_names])[:50]  # Limit name length
        output_path = f"outputs/{output_name}_combined_visualization.png"
        cv2.imwrite(output_path, img)
        st.info(f"Visualization saved to {output_path}")
        
        # Open in browser
        file_url = os.path.abspath(output_path)
        webbrowser.open(f"file:///{file_url}")
        
        return True
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False
