import streamlit as st
import re
import os

# Import UI and processing modules
from ui_views import (
    render_timeline,
    render_walls_view,
    render_stairs_view,
    render_snap_view,
    render_visualize_view
)
from ui_processing import (
    process_walls,
    process_stairs,
    process_snap,
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

st.title("Floor Plan Vectorizer")

# Render timeline at top
render_timeline()

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

# Visualize View
elif st.session_state.current_view == 'visualize':
        uploaded_files, visualize_button = render_visualize_view()
        
        if visualize_button and uploaded_files:
            process_visualize(uploaded_files)
