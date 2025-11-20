"""
File Selection Utilities

Utilities for interactive file selection and directory operations.
"""

import os


def list_and_select_file(directory, extension='.dat', prompt_message="Select a file"):
    """
    List files in a directory and prompt user to select one.
    
    Args:
        directory (str): Directory path to search
        extension (str): File extension to filter by
        prompt_message (str): Message to display to user
        
    Returns:
        str: Selected filename
        
    Raises:
        SystemExit: If no files are found
    """
    files = [f for f in os.listdir(directory) if f.endswith(extension)]
    
    if not files:
        print(f"No files with extension '{extension}' found in {directory}!")
        exit(1)
    
    print(f"\n{prompt_message}:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    
    while True:
        try:
            choice = int(input(f"\nEnter the number (1-{len(files)}): "))
            if 1 <= choice <= len(files):
                return files[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(files)}")
        except ValueError:
            print("Please enter a valid number")


def ensure_directory_exists(directory):
    """
    Create directory if it doesn't exist.
    
    Args:
        directory (str): Directory path to create
        
    Returns:
        bool: True if directory was created, False if it already existed
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
        return True
    return False


def get_species_origins_from_dataset(dataset_gpd, species_mapping):
    """
    Extract species origin cells from dataset.
    
    Args:
        dataset_gpd (GeoDataFrame): Dataset with species presence columns
        species_mapping (dict): Mapping of short names to full species names
        
    Returns:
        dict: Mapping of full species names to lists of origin cell IDs
    """
    species_origins = {}
    for species_short, species_long in species_mapping.items():
        column_name = f'has_{species_long}'
        if column_name in dataset_gpd.columns:
            origin_cells = dataset_gpd[dataset_gpd[column_name]]['grid_id'].tolist()
            species_origins[species_long] = origin_cells
            print(f"Found {len(origin_cells)} origins for {species_long}")
    return species_origins


def print_summary_statistics(ordered_cells, species_full_names):
    """
    Print summary statistics of the solution.
    
    Args:
        ordered_cells (list): List of cell dictionaries with solution data
        species_full_names (dict): Mapping of short to full species names
        
    Returns:
        None
    """
    print("\n=== Summary Statistics ===")
    print(f"Total cells: {len(ordered_cells)}")
    
    # Count corridor cells
    corridor_count = sum(1 for cell in ordered_cells if cell.get('cor', 0) == 1)
    if corridor_count > 0:
        print(f"Corridor cells: {corridor_count}")
    
    # Count actions per species
    if any('add' in cell for cell in ordered_cells):
        print("\n--- Action Summary ---")
        for i, species_long in enumerate(species_full_names.values()):
            count = sum(1 for cell in ordered_cells 
                       if 'add' in cell and i < len(cell['add']) and cell['add'][i] == 1)
            print(f"Actions for {species_long}: {count}")
    
    # Count connections per species
    if any('con' in cell for cell in ordered_cells):
        print("\n--- Connection Summary ---")
        for i, species_long in enumerate(species_full_names.values()):
            count = sum(1 for cell in ordered_cells 
                       if 'con' in cell and i < len(cell['con']) and cell['con'][i] == 1)
            print(f"Connections for {species_long}: {count}")
