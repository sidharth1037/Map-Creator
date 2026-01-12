"""
Floor matching and coordinate snapping pipeline.
Snaps coordinates in a target file to nearby points in a reference file
while preserving line orientations and connectivity.
"""

import json
import math
from collections import defaultdict


def load_json(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(data, filepath):
    """Save JSON data to file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def extract_unique_points(segments):
    """
    Extract all unique points from segments.
    
    Returns:
        Dict: {point_id: (x, y)} where point_id is "x,y" string
    """
    points = {}
    for seg in segments:
        if isinstance(seg, dict) and 'x1' in seg and 'y1' in seg:
            p1_key = f"{seg['x1']},{seg['y1']}"
            if p1_key not in points:
                points[p1_key] = (seg['x1'], seg['y1'])
            
            x2 = seg.get('x2', seg['x1'])
            y2 = seg.get('y2', seg['y1'])
            p2_key = f"{x2},{y2}"
            if p2_key not in points:
                points[p2_key] = (x2, y2)
    
    return points


def build_point_to_segments_map(segments):
    """
    Map each point to segments that use it.
    
    Returns:
        Dict: {(x, y): [segment_indices]}
    """
    point_map = defaultdict(list)
    for idx, seg in enumerate(segments):
        if isinstance(seg, dict) and 'x1' in seg and 'y1' in seg:
            p1 = (seg['x1'], seg['y1'])
            p2 = (seg.get('x2', seg['x1']), seg.get('y2', seg['y1']))
            
            point_map[p1].append((idx, 'p1'))
            if p1 != p2:
                point_map[p2].append((idx, 'p2'))
    
    return point_map


def is_vertical_line(x1, y1, x2, y2, tolerance=1.0):
    """Check if line is approximately vertical."""
    return abs(x2 - x1) <= tolerance


def is_horizontal_line(x1, y1, x2, y2, tolerance=1.0):
    """Check if line is approximately horizontal."""
    return abs(y2 - y1) <= tolerance


def find_snap_point(target_point, reference_points, threshold, target_segments, segment_idx, point_type):
    """
    Find best snap point for a target point.
    Snaps to the closest reference point within threshold, while preferring axis-aligned matches.
    
    Args:
        target_point: (x, y) to snap
        reference_points: [(x, y), ...] available reference points
        threshold: Maximum snapping distance
        target_segments: All segments in target file
        segment_idx: Index of segment containing target_point
        point_type: 'p1' or 'p2' indicating which endpoint
    
    Returns:
        Best (x, y) to snap to, or None if no good match within threshold
    """
    target_x, target_y = target_point
    segment = target_segments[segment_idx]
    
    # Get the other endpoint of this segment to determine line orientation
    if point_type == 'p1':
        other_x = segment.get('x2', segment['x1'])
        other_y = segment.get('y2', segment['y1'])
    else:
        other_x = segment['x1']
        other_y = segment['y1']
    
    # Check line orientation of current segment
    is_vert = is_vertical_line(target_x, target_y, other_x, other_y)
    is_horiz = is_horizontal_line(target_x, target_y, other_x, other_y)
    
    best_point = None
    best_distance = threshold
    best_is_aligned = False
    
    for ref_point in reference_points:
        ref_x, ref_y = ref_point
        
        # Calculate distance
        dx = ref_x - target_x
        dy = ref_y - target_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > threshold:
            continue
        
        # Check if snap would maintain line orientation
        snap_is_vert = is_vertical_line(target_x, target_y, ref_x, ref_y)
        snap_is_horiz = is_horizontal_line(target_x, target_y, ref_x, ref_y)
        snap_is_aligned = snap_is_vert or snap_is_horiz
        current_is_aligned = is_vert or is_horiz
        
        # Prefer axis-aligned snaps, but accept any within threshold
        if current_is_aligned:
            # Current line is axis-aligned
            if snap_is_aligned:
                # Snap maintains alignment - best preference
                if distance < best_distance:
                    best_distance = distance
                    best_point = ref_point
                    best_is_aligned = True
            else:
                # Snap breaks alignment - only use if nothing else found
                if not best_is_aligned and distance < best_distance:
                    best_distance = distance
                    best_point = ref_point
        else:
            # Current line is not axis-aligned
            # Accept any snap within threshold, prefer axis-aligned targets
            if snap_is_aligned:
                if distance < best_distance:
                    best_distance = distance
                    best_point = ref_point
                    best_is_aligned = True
            else:
                if not best_is_aligned and distance < best_distance:
                    best_distance = distance
                    best_point = ref_point
    
    return best_point


def match_coordinates(reference_segments, target_segments, threshold=50.0):
    """
    Snap coordinates in target to nearby points in reference while preserving geometry.
    Groups points that share X or Y coordinates (building walls on same line) and snaps them together.
    
    Args:
        reference_segments: List of reference segment dicts
        target_segments: List of target segment dicts (will be modified)
        threshold: Maximum snapping distance
    
    Returns:
        Tuple: (modified_target_segments, snap_stats)
    """
    # Extract reference points
    reference_points = list(extract_unique_points(reference_segments).values())
    
    # Extract target points with their positions
    target_points = extract_unique_points(target_segments)
    
    # Group target points by X coordinate (vertical lines)
    x_groups = defaultdict(list)  # x -> [y values]
    # Group target points by Y coordinate (horizontal lines)
    y_groups = defaultdict(list)  # y -> [x values]
    
    for point in target_points.values():
        x, y = point
        x_groups[x].append(y)
        y_groups[y].append(x)
    
    # For each group, find the best snap value
    x_snap_mapping = {}  # old_x -> new_x
    y_snap_mapping = {}  # old_y -> new_y
    
    # Process vertical lines (groups sharing same X)
    for target_x in x_groups:
        y_values = x_groups[target_x]
        
        # Find best X snap by checking reference points
        best_snap_x = None
        best_distance = threshold
        
        for ref_point in reference_points:
            ref_x, _ = ref_point
            distance = abs(ref_x - target_x)
            
            if distance < best_distance:
                best_distance = distance
                best_snap_x = ref_x
        
        if best_snap_x is not None:
            x_snap_mapping[target_x] = best_snap_x
    
    # Process horizontal lines (groups sharing same Y)
    for target_y in y_groups:
        x_values = y_groups[target_y]
        
        # Find best Y snap by checking reference points
        best_snap_y = None
        best_distance = threshold
        
        for ref_point in reference_points:
            _, ref_y = ref_point
            distance = abs(ref_y - target_y)
            
            if distance < best_distance:
                best_distance = distance
                best_snap_y = ref_y
        
        if best_snap_y is not None:
            y_snap_mapping[target_y] = best_snap_y
    
    # Apply snaps to all segments
    modified_segments = []
    for seg in target_segments:
        if not isinstance(seg, dict):
            modified_segments.append(seg)
            continue
        
        new_seg = seg.copy()
        
        # Snap p1
        if 'x1' in seg and 'y1' in seg:
            old_x1 = seg['x1']
            old_y1 = seg['y1']
            new_x1 = x_snap_mapping.get(old_x1, old_x1)
            new_y1 = y_snap_mapping.get(old_y1, old_y1)
            new_seg['x1'] = new_x1
            new_seg['y1'] = new_y1
        
        # Snap p2
        if 'x2' in seg and 'y2' in seg:
            old_x2 = seg['x2']
            old_y2 = seg['y2']
            new_x2 = x_snap_mapping.get(old_x2, old_x2)
            new_y2 = y_snap_mapping.get(old_y2, old_y2)
            new_seg['x2'] = new_x2
            new_seg['y2'] = new_y2
        
        modified_segments.append(new_seg)
    
    # Calculate stats
    snapped_x = len(x_snap_mapping)
    snapped_y = len(y_snap_mapping)
    total_lines = len(x_groups) + len(y_groups)
    
    stats = {
        'total_reference_points': len(reference_points),
        'total_target_points': len(target_points),
        'vertical_lines_snapped': snapped_x,
        'horizontal_lines_snapped': snapped_y,
        'total_lines': total_lines,
        'snap_percentage': ((snapped_x + snapped_y) / total_lines * 100) if total_lines else 0
    }
    
    return modified_segments, stats
