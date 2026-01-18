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
        ("Floor Data", "floor_connections"),
        ("Entrances", "entrances"),
        ("Rooms", "rooms"),
        ("Match", "match"),
        ("Boundary", "boundary"),
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
            
            if st.button(f"{button_color} {step_name}", width='stretch', 
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
    
    run_walls_button = st.button("Process Walls", width='stretch', type="primary", key="walls_btn")
    
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
    
    run_stairs_button = st.button("Process Stairs", width='stretch', type="primary", key="stairs_btn")
    
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
    
    snap_button = st.button("Snap Stairs to Walls", width='stretch', type="primary", key="snap_btn")
    
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


def render_floor_connections_view():
    """Render the floor connections view."""
    st.header("Floor Connections")
    
    floor_number = st.text_input(
        "Enter floor number",
        value=st.session_state.get("current_floor", ""),
        on_change=lambda: st.session_state.update({"current_floor": st.session_state.floor_input}),
        key="floor_input"
    )
    
    st.subheader("Select JSON Files")
    
    # Option to use automatic detection or custom files
    use_automatic = st.checkbox(
        "Use automatic floor detection",
        value=True,
        key="floor_conn_use_automatic"
    )
    
    walls_json_path = None
    stairs_json_path = None
    
    if use_automatic and floor_number:
        try:
            floor = float(floor_number)
            walls_json_path = f"outputs/floor_{floor}_walls.json"
            stairs_json_path = f"outputs/floor_{floor}_stairs.json"
        except ValueError:
            st.error("Invalid floor number")
    else:
        # Custom file selection
        st.write("Select walls JSON:")
        walls_file = st.selectbox(
            "Walls JSON",
            options=_get_json_files("outputs", "walls"),
            key="floor_conn_walls_select"
        )
        if walls_file:
            walls_json_path = f"outputs/{walls_file}"
        
        st.write("Select stairs JSON:")
        stairs_file = st.selectbox(
            "Stairs JSON",
            options=_get_json_files("outputs", "stairs"),
            key="floor_conn_stairs_select"
        )
        if stairs_file:
            stairs_json_path = f"outputs/{stairs_file}"
    
    plot_button = st.button("Plot", width='stretch', type="secondary", key="floor_conn_plot_btn")
    
    st.divider()
    st.subheader("Add Floor Connections")
    
    # Initialize pending connections list in session state
    if 'floor_conn_pending' not in st.session_state:
        st.session_state.floor_conn_pending = []
    
    # Form to add new connection
    col1, col2, col3 = st.columns(3)
    with col1:
        polygon_id = st.number_input(
            "Polygon ID",
            min_value=0,
            step=1,
            key="floor_conn_polygon_id"
        )
    
    with col2:
        from_floor = st.number_input(
            "From floor",
            format="%.1f",
            key="floor_conn_from"
        )
    
    with col3:
        to_floor = st.number_input(
            "To floor",
            format="%.1f",
            key="floor_conn_to"
        )
    
    add_conn_button = st.button("Add Connection", width='stretch', type="secondary", key="add_floor_conn_btn")
    
    # Display pending connections
    if st.session_state.floor_conn_pending:
        st.subheader("Pending Connections")
        st.write(f"Total: {len(st.session_state.floor_conn_pending)} connections to add")
        
        for idx, conn in enumerate(st.session_state.floor_conn_pending):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"P{conn['polygon_id']}: {conn['from_floor']} ↔ {conn['to_floor']}")
            with col2:
                if st.button("Remove", key=f"remove_conn_{idx}", width='content'):
                    st.session_state.floor_conn_pending.pop(idx)
                    st.rerun()
    
    save_button = st.button("Save All Connections", width='stretch', type="primary", key="save_floor_conn_btn")
    
    return walls_json_path, stairs_json_path, plot_button, polygon_id, from_floor, to_floor, add_conn_button, save_button


