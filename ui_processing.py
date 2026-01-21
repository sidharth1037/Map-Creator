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
        
        # Save stairs JSON to outputs
        os.makedirs("outputs", exist_ok=True)
        stairs_json_path = f"outputs/floor_{st.session_state.current_floor}_stairs.json"
        with open(stairs_json_path, 'w') as f:
            json.dump(extended_data, f, indent=2)
        st.info(f"Stairs saved to {stairs_json_path}")
        
        # Save verification image
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


def process_visualize(uploaded_files, show_labels=True):
    """
    Visualize multiple JSON files on a single image with different colors.
    
    Args:
        uploaded_files: List of Streamlit UploadedFile objects
        show_labels: Boolean to show/hide coordinate labels
    
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
            # Handle segment data (x1, y1, x2, y2), entrance data (x, y), and room data (x, y)
            if isinstance(data, dict):
                if 'entrances' in data:
                    # This is an entrances JSON with 'entrances' array
                    for item in data.get('entrances', []):
                        if isinstance(item, dict) and 'x' in item and 'y' in item:
                            all_x.append(item['x'])
                            all_y.append(item['y'])
                elif 'rooms' in data:
                    # This is a rooms JSON with 'rooms' array
                    for item in data.get('rooms', []):
                        if isinstance(item, dict) and 'x' in item and 'y' in item:
                            all_x.append(item['x'])
                            all_y.append(item['y'])
                else:
                    # This is segment data (walls, stairs) - data is a dict but not entrances/rooms
                    # Skip dict-based non-segment data
                    pass
            else:
                # This is segment data as array (walls, stairs)
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
            
            # Check if this is entrances/rooms data or segment data
            if isinstance(data, dict):
                if 'entrances' in data:
                    # Draw entrances as points
                    for item in data.get('entrances', []):
                        if isinstance(item, dict) and 'x' in item and 'y' in item:
                            x, y = int(item['x']), int(item['y'])
                            cv2.circle(img, (x, y), 6, color, -1)  # Filled circle for entrance
                elif 'rooms' in data:
                    # Draw rooms as points
                    for item in data.get('rooms', []):
                        if isinstance(item, dict) and 'x' in item and 'y' in item:
                            x, y = int(item['x']), int(item['y'])
                            cv2.circle(img, (x, y), 6, color, -1)  # Filled circle for room centroid
                else:
                    # This is not a recognized format
                    pass
            else:
                # Draw segments (walls, stairs)
                for item in data:
                    if isinstance(item, dict) and 'x1' in item and 'y1' in item:
                        x1, y1 = int(item['x1']), int(item['y1'])
                        x2 = int(item.get('x2', x1))
                        y2 = int(item.get('y2', y1))
                        
                        cv2.line(img, (x1, y1), (x2, y2), color, 2)
        
        # Collect all unique vertices
        unique_points = set()
        for data in all_data:
            if isinstance(data, dict) and ('entrances' in data or 'rooms' in data):
                # Skip entrance/room points from vertex collection (they're already drawn as filled circles)
                pass
            else:
                # Collect segment endpoints
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
            if show_labels:
                coord_text = f"({x},{y})"
                cv2.putText(img, coord_text, (x + 8, y - 8), font, 0.35, (0, 0, 0), 1, cv2.LINE_AA)
        
        # Draw legend (only if show_labels is True)
        if show_labels:
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


def process_floor_connections(walls_json_path, stairs_json_path):
    """
    Display walls and stairs with Plotly and allow setting floor connections.
    """
    import plotly.graph_objects as go
    
    if not walls_json_path or not stairs_json_path:
        st.error("Please select both walls and stairs JSON files")
        return None, None
    
    if not os.path.exists(walls_json_path):
        st.error(f"Walls file not found: {walls_json_path}")
        return None, None
    
    if not os.path.exists(stairs_json_path):
        st.error(f"Stairs file not found: {stairs_json_path}")
        return None, None
    
    # Load data
    with open(walls_json_path, 'r') as f:
        walls_data = json.load(f)
    
    with open(stairs_json_path, 'r') as f:
        stairs_data = json.load(f)
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add walls (blue lines)
    for item in walls_data:
        if isinstance(item, dict) and 'x1' in item and 'y1' in item:
            x1, y1 = item['x1'], item['y1']
            x2 = item.get('x2', x1)
            y2 = item.get('y2', y1)
            fig.add_trace(go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode='lines',
                line=dict(color='blue', width=2),
                hoverinfo='skip',
                showlegend=False
            ))
    
    # Add stairs (red lines) with polygon IDs
    stair_polygons = {}
    for item in stairs_data:
        if isinstance(item, dict) and 'x1' in item and 'y1' in item:
            x1, y1 = item['x1'], item['y1']
            x2 = item.get('x2', x1)
            y2 = item.get('y2', y1)
            poly_id = item.get('stair_polygon_id', -1)
            
            # Track polygon centers for labels
            if poly_id not in stair_polygons:
                stair_polygons[poly_id] = {'xs': [], 'ys': []}
            stair_polygons[poly_id]['xs'].extend([x1, x2])
            stair_polygons[poly_id]['ys'].extend([y1, y2])
            
            fig.add_trace(go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode='lines',
                line=dict(color='red', width=3),
                hovertext=f"Stair Polygon {poly_id}",
                hoverinfo='text',
                showlegend=False
            ))
    
    # Add polygon ID labels at centroid
    for poly_id, coords in stair_polygons.items():
        if coords['xs'] and coords['ys']:
            center_x = np.mean(coords['xs'])
            center_y = np.mean(coords['ys'])
            fig.add_trace(go.Scatter(
                x=[center_x],
                y=[center_y],
                mode='text',
                text=[f"P{poly_id}"],
                textposition='middle center',
                textfont=dict(size=12, color='red'),
                hoverinfo='skip',
                showlegend=False
            ))
    
    # Update layout
    fig.update_layout(
        title=f"Walls (Blue) and Stairs (Red) with Polygon IDs",
        xaxis_title="X",
        yaxis_title="Y",
        hovermode='closest',
        height=600,
        showlegend=False,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, width='stretch')
    
    return walls_data, stairs_data


def save_floor_connection(stairs_json_path, connections_list):
    """
    Save multiple floor connections to stairs JSON file.
    
    Args:
        stairs_json_path: Path to stairs JSON file
        connections_list: List of dicts with 'polygon_id', 'from_floor', 'to_floor'
    """
    try:
        if not connections_list:
            st.error("No connections to save")
            return False
        
        # Load current stairs data
        with open(stairs_json_path, 'r') as f:
            stairs_data = json.load(f)
        
        # Create a mapping of polygon IDs to floor connections
        conn_map = {}
        for conn in connections_list:
            poly_id = conn['polygon_id']
            conn_data = [float(conn['from_floor']), float(conn['to_floor'])]
            conn_map[poly_id] = conn_data
        
        # Update all segments with the specified polygon IDs
        total_updated = 0
        updated_segments_info = {}
        
        for item in stairs_data:
            if isinstance(item, dict) and 'stair_polygon_id' in item:
                poly_id = item['stair_polygon_id']
                if poly_id in conn_map:
                    item['floors_connected'] = conn_map[poly_id]
                    total_updated += 1
                    if poly_id not in updated_segments_info:
                        updated_segments_info[poly_id] = 0
                    updated_segments_info[poly_id] += 1
        
        if total_updated == 0:
            st.error("No segments found with the specified polygon IDs")
            return False
        
        # Save updated data back to the SAME stairs JSON file
        with open(stairs_json_path, 'w') as f:
            json.dump(stairs_data, f, indent=2)
        
        # Display confirmation
        st.success(f"✅ Floor connections saved to {stairs_json_path}")
        
        # Show summary
        with st.expander("📊 Save Summary", expanded=True):
            st.write(f"**Total connections added:** {len(connections_list)}")
            st.write(f"**Total segments updated:** {total_updated}")
            st.write("**Segments by polygon:**")
            for poly_id, count in sorted(updated_segments_info.items()):
                from_f, to_f = conn_map[poly_id]
                st.write(f"  • Polygon {poly_id}: {count} segments ({from_f} ↔ {to_f})")
        
        return True
        
    except Exception as e:
        st.error(f"Error saving floor connections: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False


def process_entrances_plot(walls_json_path, stairs_json_path=None):
    """
    Plot walls and extract unique points from coordinates.
    Points are extracted from segment endpoints and given sequential IDs.
    
    Args:
        walls_json_path: Path to walls JSON file
        stairs_json_path: Optional path to stairs JSON file
    
    Returns:
        Tuple of (walls_data, points_dict) where points_dict is {point_id: (x, y)}
    """
    import plotly.graph_objects as go
    
    if not walls_json_path:
        st.error("Please select walls JSON file")
        return None, None
    
    if not os.path.exists(walls_json_path):
        st.error(f"Walls file not found: {walls_json_path}")
        return None, None
    
    # Load walls
    with open(walls_json_path, 'r') as f:
        walls_data = json.load(f)
    
    # Load stairs if provided
    stairs_data = []
    if stairs_json_path and os.path.exists(stairs_json_path):
        with open(stairs_json_path, 'r') as f:
            stairs_data = json.load(f)
    
    # Extract unique points from both walls and stairs
    unique_points = {}  # {(x, y): point_id}
    point_id_counter = 0
    
    all_segments = walls_data + stairs_data
    
    for seg in all_segments:
        if isinstance(seg, dict) and 'x1' in seg and 'y1' in seg:
            # Extract x1, y1
            p1 = (seg['x1'], seg['y1'])
            if p1 not in unique_points:
                unique_points[p1] = point_id_counter
                point_id_counter += 1
            
            # Extract x2, y2
            if 'x2' in seg and 'y2' in seg:
                p2 = (seg['x2'], seg['y2'])
                if p2 not in unique_points:
                    unique_points[p2] = point_id_counter
                    point_id_counter += 1
    
    # Create reverse mapping for display
    points_dict = {v: k for k, v in unique_points.items()}
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add walls (blue lines)
    for item in walls_data:
        if isinstance(item, dict) and 'x1' in item and 'y1' in item:
            x1, y1 = item['x1'], item['y1']
            x2 = item.get('x2', x1)
            y2 = item.get('y2', y1)
            fig.add_trace(go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode='lines',
                line=dict(color='blue', width=2),
                hoverinfo='skip',
                showlegend=False
            ))
    
    # Add stairs if available (red lines)
    if stairs_data:
        for item in stairs_data:
            if isinstance(item, dict) and 'x1' in item and 'y1' in item:
                x1, y1 = item['x1'], item['y1']
                x2 = item.get('x2', x1)
                y2 = item.get('y2', y1)
                fig.add_trace(go.Scatter(
                    x=[x1, x2],
                    y=[y1, y2],
                    mode='lines',
                    line=dict(color='red', width=2),
                    hoverinfo='skip',
                    showlegend=False
                ))
    
    # Add points (red dots with IDs)
    point_xs = []
    point_ys = []
    point_ids = []
    point_coords = []
    
    for pid in sorted(points_dict.keys()):
        x, y = points_dict[pid]
        point_xs.append(x)
        point_ys.append(y)
        point_ids.append(f"P{pid}")
        point_coords.append(f"({int(x)}, {int(y)})")
    
    fig.add_trace(go.Scatter(
        x=point_xs,
        y=point_ys,
        mode='markers+text',
        marker=dict(size=10, color='darkred'),
        text=point_ids,
        textposition='top center',
        textfont=dict(size=11, color='darkred', family='monospace'),
        hovertext=point_coords,
        hoverinfo='text',
        showlegend=False
    ))
    
    # Update layout with equal aspect ratio and white background
    fig.update_layout(
        title=f"Walls and Extracted Points ({len(points_dict)} unique points)",
        xaxis_title="X",
        yaxis_title="Y",
        hovermode='closest',
        height=700,
        showlegend=False,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, width='stretch')
    
    st.info(f"📍 Total unique points extracted: {len(points_dict)}")
    
    return walls_data, points_dict


def save_entrances(floor_number, entrances_list, points_dict):
    """
    Save entrances to JSON file.
    
    Args:
        floor_number: Floor number for the output file
        entrances_list: List of entrance dictionaries
        points_dict: Dictionary mapping point_id to (x, y) coordinates
    
    Returns:
        Boolean indicating success
    """
    try:
        from pipeline_entrances import save_entrances_json, create_entrance_from_pair
        
        if not entrances_list:
            st.error("No entrances to save")
            return False
        
        if not points_dict:
            st.error("No points data available")
            return False
        
        try:
            floor = float(floor_number)
        except (ValueError, TypeError):
            st.error("Invalid floor number")
            return False
        
        # Format floor number for filename: use int if it's a whole number, else use float
        if floor == int(floor):
            floor_str = str(int(floor))
        else:
            floor_str = str(floor)
        
        # Create entrance objects with IDs
        entrances = []
        for idx, ent in enumerate(entrances_list, 1):
            entrance = create_entrance_from_pair(
                ent['point1_id'],
                ent['point2_id'],
                points_dict,
                name=ent.get('name') or None,
                room_no=ent.get('room_no') or None,
                stairs=ent.get('stairs', False),
                entrance_id=idx
            )
            if entrance:
                entrances.append(entrance)
        
        if not entrances:
            st.error("Failed to create any entrances")
            return False
        
        # Save to file
        output_file = f"outputs/floor_{floor_str}_entrances.json"
        save_entrances_json(entrances, output_file)
        
        st.success(f"✅ Saved {len(entrances)} entrances to {output_file}")
        
        with st.expander("📊 Save Summary", expanded=True):
            st.write(f"**Total entrances created:** {len(entrances)}")
            for ent in entrances:
                stairs_badge = " 🪜" if ent.get('stairs') else ""
                st.write(f"  • Entry {ent['id']}: {ent.get('name', '(no name)')} | Room: {ent.get('room_no', 'N/A')} | ({ent['x']}, {ent['y']}){stairs_badge}")
        
        return True
        
    except Exception as e:
        st.error(f"Error saving entrances: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False


def process_rooms_plot(walls_json_path):
    """
    Generate a visualization of walls with extracted points for room definition.
    
    Args:
        walls_json_path: Path to walls JSON file
    
    Returns:
        Tuple: (walls_data, points_dict) where points_dict = {point_id: (x, y)}
    """
    try:
        import plotly.graph_objects as go
        
        # Load walls JSON
        with open(walls_json_path, 'r') as f:
            walls_data = json.load(f)
        
        if not walls_data:
            st.error("No walls data found")
            return None, None
        
        # Extract unique points from segments
        points_dict = {}
        point_counter = 0
        
        for segment in walls_data:
            if isinstance(segment, dict) and 'x1' in segment and 'y1' in segment:
                p1 = (int(segment['x1']), int(segment['y1']))
                p2 = (int(segment['x2']) if 'x2' in segment else int(segment['x1']),
                      int(segment['y2']) if 'y2' in segment else int(segment['y1']))
                
                # Add first point if not already present
                if p1 not in points_dict.values():
                    points_dict[f"P{point_counter}"] = p1
                    point_counter += 1
                
                # Add second point if different
                if p2 not in points_dict.values():
                    points_dict[f"P{point_counter}"] = p2
                    point_counter += 1
        
        st.info(f"Extracted {len(points_dict)} unique points")
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add walls
        for segment in walls_data:
            if isinstance(segment, dict) and 'x1' in segment and 'y1' in segment:
                x1, y1 = segment['x1'], segment['y1']
                x2 = segment.get('x2', x1)
                y2 = segment.get('y2', y1)
                
                fig.add_trace(go.Scatter(
                    x=[x1, x2],
                    y=[y1, y2],
                    mode='lines',
                    line=dict(color='blue', width=2),
                    hoverinfo='skip',
                    showlegend=False
                ))
        
        # Add points with labels
        point_ids = list(points_dict.keys())
        point_coords = list(points_dict.values())
        
        if point_coords:
            xs = [p[0] for p in point_coords]
            ys = [p[1] for p in point_coords]
            
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode='markers+text',
                marker=dict(color='darkred', size=8),
                text=point_ids,
                textposition='top center',
                textfont=dict(size=10, color='darkred'),
                hoverinfo='skip',
                showlegend=False
            ))
        
        # Update layout
        fig.update_layout(
            title="Room Definition - Select 4 Points to Form Quadrilateral",
            xaxis_title="X",
            yaxis_title="Y",
            height=700,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1)
        )
        
        st.plotly_chart(fig, width='stretch')
        
        return walls_data, points_dict
        
    except FileNotFoundError:
        st.error(f"Walls file not found: {walls_json_path}")
        return None, None
    except json.JSONDecodeError:
        st.error("Invalid JSON in walls file")
        return None, None
    except Exception as e:
        st.error(f"Error processing rooms plot: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None


def save_rooms(floor_number, rooms_list, points_dict):
    """
    Save rooms data to JSON file with parsed name/number attributes.
    
    Args:
        floor_number: Floor number (int or float)
        rooms_list: List of room dicts with point IDs and names
        points_dict: Dict mapping point_id to (x, y) coordinates
    
    Returns:
        Boolean indicating success
    """
    try:
        from pipeline_rooms import create_room_from_points, save_rooms_json
        
        if not floor_number or not rooms_list or not points_dict:
            st.error("Missing floor number, rooms, or points")
            return False
        
        # Convert points_dict format: {point_id_str: (x, y)} -> {point_id_str: (x, y)}
        # Need to handle "P0" -> 0 mapping
        points_numeric = {}
        for point_id_str, coord in points_dict.items():
            # Extract number from "P0", "P1", etc.
            if point_id_str.startswith('P'):
                numeric_id = point_id_str[1:]
                points_numeric[numeric_id] = coord
            else:
                points_numeric[point_id_str] = coord
        
        # Create room objects
        rooms = []
        for idx, room_data in enumerate(rooms_list):
            try:
                p1_id = room_data['point1_id']
                p2_id = room_data['point2_id']
                p3_id = room_data['point3_id']
                p4_id = room_data['point4_id']
                room_name = room_data['name']
                
                room = create_room_from_points(
                    p1_id, p2_id, p3_id, p4_id,
                    points_numeric,
                    room_name,
                    room_id=idx + 1
                )
                if room:
                    rooms.append(room)
            except Exception as e:
                st.warning(f"Failed to create room {idx + 1}: {str(e)}")
                continue
        
        if not rooms:
            st.error("Failed to create any rooms")
            return False
        
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
        
        # Save to file
        output_file = f"outputs/floor_{floor_str}_rooms.json"
        save_rooms_json(rooms, output_file)
        
        st.success(f"✅ Saved {len(rooms)} rooms to {output_file}")
        
        with st.expander("📊 Save Summary", expanded=True):
            st.write(f"**Total rooms created:** {len(rooms)}")
            for room in rooms:
                room_label = f"{room['number']}: {room['name']}" if room['number'] else room['name']
                st.write(f"  • Room {room['id']}: {room_label} | Center: ({room['x']:.1f}, {room['y']:.1f}) | Points: {room['point_ids']}")
        
        return True
        
    except Exception as e:
        st.error(f"Error saving rooms: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False


def process_match(reference_json_path, target_json_path, threshold):
    """
    Match and snap target floor coordinates to reference floor.
    
    Args:
        reference_json_path: Path to reference JSON file
        target_json_path: Path to target JSON file to be modified
        threshold: Snapping threshold in pixels
    
    Returns:
        Boolean indicating success
    """
    try:
        from pipeline_match import load_json, save_json, match_coordinates
        
        if not reference_json_path or not target_json_path:
            st.error("Please select both reference and target files")
            return False
        
        if not os.path.exists(reference_json_path):
            st.error(f"Reference file not found: {reference_json_path}")
            return False
        
        if not os.path.exists(target_json_path):
            st.error(f"Target file not found: {target_json_path}")
            return False
        
        # Load both files
        try:
            reference_data = load_json(reference_json_path)
            target_data = load_json(target_json_path)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {str(e)}")
            return False
        
        if not reference_data or not target_data:
            st.error("One or both JSON files are empty")
            return False
        
        st.info(f"Reference file: {os.path.basename(reference_json_path)}")
        st.info(f"Target file: {os.path.basename(target_json_path)}")
        st.info(f"Snapping threshold: {threshold} pixels")
        
        # Perform matching
        progress_bar = st.progress(0, text="Analyzing coordinates...")
        
        modified_target, stats = match_coordinates(reference_data, target_data, threshold=threshold)
        
        progress_bar.progress(50, text="Saving matched coordinates...")
        
        # Save modified target
        save_json(modified_target, target_json_path)
        
        progress_bar.progress(100, text="Complete")
        
        st.success(f"✅ Successfully matched and saved {target_json_path}")
        
        # Show statistics
        with st.expander("📊 Matching Summary", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Reference Points", stats['total_reference_points'])
            with col2:
                st.metric("Target Lines", stats['total_lines'])
            with col3:
                st.metric("Vertical Lines Snapped", stats['vertical_lines_snapped'])
            with col4:
                st.metric("Horizontal Lines Snapped", stats['horizontal_lines_snapped'])
            
            st.write(f"**Result:** {stats['vertical_lines_snapped'] + stats['horizontal_lines_snapped']} out of {stats['total_lines']} building walls were snapped to reference coordinates within {threshold}px threshold ({stats['snap_percentage']:.1f}%).")
        
        return True
        
    except Exception as e:
        st.error(f"Error during matching: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False


def process_boundary_plot(walls_json_path, boundary_polygons, stairs_json_path=None):
    """
    Generate a visualization of walls with extracted points and boundary polygons.
    
    Args:
        walls_json_path: Path to walls JSON file
        boundary_polygons: List of polygon dicts with {name, points} or empty list
        stairs_json_path: Optional path to stairs JSON file
    
    Returns:
        Tuple: (figure, points_dict) where points_dict = {point_id: (x, y)}
    """
    try:
        import plotly.graph_objects as go
        
        # Load walls JSON
        with open(walls_json_path, 'r') as f:
            walls_data = json.load(f)
        
        if not walls_data:
            st.error("No walls data found")
            return None, None
        
        # Extract unique points from walls and stairs
        points_dict = {}
        point_counter = 0
        
        for segment in walls_data:
            if isinstance(segment, dict) and 'x1' in segment and 'y1' in segment:
                p1 = (int(segment['x1']), int(segment['y1']))
                p2 = (int(segment['x2']) if 'x2' in segment else int(segment['x1']),
                      int(segment['y2']) if 'y2' in segment else int(segment['y1']))
                
                # Add first point if not already present
                if p1 not in points_dict.values():
                    points_dict[f"P{point_counter}"] = p1
                    point_counter += 1
                
                # Add second point if different
                if p2 not in points_dict.values():
                    points_dict[f"P{point_counter}"] = p2
                    point_counter += 1
        
        # Extract points from stairs if provided
        if stairs_json_path and os.path.exists(stairs_json_path):
            try:
                with open(stairs_json_path, 'r') as f:
                    stairs_data = json.load(f)
                
                stairs_segments = stairs_data if isinstance(stairs_data, list) else stairs_data.get('stairs', [])
                
                for segment in stairs_segments:
                    if isinstance(segment, dict) and 'x1' in segment and 'y1' in segment:
                        p1 = (int(segment['x1']), int(segment['y1']))
                        p2 = (int(segment['x2']) if 'x2' in segment else int(segment['x1']),
                              int(segment['y2']) if 'y2' in segment else int(segment['y1']))
                        
                        # Add first point if not already present
                        if p1 not in points_dict.values():
                            points_dict[f"P{point_counter}"] = p1
                            point_counter += 1
                        
                        # Add second point if different
                        if p2 not in points_dict.values():
                            points_dict[f"P{point_counter}"] = p2
                            point_counter += 1
            except Exception as e:
                st.warning(f"Could not extract stairs points: {str(e)}")
        
        st.info(f"Extracted {len(points_dict)} unique points from walls and stairs")
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add walls
        for segment in walls_data:
            if isinstance(segment, dict) and 'x1' in segment and 'y1' in segment:
                x1, y1 = segment['x1'], segment['y1']
                x2 = segment.get('x2', x1)
                y2 = segment.get('y2', y1)
                
                fig.add_trace(go.Scatter(
                    x=[x1, x2],
                    y=[y1, y2],
                    mode='lines',
                    line=dict(color='blue', width=2),
                    hoverinfo='skip',
                    showlegend=False
                ))
        
        # Add stairs if provided
        if stairs_json_path and os.path.exists(stairs_json_path):
            try:
                with open(stairs_json_path, 'r') as f:
                    stairs_data = json.load(f)
                
                # Extract segments - handle both list and dict formats
                stairs_segments = stairs_data if isinstance(stairs_data, list) else stairs_data.get('stairs', [])
                
                for segment in stairs_segments:
                    if isinstance(segment, dict) and 'x1' in segment and 'y1' in segment:
                        x1, y1 = segment['x1'], segment['y1']
                        x2 = segment.get('x2', x1)
                        y2 = segment.get('y2', y1)
                        
                        fig.add_trace(go.Scatter(
                            x=[x1, x2],
                            y=[y1, y2],
                            mode='lines',
                            line=dict(color='orange', width=2),
                            hoverinfo='skip',
                            showlegend=False
                        ))
            except Exception as e:
                st.warning(f"Could not load stairs data: {str(e)}")
        
        # Add all available points with labels
        if points_dict:
            point_ids = list(points_dict.keys())
            point_coords = list(points_dict.values())
            xs = [p[0] for p in point_coords]
            ys = [p[1] for p in point_coords]
            
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode='markers+text',
                marker=dict(color='darkgreen', size=6),
                text=point_ids,
                textposition='top center',
                textfont=dict(size=9, color='darkgreen'),
                hoverinfo='skip',
                showlegend=False,
                name='Available Points'
            ))
        
        # Add boundary polygons and connecting lines
        colors = ['red', 'purple', 'orange', 'cyan', 'magenta', 'lime', 'yellow']
        
        if boundary_polygons and len(boundary_polygons) > 0:
            for poly_idx, polygon in enumerate(boundary_polygons):
                points = polygon.get('points', [])
                if points and len(points) > 0:
                    # Get boundary coordinates
                    boundary_xs = [p['x'] for p in points]
                    boundary_ys = [p['y'] for p in points]
                    
                    # Close the polygon by adding first point at the end
                    boundary_xs_closed = boundary_xs + [boundary_xs[0]]
                    boundary_ys_closed = boundary_ys + [boundary_ys[0]]
                    
                    # Pick color for this polygon
                    color = colors[poly_idx % len(colors)]
                    
                    # Add boundary lines
                    fig.add_trace(go.Scatter(
                        x=boundary_xs_closed,
                        y=boundary_ys_closed,
                        mode='lines',
                        line=dict(color=color, width=3),
                        name=f"{polygon.get('name', 'Polygon')}",
                        hoverinfo='skip',
                        showlegend=True
                    ))
                    
                    # Add boundary points with labels
                    fig.add_trace(go.Scatter(
                        x=boundary_xs,
                        y=boundary_ys,
                        mode='markers+text',
                        marker=dict(color=color, size=10),
                        text=[f"{polygon.get('name', 'P')}_{i}" for i in range(len(points))],
                        textposition='top center',
                        textfont=dict(size=10, color=color),
                        name=f"{polygon.get('name', 'Polygon')} Points",
                        hoverinfo='skip',
                        showlegend=True
                    ))
        
        # Update layout
        fig.update_layout(
            title="Floor Plan with Boundary Definition (Blue=Walls, Orange=Stairs, Green=Available Points, Colored=Boundaries)",
            xaxis_title="X",
            yaxis_title="Y",
            height=700,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1)
        )
        
        return fig, points_dict
        
    except FileNotFoundError:
        st.error(f"Walls file not found: {walls_json_path}")
        return None, None
    except json.JSONDecodeError:
        st.error("Invalid JSON in walls file")
        return None, None
    except Exception as e:
        st.error(f"Error processing boundary plot: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None


def save_boundary(floor_number, boundary_polygons):
    """
    Save boundary polygons to JSON file.
    
    Args:
        floor_number: Floor number (int or float or string)
        boundary_polygons: List of polygon dicts with {name, points}
    
    Returns:
        Boolean indicating success
    """
    try:
        from pipeline_boundary import save_boundary_json
        
        if not floor_number:
            st.error("Please enter a floor number")
            return False
        
        # Check that at least one polygon has points
        total_points = sum(len(p.get('points', [])) for p in boundary_polygons)
        if total_points < 3:
            st.error("Please define at least 3 boundary points total across all polygons")
            return False
        
        # Save using pipeline function
        success, result = save_boundary_json(boundary_polygons, floor_number)
        
        if success:
            st.success(f"✅ Boundary saved to {result}")
            
            with st.expander("📊 Boundary Summary", expanded=True):
                st.write(f"**Floor:** {floor_number}")
                st.write(f"**Total polygons:** {len(boundary_polygons)}")
                for poly in boundary_polygons:
                    st.write(f"**{poly['name']}:** {len(poly.get('points', []))} points")
                    for point in poly.get('points', []):
                        st.write(f"  • B{point['id']}: ({point['x']}, {point['y']})")
            
            return True
        else:
            st.error(f"Failed to save boundary: {result}")
            return False
        
    except Exception as e:
        st.error(f"Error saving boundary: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False


def load_boundary(boundary_json_path):
    """
    Load an existing boundary file and extract polygons for editing.
    Handles both new format (multiple polygons) and legacy format.
    
    Args:
        boundary_json_path: Path to the boundary JSON file
    
    Returns:
        Tuple: (boundary_polygons, floor_number, walls_json_path)
               or (None, None, None) on failure
    """
    try:
        if not boundary_json_path or not os.path.exists(boundary_json_path):
            st.error("Boundary file not found")
            return None, None, None
        
        with open(boundary_json_path, 'r') as f:
            boundary_data = json.load(f)
        
        floor_number = boundary_data.get('floor', '')
        
        # Handle new format (multiple polygons)
        if 'polygons' in boundary_data:
            boundary_polygons = boundary_data.get('polygons', [])
            if not boundary_polygons:
                st.error("No polygons found in file")
                return None, None, None
            polygon_count = len(boundary_polygons)
            point_count = sum(len(p.get('points', [])) for p in boundary_polygons)
        # Handle legacy format (single polygon)
        else:
            boundary_points = boundary_data.get('boundary_points', [])
            if not boundary_points:
                st.error("No boundary points found in file")
                return None, None, None
            boundary_polygons = [{"name": "Imported Boundary", "points": boundary_points}]
            polygon_count = 1
            point_count = len(boundary_points)
        
        # Try to find corresponding walls file
        json_dir = "outputs"
        walls_filename = f"floor_{floor_number}_walls.json"
        walls_json_path = os.path.join(json_dir, walls_filename)
        
        if not os.path.exists(walls_json_path):
            st.warning(f"Walls file not found: {walls_filename}")
            walls_json_path = None
        
        st.success(f"✅ Loaded {polygon_count} polygon(s) with {point_count} total points from floor {floor_number}")
        
        return boundary_polygons, floor_number, walls_json_path
        
    except json.JSONDecodeError:
        st.error("Invalid JSON in boundary file")
        return None, None, None
    except Exception as e:
        st.error(f"Error loading boundary: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None, None


def process_cost_map(uploaded_image):
    """
    Generate a cost map from an uploaded floor plan image.
    
    Args:
        uploaded_image: Streamlit UploadedFile object
    
    Returns:
        Tuple: (cost_map, heatmap, cost_normalized) or (None, None, None) on failure
    """
    try:
        from pipeline_cost_map import generate_cost_map, create_heatmap
        
        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(uploaded_image.getbuffer())
            tmp_path = tmp_file.name
        
        # Generate cost map
        cost_map, cost_normalized = generate_cost_map(tmp_path)
        
        if cost_map is None:
            st.error("Failed to process image")
            return None, None, None
        
        # Create heatmap visualization
        heatmap = create_heatmap(cost_normalized)
        
        if heatmap is None:
            st.error("Failed to create heatmap")
            return None, None, None
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        st.success("✅ Cost map generated successfully")
        st.info(f"Cost range: {cost_map.min():.2f} to {cost_map.max():.2f}")
        
        return cost_map, heatmap, cost_normalized
        
    except Exception as e:
        st.error(f"Error generating cost map: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None, None


def process_cost_heuristic(uploaded_image):
    """
    Generate movement cost heuristic from an uploaded floor plan image.
    Suitable for pre-computation for mobile/API use.
    
    Args:
        uploaded_image: Streamlit UploadedFile object
    
    Returns:
        Tuple: (cost_map_float32, metadata, heatmap) or (None, None, None) on failure
    """
    try:
        from pipeline_cost_map import calculate_movement_cost_heuristic, create_heatmap_from_cost
        
        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(uploaded_image.getbuffer())
            tmp_path = tmp_file.name
        
        # Generate movement cost heuristic (Kotlin-compatible formula)
        cost_map, metadata = calculate_movement_cost_heuristic(tmp_path)
        
        if cost_map is None:
            st.error("Failed to process image")
            return None, None, None
        
        # Create heatmap visualization
        heatmap = create_heatmap_from_cost(cost_map)
        
        if heatmap is None:
            st.error("Failed to create heatmap")
            return None, None, None
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        st.success("✅ Cost heuristic generated successfully")
        st.info(f"Movement cost range: {metadata['cost_min']:.2f} to {metadata['cost_max']:.2f}")
        st.info(f"Image dimensions: {metadata['image_width']}x{metadata['image_height']}")
        
        return cost_map, metadata, heatmap
        
    except Exception as e:
        st.error(f"Error generating cost heuristic: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None, None


def save_cost_map(heatmap, floor_number):
    """
    Save the cost map heatmap to file.
    
    Args:
        heatmap: The heatmap image
        floor_number: Floor number for filename
    
    Returns:
        Boolean indicating success
    """
    try:
        from pipeline_cost_map import save_cost_map as save_cost_map_file
        
        if not floor_number:
            st.error("Please enter a floor number")
            return False
        
        if heatmap is None:
            st.error("No cost map generated yet")
            return False
        
        success, result = save_cost_map_file(heatmap, floor_number)
        
        if success:
            st.success(f"✅ Cost map saved to {result}")
            return True
        else:
            st.error(f"Failed to save cost map: {result}")
            return False
        
    except Exception as e:
        st.error(f"Error saving cost map: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False


def save_cost_heuristic(cost_map_float32, metadata, floor_number):
    """
    Save the movement cost heuristic as PNG + JSON for mobile/API use.
    
    Generates two files:
    1. floor_X_cost_heuristic.png - Pre-computed movement costs
    2. floor_X_cost_heuristic.json - Metadata for decoding PNG values
    
    Args:
        cost_map_float32: Float32 cost map from process_cost_heuristic()
        metadata: Metadata dict from process_cost_heuristic()
        floor_number: Floor number for filename
    
    Returns:
        Boolean indicating success
    """
    try:
        from pipeline_cost_map import save_cost_heuristic as save_heuristic_file
        
        if not floor_number:
            st.error("Please enter a floor number")
            return False
        
        if cost_map_float32 is None or metadata is None:
            st.error("No cost heuristic generated yet")
            return False
        
        success, png_path, json_path = save_heuristic_file(cost_map_float32, metadata, floor_number)
        
        if success:
            st.success(f"✅ Movement cost heuristic saved successfully!")
            st.info(f"PNG (cost values): {png_path}")
            st.info(f"JSON (metadata): {json_path}")
            
            # Display file info
            with open(json_path, 'r') as f:
                saved_metadata = json.load(f)
            st.json(saved_metadata)
            
            return True
        else:
            st.error(f"Failed to save cost heuristic: {png_path}")
            return False
        
    except Exception as e:
        st.error(f"Error saving cost heuristic: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False

