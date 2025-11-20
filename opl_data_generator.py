"""OPL Data Generator

Generates OPL-compatible data files from the Menorca dataset.
Creates both JSON and .dat formats for use with OPL optimization models.
"""

import json
import os

from utils import (
    load_menorca_data, add_neighbors_column, 
    add_species_distance_column, get_suitability_score
)
from data import generate_suitability_data


def generate_model_data_json():
    """Generate the base model data JSON file if it doesn't exist."""
    if os.path.exists('opl_model_data.json'):
        print("OPL model data file already exists. Skipping data generation.")
        return

    print("Loading Menorca dataset...")
    dataset_gpd = load_menorca_data()
    print("Menorca dataset loaded.")
    print("Adding neighbors column...")
    dataset_gpd = add_neighbors_column(dataset_gpd)
    print("Neighbors column added.")
    print("Adding species distance columns...")
    dataset_gpd = add_species_distance_column(dataset_gpd)
    print("Species distance columns added.")

    suitability_dict = generate_suitability_data()

    # Prepare data dictionary
    export_data = {}

    # List of grid cell ids
    export_data['Cells'] = dataset_gpd['grid_id'].tolist()

    # Actions, species, connections as sets
    export_data['Actions'] = ['adaptation_atelerix', 'adaptation_martes',
                            'adaptation_eliomys', 'adaptation_oryctolagus', 'corridor']
    export_data['Species'] = ['atelerix', 'martes', 'eliomys', 'oryctolagus']
    export_data['Connections'] = ['connected_atelerix', 'connected_martes', 'connected_eliomys', 'connected_oryctolagus']

    # Costs for each action in each cell (dictionary of dictionaries)
    costs = {}
    for idx, row in dataset_gpd.iterrows():
        costs[row['grid_id']] = {action: row.get(f'cost_{action}', 0) for action in export_data['Actions']}
    export_data['Costs'] = costs

    # Suitability scores for actions and grid cells (computed in Python as OPL cannot do this)
    suitability_scores = {}
    for idx, row in dataset_gpd.iterrows():
        suitability_scores[row['grid_id']] = {}
        land_cover = row['dominant_land_cover_name']
        for action in export_data['Actions']:
            if action == 'corridor':
                continue
            # Using your predefined 'get_suitability_score' function here
            score = get_suitability_score(action, land_cover, suitability_dict)
            suitability_scores[row['grid_id']][action] = score
    export_data['SuitabilityScores'] = suitability_scores

    # Neighbors (list of neighbor grid ids for each cell)
    neighbors = {row['grid_id']: row['neighbors'] for idx, row in dataset_gpd.iterrows()}
    export_data['Neighbors'] = neighbors

    # Species distances per cell (already stored in columns like 'atelerix_distances')
    species_distances = {}
    for species in export_data['Species']:
        species_distances[species] = {row['grid_id']: row[f'{species}_distances'] for idx, row in dataset_gpd.iterrows()}
    export_data['SpeciesDistances'] = species_distances
    
    # Store the origin cell IDs for each species (in the order they appear in the dataset)
    species_origins = {}
    for species_short, species_long in [('atelerix', 'atelerix_algirus'), 
                                         ('martes', 'martes_martes'),
                                         ('eliomys', 'eliomys_quercinus'), 
                                         ('oryctolagus', 'oryctolagus_cuniculus')]:
        origins = dataset_gpd[dataset_gpd[f'has_{species_long}']]['grid_id'].tolist()
        species_origins[species_short] = origins
    export_data['SpeciesOrigins'] = species_origins

    # Other relevant parameters as needed. For example, area of each cell
    areas = {row['grid_id']: row['cell_area_km2'] for idx, row in dataset_gpd.iterrows()}
    export_data['Area'] = areas

    # Export to JSON
    with open('opl_model_data.json', 'w') as f:
        json.dump(export_data, f, indent=4)
    
    print("OPL model data JSON generated successfully.")


# Read the JSON data file
with open('opl_model_data.json', 'r') as file:
    data = json.load(file)

