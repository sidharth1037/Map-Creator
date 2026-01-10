"""UI view rendering functions for the Floor Plan Vectorizer."""

import streamlit as st
import os
import json
import re


def extract_floor_from_filename(filename):
    """Extract floor number from filename (e.g., 'floor_1.5_walls.json' -> '1.5')"""
    match = re.search(r'floor[_\s]+([0-9.]+)', filename, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def render_timeline():
    """Render the timeline navigation at the top."""
    STEPS = [
        ("Walls", "walls"),
        ("Stairs", "stairs"),
        ("Snap", "snap"),
        ("Visualize", "visualize"),
    ]
    
    st.markdown("---")
    
    cols = st.columns(len(STEPS))
    
    for idx, (step_name, step_key) in enumerate(STEPS):
        with cols[idx]:
            # Determine step status
            is_current = st.session_state.current_view == step_key
            is_completed = False
            
            if step_key == "walls":
                is_completed = st.session_state.walls_processed
            elif step_key == "stairs":
                is_completed = st.session_state.stairs_processed
            elif step_key == "snap":
                is_completed = st.session_state.snapped
            
            # Style button based on status
            if is_completed:
                button_color = "🟢"
            elif is_current:
                button_color = "🔵"
            else:
                button_color = "⭕"
            
            if st.button(f"{button_color} {step_name}", use_container_width=True, 
                        key=f"timeline_{step_key}"):
                st.session_state.current_view = step_key
                st.rerun()
    
    st.markdown("---")


def render_walls_view():
    """Render the walls processing view."""
    st.header("Step 1: Process Walls")
    
    st.subheader("Floor Number")
    col1, col2 = st.columns([2, 1])
    with col1:
        floor_number = st.text_input(
            "Enter floor number",
            value=st.session_state.current_floor or "1",
            help="e.g., 1, 1.5, 2.5",
            key="walls_floor_input"
        )
        # Auto-update session state as user types
        st.session_state.current_floor = floor_number
    
    st.subheader("Image Source")
    image_source = st.radio(
        "Select source:",
        ["Upload Image", "Use Existing File"],
        key="walls_source"
    )
    
    selected_image_path = None
    
    if image_source == "Upload Image":
        uploaded_file = st.file_uploader(
            "Upload floor plan image",
            type=["jpg", "jpeg", "png", "bmp", "tiff"],
            key="walls_upload"
        )
        if uploaded_file:
            temp_path = f"/tmp/floor_plan_temp.{uploaded_file.name.split('.')[-1]}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_image_path = temp_path
    else:
        image_folder = "images"
        if os.path.exists(image_folder):
            image_files = [f for f in os.listdir(image_folder) 
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))]
            if image_files:
                selected_file = st.selectbox(
                    "Select existing image:",
                    image_files,
                    key="walls_select"
                )
                selected_image_path = os.path.join(image_folder, selected_file)
            else:
                st.warning("No image files found in 'images' folder")
        else:
            st.warning("'images' folder not found")
    
    run_walls_button = st.button("Process Walls", use_container_width=True, type="primary", key="walls_btn")
    
    # Extract floor from filename if available
    floor_from_file = None
    if selected_image_path and os.path.exists(selected_image_path):
        filename = os.path.basename(selected_image_path)
        floor_from_file = extract_floor_from_filename(filename)
    
    return selected_image_path, run_walls_button, floor_from_file


def render_stairs_view():
    """Render the stairs processing view."""
    st.header("Step 2: Process Stairs")
    
    st.subheader("Floor Number")
    col1, col2 = st.columns([2, 1])
    with col1:
        floor_number = st.text_input(
            "Enter floor number",
            value=st.session_state.current_floor or "1",
            help="e.g., 1, 1.5, 2.5",
            key="stairs_floor_input"
        )
        # Auto-update session state as user types
        st.session_state.current_floor = floor_number
    
    st.subheader("Image Source")
    stairs_source = st.radio(
        "Select source:",
        ["Upload Image", "Use Existing File"],
        key="stairs_source"
    )
    
    stairs_image_path = None
    
    if stairs_source == "Upload Image":
        stairs_uploaded = st.file_uploader(
            "Upload stairs image",
            type=["jpg", "jpeg", "png", "bmp", "tiff"],
            key="stairs_upload"
        )
        if stairs_uploaded:
            temp_path = f"/tmp/stairs_temp.{stairs_uploaded.name.split('.')[-1]}"
            with open(temp_path, "wb") as f:
                f.write(stairs_uploaded.getbuffer())
            stairs_image_path = temp_path
    else:
        image_folder = "images"
        if os.path.exists(image_folder):
            image_files = [f for f in os.listdir(image_folder) 
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))]
            if image_files:
                stairs_file = st.selectbox(
                    "Select existing image:",
                    image_files,
                    key="stairs_select"
                )
                stairs_image_path = os.path.join(image_folder, stairs_file)
            else:
                st.warning("No image files found in 'images' folder")
        else:
            st.warning("'images' folder not found")
    
    run_stairs_button = st.button("Process Stairs", use_container_width=True, type="primary", key="stairs_btn")
    
    # Extract floor from filename if available
    floor_from_file = None
    if stairs_image_path and os.path.exists(stairs_image_path):
        filename = os.path.basename(stairs_image_path)
        floor_from_file = extract_floor_from_filename(filename)
    
    return stairs_image_path, run_stairs_button, floor_from_file


