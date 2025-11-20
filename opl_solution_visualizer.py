"""
OPL Solution Visualizer

Interactive visualization tool for optimization solutions showing:
- Solution map: Actions, corridors, and population origins
- Connection map: Species connections and corridors with origin arrows

This script loads OPL data and solution files, then generates interactive
HTML maps with hover interactions.
"""

import os
import geopandas as gpd

from opl_parser import (
    parse_opl_set, parse_opl_1d_array, parse_opl_2d_array, 
    parse_opl_3d_array, parse_opl_array_of_sets, load_opl_file
)
from visualization import (
    create_base_map, determine_solution_cell_color, 
    determine_connection_cell_color, build_solution_tooltip,
    build_connection_tooltip, add_cell_to_map, add_connection_arrows,
    inject_hover_javascript, compute_centroids, SPECIES_FULL_NAMES
)
from file_utils import (
    list_and_select_file, ensure_directory_exists,
    get_species_origins_from_dataset, print_summary_statistics
)


def load_menorca_dataset():
    """Load the Menorca dataset for geometries and land cover."""
    print("Loading Menorca dataset for geometry only...")
    dataset_gpd = gpd.read_file(
        "https://gitlab.com/drvicsana/opt-milp-project-2025/-/raw/main/datasets/dataset.geojson"
    )
    print("Dataset loaded.")
    return dataset_gpd


def load_and_parse_opl_data(opl_data_dir):
    """
    Load and parse OPL data file selected by user.
    
    Returns:
        tuple: (cells, species_list, neighbors_list, opl_data_filename)
    """
    selected_file = list_and_select_file(
        opl_data_dir, 
        extension='.dat',
        prompt_message="Available OPL data files"
    )
    
    opl_data_path = os.path.join(opl_data_dir, selected_file)
    print(f"\nLoading OPL data from: {selected_file}")
    
    content = load_opl_file(opl_data_path)
    
    cells = parse_opl_set(content, 'Cells')
    species_list = parse_opl_set(content, 'Species')
    neighbors_list = parse_opl_array_of_sets(content, 'Neighbors')
    
    print(f"Loaded {len(cells)} cells")
    print(f"Species: {species_list}")
    print(f"Neighbors: {len(neighbors_list) if neighbors_list else 0} cell neighbor lists")
    
    return cells, species_list, neighbors_list, selected_file


def create_ordered_cells(cells, neighbors_list, dataset_gpd):
    """
    Create ordered cell list with geometries and metadata.
    
    Args:
        cells (list): Cell IDs from OPL data
        neighbors_list (list): Neighbor lists from OPL data
        dataset_gpd (GeoDataFrame): Menorca dataset
        
    Returns:
        list: Ordered cell dictionaries
    """
    # Create mappings
    geometry_map = {row['grid_id']: row.geometry for _, row in dataset_gpd.iterrows()}
    land_cover_map = {row['grid_id']: row['dominant_land_cover_name'] 
                      for _, row in dataset_gpd.iterrows()}
    
    # Build ordered cells
    ordered_cells = []
    for i, cell_id in enumerate(cells):
        if cell_id in geometry_map:
            ordered_cells.append({
                'grid_id': cell_id,
                'geometry': geometry_map[cell_id],
                'land_cover': land_cover_map.get(cell_id, 'Unknown'),
                'neighbors': neighbors_list[i] if neighbors_list and i < len(neighbors_list) else []
            })
    
    print(f"Matched {len(ordered_cells)} cells with geometries")
    return ordered_cells


def load_and_parse_solution(solution_dir):
    """
    Load and parse solution file selected by user.
    
    Returns:
        tuple: (add_data, cor_data, con_data, con_o_data, solution_filename)
    """
    selected_file = list_and_select_file(
        solution_dir,
        extension='.dat',
        prompt_message="Available solution files"
    )
    
    solution_path = os.path.join(solution_dir, selected_file)
    print(f"\nLoading solution from: {selected_file}")
    
    content = load_opl_file(solution_path)
    
    add_data = parse_opl_2d_array(content, 'add')
    cor_data = parse_opl_1d_array(content, 'cor')
    con_data = parse_opl_2d_array(content, 'con')
    con_o_data = parse_opl_3d_array(content, 'con_o')
    
    print(f"Parsed add: {len(add_data) if add_data else 0} rows")
    print(f"Parsed cor: {len(cor_data) if cor_data else 0} values")
    print(f"Parsed con: {len(con_data) if con_data else 0} rows")
    print(f"Parsed con_o: {len(con_o_data) if con_o_data else 0} cells")
    
    return add_data, cor_data, con_data, con_o_data, selected_file