# OPL file writing utilities
def write_opl_set(f, name, array):
    """Write an OPL set: Name = { "item1", "item2", ... };"""
    f.write(f'{name} = {{\n')
    for item in array:
        f.write(f'  "{item}",\n')
    f.write('};\n\n')


def write_opl_map_of_list(f, name, map_of_lists):
    """Write an array of sets: Name = [{"a", "b"}, {"c"}, ...];"""
    f.write(f'{name} = [\n')
    for key, lst in map_of_lists.items():
        quoted_list = ', '.join(f'"{elem}"' for elem in lst)
        f.write(f'{{{quoted_list}}},\n')
    f.write('];\n\n')


def write_opl_map_of_numbers(f, name, map_of_nums):
    """Write a 1D array of numbers: Name = [val1, val2, ...];"""
    f.write(f'{name} = [\n')
    for key, val in map_of_nums.items():
        f.write(f'{val},\n')
    f.write('];\n\n')


def write_opl_2d_float_array(f, name, data, rows, cols):
    """
    Write a 2D float array as an OPL matrix.
    
    Args:
        f: File handle
        name (str): Variable name
        data (dict): Nested dict data[row_key][col_key] = value
        rows (list): Row keys in desired order
        cols (list): Column keys in desired order
    """
    f.write(f'{name} = [\n')
    for r in rows:
        row_vals = []
        for c in cols:
            val = data.get(r, {}).get(c, 0.0)
            row_vals.append(f'{val}')
        f.write('  [' + ', '.join(row_vals) + '],\n')
    f.write('];\n\n')

def write_species_distances(f, species_distances_data, n_closest, padding_value=1e6):
    """Write species distances as 3D array, keeping only n closest distances."""
    # Find maximum length
    max_length = 0
    for species_data in species_distances_data.values():
        for dist_list in species_data.values():
            if len(dist_list) > max_length:
                max_length = len(dist_list)
    
    f.write('SpeciesDistances = [\n')
    for species, species_data in species_distances_data.items():
        f.write('[\n')
        for cell, dist_list in species_data.items():
            # Keep only n smallest distances
            sorted_indices = sorted(range(len(dist_list)), key=lambda i: dist_list[i])[:n_closest]
            keep_indices = set(sorted_indices)
            
            padded_dists = []
            for idx in range(max_length):
                if idx < len(dist_list) and idx in keep_indices:
                    padded_dists.append(dist_list[idx])
                else:
                    padded_dists.append(padding_value)
            
            dist_str = ', '.join(str(d) for d in padded_dists)
            f.write(f'[{dist_str}],\n')
        f.write('],\n')
    f.write('];\n\n')


def generate_opl_dat_file(data, n_closest=11):
    """Generate OPL .dat file from JSON data."""
    output_path = f'opl_data/opl_model_data_n{n_closest}.dat'
    
    # Ensure output directory exists
    os.makedirs('opl_data', exist_ok=True)
    
    with open(output_path, 'w') as f:
        write_opl_set(f, 'Cells', data['Cells'])
        write_opl_set(f, 'Actions', data['Actions'])
        write_opl_set(f, 'Species', data['Species'])
        write_opl_set(f, 'Connections', data['Connections'])

        write_opl_2d_float_array(f, 'Costs', data['Costs'], data['Cells'], data['Actions'])
        write_opl_2d_float_array(f, 'SuitabilityScores', data['SuitabilityScores'], data['Cells'], data['Actions'])
        write_opl_map_of_list(f, 'Neighbors', data['Neighbors'])
        
        write_species_distances(f, data['SpeciesDistances'], n_closest)
        
        write_opl_map_of_numbers(f, 'Area', data['Area'])
    
    print(f"OPL .dat file generated: {output_path}")


def main():
    """Main execution function."""
    # Generate JSON data if not exists
    generate_model_data_json()
    
    # Load JSON data
    with open('opl_model_data.json', 'r') as file:
        data = json.load(file)
    
    # Generate .dat files with different n values
    for n in [2, 5, 11]:
        generate_opl_dat_file(data, n_closest=n)
    
    print("\nAll OPL data files generated successfully!")


if __name__ == "__main__":
    main()