def render_snap_view():
    """Render the snap to walls view."""
    st.header("Step 3: Snap Stairs to Walls")
    
    st.subheader("Floor Number & JSON Files")
    
    col1, col2, col3 = st.columns([1, 1.5, 1.5])
    
    with col1:
        floor_number = st.text_input(
            "Floor number",
            value=st.session_state.current_floor or "1",
            help="e.g., 1, 1.5, 2.5",
            key="snap_floor_input"
        )
        # Auto-update session state as user types
        st.session_state.current_floor = floor_number
    
    # Get available JSON files
    json_folder = "outputs"
    walls_files = []
    stairs_files = []
    
    if os.path.exists(json_folder):
        json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
        walls_files = sorted([f for f in json_files if 'walls' in f.lower()])
        stairs_files = sorted([f for f in json_files if 'stair' in f.lower() and 'verification' not in f.lower()])
    
    # Try to auto-select files for current floor
    current_floor = st.session_state.current_floor or floor_number
    default_walls_idx = 0
    default_stairs_idx = 0
    
    for idx, f in enumerate(walls_files):
        if current_floor in f:
            default_walls_idx = idx
            break
    
    for idx, f in enumerate(stairs_files):
        if current_floor in f:
            default_stairs_idx = idx
            break
    
    with col2:
        walls_file = st.selectbox(
            "Select walls JSON",
            walls_files or ["No files found"],
            index=default_walls_idx if walls_files else 0,
            key="snap_walls_select"
        )
    
    with col3:
        stairs_file = st.selectbox(
            "Select stairs JSON",
            stairs_files or ["No files found"],
            index=default_stairs_idx if stairs_files else 0,
            key="snap_stairs_select"
        )
    
    # Check if files are valid
    walls_json_path = None
    stairs_json_path = None
    floor_from_file = None
    
    if walls_file and walls_file != "No files found":
        walls_json_path = os.path.join(json_folder, walls_file)
        floor_extracted = extract_floor_from_filename(walls_file)
        if floor_extracted:
            floor_from_file = floor_extracted
    
    if stairs_file and stairs_file != "No files found":
        stairs_json_path = os.path.join(json_folder, stairs_file)
        floor_extracted = extract_floor_from_filename(stairs_file)
        if floor_extracted:
            floor_from_file = floor_extracted
    
    st.subheader("Snap Settings")
    col1, col2 = st.columns(2)
    with col1:
        endpoint_threshold = st.slider(
            "Endpoint Snap Threshold (px)",
            min_value=10.0,
            max_value=100.0,
            value=50.0,
            step=5.0,
            help="Distance threshold for snapping to wall endpoints",
            on_change=lambda: st.session_state.update({"snapped": False})
        )
    
    with col2:
        line_threshold = st.slider(
            "Line Snap Threshold (px)",
            min_value=5.0,
            max_value=50.0,
            value=30.0,
            step=2.5,
            help="Distance threshold for snapping to wall lines",
            on_change=lambda: st.session_state.update({"snapped": False})
        )
    
    snap_button = st.button("Snap Stairs to Walls", use_container_width=True, type="primary", key="snap_btn")
    
    # Validate files before snapping
    if snap_button:
        if not walls_json_path or not os.path.exists(walls_json_path):
            st.error("Please select a valid walls JSON file")
            snap_button = False
        elif not stairs_json_path or not os.path.exists(stairs_json_path):
            st.error("Please select a valid stairs JSON file")
            snap_button = False
        else:
            st.session_state.snap_endpoint_threshold = endpoint_threshold
            st.session_state.snap_line_threshold = line_threshold
            st.session_state.snap_walls_json = walls_json_path
            st.session_state.snap_stairs_json = stairs_json_path
    
    return endpoint_threshold, line_threshold, snap_button, floor_from_file


def render_visualize_view():
    """Render the JSON visualization view."""
    st.header("Visualize JSON")
    
    st.subheader("Upload JSON Files to Visualize")
    
    uploaded_files = st.file_uploader(
        "Choose JSON files",
        type=["json"],
        accept_multiple_files=True,
        key="visualize_upload"
    )
    
    visualize_button = st.button("Visualize", use_container_width=True, type="primary", key="visualize_btn")
    
    return uploaded_files, visualize_button

