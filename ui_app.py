import streamlit as st
import re
import os

# Import UI and processing modules
from ui_views import (
    render_timeline,
    render_walls_view,
    render_stairs_view,
    render_snap_view,
    render_match_view,
    render_boundary_view,
    render_floor_connections_view,
    render_entrances_view,
    render_rooms_view,
    render_visualize_view
)
from ui_processing import (
    process_walls,
    process_stairs,
    process_snap,
    process_match,
    process_boundary_plot,
    save_boundary,
    load_boundary,
    process_floor_connections,
    save_floor_connection,
    process_entrances_plot,
    save_entrances,
    process_rooms_plot,
    save_rooms,
    process_visualize
)

# Page configuration
st.set_page_config(
    page_title="Floor Plan Vectorizer",
    layout="wide"
)

# Helper function to extract floor number from filename
def extract_floor_from_filename(filename):
    """Extract floor number from filename (e.g., 'floor_1.5_walls.json' -> '1.5')"""
    match = re.search(r'floor[_\s]+([0-9.]+)', filename, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

# Initialize session state for navigation
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'walls'  # Start with walls step
if 'current_floor' not in st.session_state:
    st.session_state.current_floor = None
if 'walls_processed' not in st.session_state:
    st.session_state.walls_processed = False
if 'stairs_processed' not in st.session_state:
    st.session_state.stairs_processed = False
if 'walls_output_path' not in st.session_state:
    st.session_state.walls_output_path = None
if 'stairs_output_path' not in st.session_state:
    st.session_state.stairs_output_path = None
if 'walls_aligned_data' not in st.session_state:
    st.session_state.walls_aligned_data = None
if 'stairs_aligned_data' not in st.session_state:
    st.session_state.stairs_aligned_data = None
if 'snapped' not in st.session_state:
    st.session_state.snapped = False
if 'floor_conn_auto_shown' not in st.session_state:
    st.session_state.floor_conn_auto_shown = False
if 'floor_conn_pending' not in st.session_state:
    st.session_state.floor_conn_pending = []
if 'floor_conn_plot_shown' not in st.session_state:
    st.session_state.floor_conn_plot_shown = False
if 'floor_conn_last_paths' not in st.session_state:
    st.session_state.floor_conn_last_paths = (None, None)
if 'ent_pending' not in st.session_state:
    st.session_state.ent_pending = []
if 'ent_plot_shown' not in st.session_state:
    st.session_state.ent_plot_shown = False
if 'ent_last_paths' not in st.session_state:
    st.session_state.ent_last_paths = (None, None)
if 'ent_points_dict' not in st.session_state:
    st.session_state.ent_points_dict = None
if 'rooms_pending' not in st.session_state:
    st.session_state.rooms_pending = []
if 'rooms_plot_shown' not in st.session_state:
    st.session_state.rooms_plot_shown = False
if 'rooms_last_path' not in st.session_state:
    st.session_state.rooms_last_path = None
if 'rooms_points_dict' not in st.session_state:
    st.session_state.rooms_points_dict = None
if 'boundary_polygons' not in st.session_state:
    st.session_state.boundary_polygons = [{"name": "Polygon 1", "points": []}]
if 'boundary_plot_updated' not in st.session_state:
    st.session_state.boundary_plot_updated = False
if 'boundary_walls_path' not in st.session_state:
    st.session_state.boundary_walls_path = None

st.title("Floor Plan Vectorizer")
# Render timeline at top
render_timeline()

# Reset floor_conn_auto_shown and plot_shown when leaving floor_connections view
if st.session_state.current_view != 'floor_connections':
    st.session_state.floor_conn_auto_shown = False
    st.session_state.floor_conn_plot_shown = False

# Reset entrances plot when leaving entrances view
if st.session_state.current_view != 'entrances':
    st.session_state.ent_plot_shown = False

# Clear any stale session state
if 'verification_img' in st.session_state:
    del st.session_state.verification_img
if 'skeleton_img' in st.session_state:
    del st.session_state.skeleton_img
if 'wall_data' in st.session_state:
    del st.session_state.wall_data
if 'aligned_data' in st.session_state:
    del st.session_state.aligned_data

# ============= VIEWS =============

# Walls View
if st.session_state.current_view == 'walls':
    selected_image_path, run_walls_button, floor_from_file = render_walls_view()
    
    if floor_from_file:
        st.session_state.current_floor = floor_from_file
    
    if run_walls_button:
        process_walls(selected_image_path)

# Stairs View
elif st.session_state.current_view == 'stairs':
    stairs_image_path, run_stairs_button, floor_from_file = render_stairs_view()
    
    if floor_from_file:
        st.session_state.current_floor = floor_from_file
    
    if run_stairs_button:
        process_stairs(stairs_image_path)

# Snap View
elif st.session_state.current_view == 'snap':
    endpoint_threshold, line_threshold, snap_button, floor_from_file = render_snap_view()
    
    if floor_from_file:
        st.session_state.current_floor = floor_from_file
    
    if snap_button and not st.session_state.snapped:
        process_snap()

# Floor Connections View
elif st.session_state.current_view == 'floor_connections':
    walls_json_path, stairs_json_path, plot_button, polygon_id, from_floor, to_floor, add_conn_button, save_button = render_floor_connections_view()
    
    # Auto-plot if we're coming sequentially from snap and have a floor number
    auto_show = st.session_state.current_floor is not None and st.session_state.snapped
    
    if auto_show and 'floor_conn_auto_shown' not in st.session_state:
        st.session_state.floor_conn_auto_shown = True
        plot_button = True
    
    walls_data = None
    stairs_data = None
    
    # Check if plot button was clicked or if we should persist the previous plot
    if plot_button:
        st.session_state.floor_conn_plot_shown = True
        st.session_state.floor_conn_last_paths = (walls_json_path, stairs_json_path)
    
    # Show plot if it was previously shown and paths are still valid
    if st.session_state.floor_conn_plot_shown:
        last_walls, last_stairs = st.session_state.floor_conn_last_paths
        if last_walls and last_stairs and os.path.exists(last_walls) and os.path.exists(last_stairs):
            walls_data, stairs_data = process_floor_connections(last_walls, last_stairs)
        else:
            st.session_state.floor_conn_plot_shown = False
    
    # Handle add connection button
    if add_conn_button:
        new_conn = {
            'polygon_id': int(polygon_id),
            'from_floor': from_floor,
            'to_floor': to_floor
        }
        st.session_state.floor_conn_pending.append(new_conn)
        st.rerun()
    
    # Handle save button - save all pending connections
    if save_button and st.session_state.floor_conn_pending:
        if stairs_json_path:
            if save_floor_connection(stairs_json_path, st.session_state.floor_conn_pending):
                # Show what was saved
                st.info("✨ Ready to add more connections or navigate to another step")
                # Mark as saved but keep pending list for reference
                st.session_state.last_saved_connections = st.session_state.floor_conn_pending.copy()
                st.session_state.floor_conn_pending = []
        else:
            st.error("Please select a stairs JSON file first")

# Entrances View
elif st.session_state.current_view == 'entrances':
    walls_json_path, stairs_json_path, plot_button, point1_id, point2_id, ent_name, room_no, is_stairs, add_entrance_button, save_button = render_entrances_view()
    
    # Store points_dict in session state when plot is generated
    if 'ent_points_dict' not in st.session_state:
        st.session_state.ent_points_dict = None
    
    # Check if plot button was clicked or if we should persist the previous plot
    if plot_button:
        st.session_state.ent_plot_shown = True
        st.session_state.ent_last_paths = (walls_json_path, stairs_json_path)
    
    # Show plot if it was previously shown and paths are still valid
    if st.session_state.ent_plot_shown:
        last_walls, last_stairs = st.session_state.ent_last_paths
        if last_walls and os.path.exists(last_walls):
            walls_data, points_dict = process_entrances_plot(last_walls, last_stairs)
            if walls_data and points_dict:
                st.session_state.ent_points_dict = points_dict
    
    # Handle add entrance button
    if add_entrance_button:
        new_entrance = {
            'point1_id': int(point1_id),
            'point2_id': int(point2_id),
            'name': ent_name,
            'room_no': room_no,
            'stairs': is_stairs
        }
        st.session_state.ent_pending.append(new_entrance)
        st.rerun()
    
    # Handle save button - save all pending entrances
    if save_button and st.session_state.ent_pending:
        floor_number = st.session_state.get("current_floor")
        points_dict = st.session_state.ent_points_dict
        if floor_number and points_dict:
            if save_entrances(floor_number, st.session_state.ent_pending, points_dict):
                st.info("✨ Ready to add more entrances or navigate to another step")
                st.session_state.ent_pending = []
        else:
            st.error("Please enter a floor number and plot the map first")

# Rooms View
elif st.session_state.current_view == 'rooms':
    walls_json_path, plot_button, point1_id, point2_id, point3_id, point4_id, room_full_name, add_room_button, save_button = render_rooms_view()
    
    # Check if plot button was clicked or if we should persist the previous plot
    if plot_button:
        st.session_state.rooms_plot_shown = True
        st.session_state.rooms_last_path = walls_json_path
    
    # Show plot if it was previously shown and path is still valid
    if st.session_state.rooms_plot_shown:
        last_walls = st.session_state.rooms_last_path
        if last_walls and os.path.exists(last_walls):
            walls_data, points_dict = process_rooms_plot(last_walls)
            if walls_data and points_dict:
                st.session_state.rooms_points_dict = points_dict
        else:
            st.session_state.rooms_plot_shown = False
    
    # Handle add room button
    if add_room_button:
        if point1_id and point2_id and point3_id and point4_id and room_full_name:
            try:
                new_room = {
                    'point1_id': int(point1_id),
                    'point2_id': int(point2_id),
                    'point3_id': int(point3_id),
                    'point4_id': int(point4_id),
                    'name': room_full_name
                }
                st.session_state.rooms_pending.append(new_room)
                st.rerun()
            except ValueError:
                st.error("Point IDs must be integers")
        else:
            st.error("Please fill all fields: 4 point IDs and room name")
    
    # Handle save button - save all pending rooms
    if save_button and st.session_state.rooms_pending:
        floor_number = st.session_state.get("current_floor")
        points_dict = st.session_state.rooms_points_dict
        if floor_number and points_dict:
            if save_rooms(floor_number, st.session_state.rooms_pending, points_dict):
                st.info("✨ Ready to add more rooms or navigate to another step")
                st.session_state.rooms_pending = []
        else:
            st.error("Please enter a floor number and plot the map first")

# Match View
elif st.session_state.current_view == 'match':
    reference_json_path, target_json_path, threshold, match_button = render_match_view()
    
    if match_button:
        process_match(reference_json_path, target_json_path, threshold)

# Boundary View
elif st.session_state.current_view == 'boundary':
    plot_placeholder, walls_json_path, stairs_json_path, plot_button, boundary_json_path, load_boundary_button, point_id_input, add_point_button, plot_verification_button, floor_number, save_button = render_boundary_view()
    
    # Initialize session state variables
    if 'boundary_points_dict' not in st.session_state:
        st.session_state.boundary_points_dict = {}
    if 'boundary_plot_fig' not in st.session_state:
        st.session_state.boundary_plot_fig = None
    
    # Handle load existing boundary button
    if load_boundary_button:
        boundary_polygons, loaded_floor, walls_path = load_boundary(boundary_json_path)
        if boundary_polygons:
            st.session_state.boundary_polygons = boundary_polygons
            st.session_state.current_floor = loaded_floor
            st.session_state.boundary_walls_path = walls_path
            st.session_state.boundary_stairs_path = stairs_json_path
            if walls_path:
                fig, points_dict = process_boundary_plot(walls_path, [], stairs_json_path=stairs_json_path)
                if fig and points_dict:
                    st.session_state.boundary_points_dict = points_dict
                    st.session_state.boundary_plot_fig = fig
            st.rerun()
    
    # Update walls path if plot button clicked
    if plot_button or st.session_state.boundary_walls_path is None:
        st.session_state.boundary_walls_path = walls_json_path
        st.session_state.boundary_stairs_path = stairs_json_path
    
    # Update plot when plot or verification button clicked
    if (plot_button or plot_verification_button) and st.session_state.boundary_walls_path:
        fig, points_dict = process_boundary_plot(st.session_state.boundary_walls_path, st.session_state.boundary_polygons, stairs_json_path=st.session_state.get('boundary_stairs_path'))
        if fig and points_dict:
            st.session_state.boundary_points_dict = points_dict
            st.session_state.boundary_plot_fig = fig
    
    # Display plot (persists from session state)
    if st.session_state.boundary_plot_fig:
        with plot_placeholder.container():
            st.plotly_chart(st.session_state.boundary_plot_fig, width='stretch')
    
    # Get current polygon index and points
    current_poly_idx = st.session_state.get('boundary_poly_select', 0)
    if current_poly_idx < len(st.session_state.boundary_polygons):
        current_polygon = st.session_state.boundary_polygons[current_poly_idx]
    
    # Handle add point button (no rerun, just add to list)
    if add_point_button:
        point_number = point_id_input.strip()  # Get input number
        
        # Convert number to point ID (0 -> P0, 1 -> P1, etc.)
        point_id = f"P{point_number}"
        
        # Find matching point from available points
        found_point = None
        for pid, (x, y) in st.session_state.boundary_points_dict.items():
            if pid == point_id:
                found_point = (x, y)
                break
        
        if found_point:
            new_point = {
                'id': len(current_polygon['points']),
                'x': found_point[0],
                'y': found_point[1],
                'source_point_id': point_number
            }
            current_polygon['points'].append(new_point)
            st.success(f"Point {point_number} added to {current_polygon['name']}. Click 'Plot Verification' to update.")
        else:
            available_points = ', '.join(sorted(st.session_state.boundary_points_dict.keys()))
            st.error(f"Point {point_number} not found. Available: {available_points}")
    
    # Handle save button
    if save_button:
        if save_boundary(floor_number, st.session_state.boundary_polygons):
            st.session_state.boundary_polygons = [{"name": "Polygon 1", "points": []}]
            st.rerun()

# Visualize View
elif st.session_state.current_view == 'visualize':
    uploaded_files, visualize_button = render_visualize_view()
    
    if visualize_button and uploaded_files:
        process_visualize(uploaded_files)
