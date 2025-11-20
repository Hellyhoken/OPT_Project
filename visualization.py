"""
Visualization Module for OPL Solutions

This module provides functions for creating interactive Folium maps
to visualize optimization solutions, including species connections,
corridors, and habitat actions.
"""

import folium


# Species color mapping for connection visualization
SPECIES_COLORS = {
    'atelerix_algirus': '#FF6B6B',
    'martes_martes': '#4ECDC4',
    'eliomys_quercinus': '#FFE66D',
    'oryctolagus_cuniculus': '#95E1D3'
}

# Species name mapping (short to full)
SPECIES_FULL_NAMES = {
    'atelerix': 'atelerix_algirus',
    'martes': 'martes_martes',
    'eliomys': 'eliomys_quercinus',
    'oryctolagus': 'oryctolagus_cuniculus'
}

# Base map configuration
MAP_CENTER = [39.97, 4.0460]
MAP_ZOOM = 11


def create_base_map():
    """
    Create a base Folium map centered on Menorca.
    
    Returns:
        folium.Map: Base map object
    """
    return folium.Map(
        location=MAP_CENTER,
        zoom_start=MAP_ZOOM,
        tiles='OpenStreetMap',
        width="90%",
        height="90%"
    )


def determine_solution_cell_color(cell, species_origins):
    """
    Determine the color for a cell in the solution map.
    
    Color scheme:
    - Orange: Corridor
    - Blue: Origin with action
    - Red: Origin without action
    - Green: Action (no origin)
    - Light gray: No action
    
    Args:
        cell (dict): Cell data dictionary
        species_origins (dict): Species origins mapping
        
    Returns:
        tuple: (color, cell_type)
    """
    is_corridor = cell['cor'] == 1
    has_origin = any(cell['is_origin'].values())
    has_action = sum(cell['add']) > 0
    
    if is_corridor:
        return '#FFA500', 'corridor'
    elif has_origin:
        if has_action:
            return '#0066FF', 'population_with_action'
        else:
            return '#FF0000', 'population_no_action'
    elif has_action:
        return '#00CC00', 'action'
    else:
        return '#E8E8E8', 'no_action'


def determine_connection_cell_color(cell, species_origins):
    """
    Determine the color for a cell in the connection map.
    
    Color scheme:
    - Orange: Corridor
    - Black: Origin cell
    - Species color: Connected to single species
    - Purple: Connected to multiple species
    - Light gray: Not connected
    
    Args:
        cell (dict): Cell data dictionary
        species_origins (dict): Species origins mapping
        
    Returns:
        str: Hex color code
    """
    is_corridor = cell['cor'] == 1
    has_origin = any(cell['is_origin'].values())
    
    if is_corridor:
        return '#FFA500'
    elif has_origin:
        return '#000000'
    
    # Check connections
    connected_species = []
    for i, species_long in enumerate(SPECIES_FULL_NAMES.values()):
        if i < len(cell['con']) and cell['con'][i] == 1:
            connected_species.append(species_long)
    
    if len(connected_species) == 0:
        return '#E8E8E8'
    elif len(connected_species) == 1:
        return SPECIES_COLORS[connected_species[0]]
    else:
        return '#9B59B6'  # Purple for multiple species


def build_solution_tooltip(cell, species_origins):
    """
    Build HTML tooltip for solution map cell.
    
    Args:
        cell (dict): Cell data dictionary
        species_origins (dict): Species origins mapping
        
    Returns:
        str: HTML string for tooltip
    """
    tooltip_lines = [
        f"Grid ID: {cell['grid_id']}",
        f"Land Cover: {cell['land_cover']}",
        "<br><b>Original Populations:</b>"
    ]
    
    for species_long in species_origins.keys():
        if cell['is_origin'].get(species_long, False):
            tooltip_lines.append(f"  • {species_long}: YES")
    
    tooltip_lines.append("<br><b>Actions:</b>")
    for i, species_long in enumerate(SPECIES_FULL_NAMES.values()):
        if i < len(cell['add']) and cell['add'][i] == 1:
            tooltip_lines.append(f"  • {species_long}: YES")
    
    is_corridor = cell['cor'] == 1
    tooltip_lines.append(f"<br><b>Corridor:</b> {'YES' if is_corridor else 'NO'}")
    tooltip_lines.append(f"<br><b>Neighbors:</b> {len(cell['neighbors'])}")
    
    return "<br>".join(tooltip_lines)


def build_connection_tooltip(cell, species_origins):
    """
    Build HTML tooltip for connection map cell.
    
    Args:
        cell (dict): Cell data dictionary
        species_origins (dict): Species origins mapping
        
    Returns:
        str: HTML string for tooltip
    """
    tooltip_lines = [
        f"Grid ID: {cell['grid_id']}",
        f"Land Cover: {cell['land_cover']}",
        "<br><b>Original Populations:</b>"
    ]
    
    for species_long in species_origins.keys():
        if cell['is_origin'].get(species_long, False):
            tooltip_lines.append(f"  • {species_long}: YES")
    
    tooltip_lines.append("<br><b>Connected to Species:</b>")
    for i, species_long in enumerate(SPECIES_FULL_NAMES.values()):
        if i < len(cell['con']) and cell['con'][i] == 1:
            # Find connected origins
            connected_origin_ids = []
            if 'con_o' in cell and i < len(cell['con_o']):
                origin_binary = cell['con_o'][i]
                species_origin_list = species_origins.get(species_long, [])
                for j, val in enumerate(origin_binary):
                    if val == 1 and j < len(species_origin_list):
                        connected_origin_ids.append(species_origin_list[j])
            
            tooltip_lines.append(f"  • {species_long}: YES")
            if connected_origin_ids:
                tooltip_lines.append(f"    Origins: {', '.join(connected_origin_ids)}")
    
    is_corridor = cell['cor'] == 1
    tooltip_lines.append(f"<br><b>Corridor:</b> {'YES' if is_corridor else 'NO'}")
    tooltip_lines.append(f"<br><b>Neighbors:</b> {len(cell['neighbors'])}")
    
    return "<br>".join(tooltip_lines)