def attach_solution_data_to_cells(ordered_cells, add_data, cor_data, con_data, 
                                   con_o_data, species_origins):
    """
    Attach solution data and origin flags to cell dictionaries.
    
    Args:
        ordered_cells (list): Cell dictionaries
        add_data (list): Action data
        cor_data (list): Corridor data
        con_data (list): Connection data
        con_o_data (list): Connection origin data
        species_origins (dict): Species origins mapping
        
    Returns:
        None (modifies ordered_cells in place)
    """
    for i, cell in enumerate(ordered_cells):
        cell['add'] = add_data[i] if add_data and i < len(add_data) else [0] * 4
        cell['cor'] = cor_data[i] if cor_data and i < len(cor_data) else 0
        cell['con'] = con_data[i] if con_data and i < len(con_data) else [0] * 4
        cell['con_o'] = con_o_data[i] if con_o_data and i < len(con_o_data) else [[0] * 24] * 4
        
        # Check if this cell is an origin for any species
        cell['is_origin'] = {}
        for species_long, origins in species_origins.items():
            cell['is_origin'][species_long] = cell['grid_id'] in origins


def create_solution_map(ordered_cells, grid_centroids, species_origins, output_path):
    """
    Create and save solution map (actions + corridors).
    
    Args:
        ordered_cells (list): Cell dictionaries with solution data
        grid_centroids (dict): Cell centroid coordinates
        species_origins (dict): Species origins mapping
        output_path (str): Output HTML file path
        
    Returns:
        None
    """
    print("\nCreating solution map...")
    solution_map = create_base_map()
    
    for cell in ordered_cells:
        color, cell_type = determine_solution_cell_color(cell, species_origins)
        cell['tooltip'] = build_solution_tooltip(cell, species_origins)
        add_cell_to_map(solution_map, cell, color, grid_centroids, 
                       add_neighbor_arrows=True)
    
    solution_map.save(output_path)
    inject_hover_javascript(output_path)
    print(f"Solution map saved to: {output_path}")


def create_connection_map(ordered_cells, grid_centroids, species_origins, output_path):
    """
    Create and save connection map (connections + corridors + origin arrows).
    
    Args:
        ordered_cells (list): Cell dictionaries with solution data
        grid_centroids (dict): Cell centroid coordinates
        species_origins (dict): Species origins mapping
        output_path (str): Output HTML file path
        
    Returns:
        None
    """
    print("\nCreating connection map...")
    connection_map = create_base_map()
    
    for cell in ordered_cells:
        color = determine_connection_cell_color(cell, species_origins)
        cell['tooltip'] = build_connection_tooltip(cell, species_origins)
        add_cell_to_map(connection_map, cell, color, grid_centroids, 
                       add_neighbor_arrows=True)
        add_connection_arrows(connection_map, cell, grid_centroids, species_origins)
    
    connection_map.save(output_path)
    inject_hover_javascript(output_path)
    print(f"Connection map saved to: {output_path}")


def main():
    """Main execution function."""
    # Configuration
    OPL_DATA_DIR = "opl_data"
    SOLUTION_DIR = "opl_solutions"
    OUTPUT_DIR = "html_files"
    
    # Load dataset
    dataset_gpd = load_menorca_dataset()
    
    # Get species origins from dataset
    species_origins = get_species_origins_from_dataset(dataset_gpd, SPECIES_FULL_NAMES)
    
    # Load OPL data
    cells, species_list, neighbors_list, opl_data_file = load_and_parse_opl_data(OPL_DATA_DIR)
    
    # Create ordered cells with geometries
    ordered_cells = create_ordered_cells(cells, neighbors_list, dataset_gpd)
    
    # Load solution
    add_data, cor_data, con_data, con_o_data, solution_file = load_and_parse_solution(SOLUTION_DIR)
    
    # Attach solution data to cells
    attach_solution_data_to_cells(ordered_cells, add_data, cor_data, 
                                   con_data, con_o_data, species_origins)
    
    # Compute centroids for arrow drawing
    grid_centroids = compute_centroids(ordered_cells)
    
    # Create output directory
    ensure_directory_exists(OUTPUT_DIR)
    
    print("\n=== Creating Visualizations ===")
    
    # Create solution map
    solution_output = os.path.join(OUTPUT_DIR, 
                                   f"solution_map_{solution_file.replace('.dat', '.html')}")
    create_solution_map(ordered_cells, grid_centroids, species_origins, solution_output)
    
    # Create connection map if connection data exists
    if con_data:
        connection_output = os.path.join(OUTPUT_DIR, 
                                        f"connection_map_{solution_file.replace('.dat', '.html')}")
        create_connection_map(ordered_cells, grid_centroids, species_origins, connection_output)
    
    # Print summary statistics
    print_summary_statistics(ordered_cells, SPECIES_FULL_NAMES)
    
    print("\nVisualization complete!")


if __name__ == "__main__":
    main()