def render_entrances_view():
    """Render the entrances creation view."""
    st.header("Create Entrances")
    
    floor_number = st.text_input(
        "Enter floor number",
        value=st.session_state.get("current_floor", ""),
        on_change=lambda: st.session_state.update({"current_floor": st.session_state.ent_floor_input}),
        key="ent_floor_input"
    )
    
    st.subheader("Select Data Files")
    
    # Option to use automatic detection or custom files
    use_automatic = st.checkbox(
        "Use automatic floor detection",
        value=True,
        key="ent_use_automatic"
    )
    
    walls_json_path = None
    stairs_json_path = None
    
    if use_automatic and floor_number:
        try:
            floor = float(floor_number)
            walls_json_path = f"outputs/floor_{floor}_walls.json"
            stairs_json_path = f"outputs/floor_{floor}_stairs.json"
        except ValueError:
            st.error("Invalid floor number")
    else:
        # Custom file selection
        st.write("Select walls JSON:")
        walls_file = st.selectbox(
            "Walls JSON",
            options=_get_json_files("outputs", "walls"),
            key="ent_walls_select"
        )
        if walls_file:
            walls_json_path = f"outputs/{walls_file}"
        
        st.write("Select stairs JSON (optional):")
        stairs_file = st.selectbox(
            "Stairs JSON",
            options=["-None-"] + _get_json_files("outputs", "stairs"),
            key="ent_stairs_select"
        )
        if stairs_file and stairs_file != "-None-":
            stairs_json_path = f"outputs/{stairs_file}"
    
    plot_button = st.button("Plot Points", width='stretch', type="secondary", key="ent_plot_btn")
    
    st.divider()
    st.subheader("Add Entrance Pairs")
    
    # Initialize pending entrances list in session state
    if 'ent_pending' not in st.session_state:
        st.session_state.ent_pending = []
    
    col1, col2 = st.columns(2)
    with col1:
        point1_id = st.number_input(
            "Point 1 ID",
            min_value=0,
            step=1,
            key="ent_point1_id"
        )
    
    with col2:
        point2_id = st.number_input(
            "Point 2 ID",
            min_value=0,
            step=1,
            key="ent_point2_id"
        )
    
    st.write("Optional Entrance Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        ent_name = st.text_input("Name", key="ent_name")
    
    with col2:
        room_no = st.text_input("Room No.", key="ent_room_no")
    
    with col3:
        is_stairs = st.checkbox("Stairs", key="ent_is_stairs")
    
    add_entrance_button = st.button("Add Entrance Pair", width='stretch', type="secondary", key="add_ent_btn")
    
    # Display pending entrances
    if st.session_state.ent_pending:
        st.subheader("Pending Entrances")
        st.write(f"Total: {len(st.session_state.ent_pending)} pairs")
        
        for idx, ent in enumerate(st.session_state.ent_pending):
            col1, col2 = st.columns([4, 1])
            with col1:
                stairs_badge = " 🪜" if ent.get('stairs') else ""
                st.write(f"P{ent['point1_id']}-P{ent['point2_id']}: {ent.get('name', '(no name)')} | Room: {ent.get('room_no', 'N/A')}{stairs_badge}")
            with col2:
                if st.button("Remove", key=f"remove_ent_{idx}", width='content'):
                    st.session_state.ent_pending.pop(idx)
                    st.rerun()
    
    save_button = st.button("Save All Entrances", width='stretch', type="primary", key="save_ent_btn")
    
    return walls_json_path, stairs_json_path, plot_button, point1_id, point2_id, ent_name, room_no, is_stairs, add_entrance_button, save_button
def _get_json_files(directory, filter_type=None):
    """Get list of JSON files in directory with optional filtering."""
    if not os.path.exists(directory):
        return []
    
    files = []
    for f in os.listdir(directory):
        if f.endswith('.json'):
            if filter_type is None or filter_type in f:
                files.append(f)
    
    return sorted(files)


def render_visualize_view():
    """Render the JSON visualization view."""
    st.header("Visualize JSON")
    
    st.subheader("Upload JSON Files to Visualize")
    
    uploaded_files = st.file_uploader(
        "Select one or more JSON files",
        type=["json"],
        accept_multiple_files=True
    )
    
    visualize_button = st.button("Visualize", key="visualize_button")
    
    return uploaded_files, visualize_button


def render_rooms_view():
    """Render the rooms creation view."""
    st.header("Create Rooms")
    
    st.subheader("Load Floor Plan")
    
    # Auto-detect from filename
    floor_from_file = None
    if st.session_state.current_floor is not None:
        st.info(f"📍 Floor: {st.session_state.current_floor}")
        floor_from_file = st.session_state.current_floor
    
    # Allow custom floor input
    with st.expander("Change floor number"):
        custom_floor = st.text_input("Floor number", value=st.session_state.current_floor or "")
        if custom_floor:
            floor_from_file = custom_floor
    
    # Get walls JSON files
    json_dir = "outputs"
    json_files = _get_json_files(json_dir, filter_type="walls")
    
    # Auto-select walls file based on floor
    selected_walls_file = None
    if floor_from_file:
        matching_files = [f for f in json_files if f"floor_{floor_from_file}_walls" in f]
        if matching_files:
            selected_walls_file = matching_files[0]
    
    # Manual file selection fallback
    if not selected_walls_file:
        st.subheader("Manually select walls JSON")
        selected_walls_file = st.selectbox(
            "Select walls JSON file",
            json_files,
            key="rooms_walls_select"
        )
    else:
        st.success(f"✓ Using: {selected_walls_file}")
        if st.checkbox("Change walls file", key="rooms_change_walls"):
            selected_walls_file = st.selectbox(
                "Select walls JSON file",
                json_files,
                key="rooms_walls_select_manual"
            )
    
    walls_json_path = f"{json_dir}/{selected_walls_file}" if selected_walls_file else None
    
    # Plot button
    plot_button = st.button("Plot Walls", key="rooms_plot_button")
    
    st.markdown("---")
    st.subheader("Define Rooms")
    
    # 4-point selection
    st.write("Select 4 points to form a quadrilateral room:")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        point1_id = st.text_input("Point 1 ID", placeholder="e.g., 0", key="rooms_p1")
    with col2:
        point2_id = st.text_input("Point 2 ID", placeholder="e.g., 1", key="rooms_p2")
    with col3:
        point3_id = st.text_input("Point 3 ID", placeholder="e.g., 2", key="rooms_p3")
    with col4:
        point4_id = st.text_input("Point 4 ID", placeholder="e.g., 3", key="rooms_p4")
    
    # Room name and number
    room_full_name = st.text_input(
        "Room name (e.g., '114: Gents Toilet' or just 'Lift')",
        placeholder="Format: number: name (optional)",
        key="rooms_name"
    )
    
    add_room_button = st.button("Add Room", key="rooms_add_button")
    
    st.markdown("---")
    st.subheader("Pending Rooms")
    
    # Display pending rooms
    if st.session_state.rooms_pending:
        st.info(f"Total rooms to add: {len(st.session_state.rooms_pending)}")
        
        for idx, room in enumerate(st.session_state.rooms_pending):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{room.get('name', 'Unnamed')}**")
            with col2:
                point_ids = [room['point1_id'], room['point2_id'], room['point3_id'], room['point4_id']]
                st.write(f"Points: {point_ids}")
            with col3:
                if st.button("✕", key=f"rooms_remove_{idx}"):
                    st.session_state.rooms_pending.pop(idx)
                    st.rerun()
    
    # Save button
    save_button = st.button("Save Rooms to JSON", key="rooms_save_button")
    
    return walls_json_path, plot_button, point1_id, point2_id, point3_id, point4_id, room_full_name, add_room_button, save_button


def render_match_view():
    """Render the floor matching view."""
    st.header("Match Floors")
    
    st.write("Keep one floor as reference and snap another floor's coordinates to match boundaries. Supports walls and stairs files.")
    
    st.markdown("---")
    st.subheader("Select Reference Floor (Fixed)")
    
    json_dir = "outputs"
    json_files = _get_json_files(json_dir)
    
    # Filter for walls and stairs only
    ref_files = [f for f in json_files if '_walls' in f or '_stairs' in f]
    
    reference_file = st.selectbox(
        "Reference file (won't be modified)",
        ref_files,
        key="match_reference_select"
    )
    
    reference_json_path = f"{json_dir}/{reference_file}" if reference_file else None
    
    st.markdown("---")
    st.subheader("Select Target Floor (Will be Modified)")
    
    # Filter out the reference file from target options
    target_files = [f for f in ref_files if f != reference_file]
    
    target_file = st.selectbox(
        "Target file (coordinates will be snapped to reference)",
        target_files,
        key="match_target_select"
    )
    
    target_json_path = f"{json_dir}/{target_file}" if target_file else None
    
    st.markdown("---")
    st.subheader("Snapping Settings")
    
    threshold = st.slider(
        "Snapping Threshold (pixels)",
        min_value=5,
        max_value=200,
        value=50,
        step=5,
        help="Maximum distance to snap coordinates to reference points"
    )
    
    st.markdown("---")
    
    match_button = st.button("Match & Snap Coordinates", key="match_button")
    
    return reference_json_path, target_json_path, threshold, match_button


def render_boundary_view():
    """Render the floor boundary definition view."""
    st.header("Define Floor Boundary")
    
    st.write("Click points on the plot or enter their IDs. Points will be connected in order with a boundary line.")
    
    st.markdown("---")
    
    # Left and right columns
    col_plot, col_controls = st.columns([2, 1])
    
    with col_plot:
        st.subheader("Floor Plan - Click points or select from list")
        plot_placeholder = st.empty()
    
    with col_controls:
        st.subheader("Controls")
        
        # Option to load existing boundary or create new
        load_option = st.radio("Choose:", ["Create New Boundary", "Load Existing Boundary"], key="boundary_load_option")
        
        st.markdown("---")
        
        if load_option == "Load Existing Boundary":
            st.write("**Load Boundary File:**")
            json_dir = "outputs"
            json_files = _get_json_files(json_dir, filter_type="_boundary")
            
            boundary_file = st.selectbox(
                "Select boundary file",
                json_files,
                key="boundary_file_select"
            )
            
            boundary_json_path = f"{json_dir}/{boundary_file}" if boundary_file else None
            
            st.write("**Optional - Include Stairs:**")
            stairs_files = _get_json_files(json_dir, filter_type="_stairs")
            stairs_files = ["None"] + stairs_files
            
            stairs_file = st.selectbox(
                "Select stairs file (optional)",
                stairs_files,
                key="boundary_stairs_select_load"
            )
            
            stairs_json_path = f"{json_dir}/{stairs_file}" if stairs_file and stairs_file != "None" else None
            
            load_boundary_button = st.button("Load Boundary", key="boundary_load_button")
            
            plot_button = None
            walls_json_path = None
        else:
            st.write("**Create New Boundary:**")
            # Floor selection
            json_dir = "outputs"
            json_files = _get_json_files(json_dir, filter_type="_walls")
            
            walls_file = st.selectbox(
                "Select walls file",
                json_files,
                key="boundary_walls_select"
            )
            
            walls_json_path = f"{json_dir}/{walls_file}" if walls_file else None
            
            # Stairs file selection (optional)
            st.write("**Optional - Include Stairs:**")
            stairs_files = _get_json_files(json_dir, filter_type="_stairs")
            stairs_files = ["None"] + stairs_files
            
            stairs_file = st.selectbox(
                "Select stairs file (optional)",
                stairs_files,
                key="boundary_stairs_select"
            )
            
            stairs_json_path = f"{json_dir}/{stairs_file}" if stairs_file and stairs_file != "None" else None
            
            plot_button = st.button("Plot Walls & Points", key="boundary_plot_button")
            boundary_json_path = None
            load_boundary_button = None
        
        st.markdown("---")
        st.write("**Polygon Management:**")
        
        # Polygon selector and controls
        col_poly1, col_poly2, col_poly3 = st.columns([2, 1, 1])
        
        with col_poly1:
            polygon_names = [p['name'] for p in st.session_state.boundary_polygons]
            current_poly_idx = st.selectbox(
                "Select polygon",
                range(len(polygon_names)) if polygon_names else [0],
                format_func=lambda i: polygon_names[i] if i < len(polygon_names) else "Default",
                key="boundary_poly_select"
            )
        
        with col_poly2:
            if st.button("➕ New Polygon", key="boundary_new_poly"):
                new_poly = {
                    "name": f"Polygon {len(st.session_state.boundary_polygons) + 1}",
                    "points": []
                }
                st.session_state.boundary_polygons.append(new_poly)
                st.rerun()
        
        with col_poly3:
            if len(st.session_state.boundary_polygons) > 1:
                if st.button("🗑️ Delete Polygon", key="boundary_delete_poly"):
                    st.session_state.boundary_polygons.pop(current_poly_idx)
                    st.rerun()
        
        st.markdown("---")
        st.write("**Add Boundary Points:**")
        
        # Point ID input
        point_id_input = st.text_input(
            "Enter point number",
            placeholder="e.g., 0, 1, 2",
            key="boundary_point_id"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            add_point_button = st.button("Add Point", key="boundary_add_point")
        with col_btn2:
            plot_verification_button = st.button("Plot Verification", key="boundary_plot_verify")
        
        st.markdown("---")
        
        # Display current polygon points
        if current_poly_idx < len(st.session_state.boundary_polygons):
            current_polygon = st.session_state.boundary_polygons[current_poly_idx]
            if current_polygon['points']:
                st.write(f"**{current_polygon['name']}: {len(current_polygon['points'])} points**")
                
                for idx, point in enumerate(current_polygon['points']):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.write(f"**B{idx}**")
                    with col2:
                        st.write(f"({point['x']}, {point['y']})")
                    with col3:
                        if st.button("✕", key=f"boundary_remove_{idx}"):
                            current_polygon['points'].pop(idx)
                            st.rerun()
            else:
                st.info(f"No points in {current_polygon['name']} yet")
        
        st.markdown("---")
        
        # Floor number input
        floor_number = st.text_input("Floor number", value="", key="boundary_floor", placeholder="e.g., 1 or 1.5")
        
        # Save button
        save_button = st.button("Save Boundary", key="boundary_save_button", type="primary")
    
    return plot_placeholder, walls_json_path, stairs_json_path, plot_button, boundary_json_path, load_boundary_button, point_id_input, add_point_button, plot_verification_button, floor_number, save_button