def add_cell_to_map(map_obj, cell, color, grid_centroids, add_neighbor_arrows=True):
    """
    Add a cell polygon and optional neighbor arrows to a map.
    
    Args:
        map_obj (folium.Map): Map to add to
        cell (dict): Cell data dictionary
        color (str): Fill color for the cell
        grid_centroids (dict): Mapping of cell IDs to centroid coordinates
        add_neighbor_arrows (bool): Whether to add invisible hover arrows to neighbors
        
    Returns:
        None
    """
    grid_id = cell['grid_id']
    
    folium.GeoJson(
        cell['geometry'],
        style_function=lambda x, c=color, cn=grid_id: {
            'fillColor': c,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7,
            'className': cn
        },
        tooltip=cell.get('tooltip', f"Grid ID: {grid_id}")
    ).add_to(map_obj)
    
    if add_neighbor_arrows and grid_id in grid_centroids:
        cell_centroid = grid_centroids[grid_id]
        for neighbor_id in cell['neighbors']:
            if neighbor_id in grid_centroids:
                neighbor_centroid = grid_centroids[neighbor_id]
                arrow = folium.PolyLine(
                    locations=[cell_centroid, neighbor_centroid],
                    color='#FF00FF',
                    weight=3,
                    opacity=0,
                    popup=f"{grid_id} → {neighbor_id}",
                    className=f"arrow_{grid_id}"
                )
                arrow.add_to(map_obj)


def add_connection_arrows(map_obj, cell, grid_centroids, species_origins):
    """
    Add connection arrows from cell to its connected origins.
    
    Args:
        map_obj (folium.Map): Map to add arrows to
        cell (dict): Cell data dictionary
        grid_centroids (dict): Mapping of cell IDs to centroid coordinates
        species_origins (dict): Species origins mapping
        
    Returns:
        None
    """
    if 'con_o' not in cell:
        return
    
    grid_id = cell['grid_id']
    if grid_id not in grid_centroids:
        return
    
    cell_centroid = grid_centroids[grid_id]
    
    for i, species_long in enumerate(SPECIES_FULL_NAMES.values()):
        if i < len(cell['con']) and cell['con'][i] == 1:
            if i < len(cell['con_o']):
                origin_binary = cell['con_o'][i]
                species_origin_list = species_origins.get(species_long, [])
                for j, val in enumerate(origin_binary):
                    if val == 1 and j < len(species_origin_list):
                        origin_id = species_origin_list[j]
                        if origin_id in grid_centroids:
                            origin_centroid = grid_centroids[origin_id]
                            connection_arrow = folium.PolyLine(
                                locations=[cell_centroid, origin_centroid],
                                color=SPECIES_COLORS[species_long],
                                weight=2,
                                opacity=0.6,
                                popup=f"{grid_id} → {origin_id} ({species_long})",
                                dash_array='5, 5'
                            )
                            connection_arrow.add_to(map_obj)


def get_hover_interaction_js():
    """
    Get JavaScript code for hover interactions (neighbor arrow display).
    
    Returns:
        str: JavaScript code wrapped in <script> tags
    """
    return """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const allPaths = document.querySelectorAll('path');
    
    allPaths.forEach(path => {
        const classes = path.getAttribute('class');
        if (classes && classes.startsWith('cell_')) {
            const cellId = classes.match(/cell_(\\d+_\\d+)/);
            if (cellId) {
                const gridId = cellId[0];
                
                path.addEventListener('mouseenter', function() {
                    this.style.strokeWidth = '3';
                    this.style.stroke = '#FF00FF';
                    
                    const arrows = document.querySelectorAll(`.arrow_${gridId}`);
                    arrows.forEach(arrow => {
                        arrow.style.strokeOpacity = '0.8';
                    });
                });
                
                path.addEventListener('mouseleave', function() {
                    this.style.strokeWidth = '0.5';
                    this.style.stroke = 'black';
                    
                    const arrows = document.querySelectorAll(`.arrow_${gridId}`);
                    arrows.forEach(arrow => {
                        arrow.style.strokeOpacity = '0';
                    });
                });
            }
        }
    });
});
</script>
"""


def inject_hover_javascript(html_filepath):
    """
    Inject hover interaction JavaScript into an HTML file.
    
    Args:
        html_filepath (str): Path to HTML file
        
    Returns:
        None
    """
    with open(html_filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    custom_js = get_hover_interaction_js()
    html_content = html_content.replace('</body>', custom_js + '\n</body>')
    
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)


def compute_centroids(ordered_cells):
    """
    Compute centroids for all cells in the dataset.
    
    Args:
        ordered_cells (list): List of cell dictionaries with 'grid_id' and 'geometry'
        
    Returns:
        dict: Mapping of cell IDs to (lat, lon) tuples
    """
    grid_centroids = {}
    for cell in ordered_cells:
        centroid = cell['geometry'].centroid
        grid_centroids[cell['grid_id']] = (centroid.y, centroid.x)
    return grid_centroids
