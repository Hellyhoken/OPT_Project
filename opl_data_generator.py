from utils import *
from data import generate_suitability_data

print("Loading Menorca dataset...")
dataset_gpd = load_menorca_data()
print("Menorca dataset loaded.")
print("Adding neighbors column...")
dataset_gpd = add_neighbors_column(dataset_gpd)
print("Neighbors column added.")
print("Adding species distance columns...")
dataset_gpd = add_species_distance_column(dataset_gpd)
print("Species distance columns added.")
import json
import os

suitability_dict = generate_suitability_data()

if not os.path.exists('opl_model_data.json'):
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

    # Other relevant parameters as needed. For example, area of each cell
    areas = {row['grid_id']: row['cell_area_km2'] for idx, row in dataset_gpd.iterrows()}
    export_data['Area'] = areas

    # Export to JSON (or to .dat if preferred with some formatting)
    with open('opl_model_data.json', 'w') as f:
        json.dump(export_data, f, indent=4)

# Read the JSON data file
with open('opl_model_data.json', 'r') as file:
    data = json.load(file)

def write_opl_set(f, name, array):
    f.write(f'{name} = {{\n')
    for item in array:
        f.write(f'  "{item}",\n')
    f.write('};\n\n')

def write_opl_map_of_map(f, name, map_of_maps):
    f.write(f'{name} = [\n')
    for outer_key, inner_map in map_of_maps.items():
        for inner_key, val in inner_map.items():
            f.write(f' <"{outer_key}", "{inner_key}"> {val},\n')
    f.write('];\n\n')

def write_opl_map_of_list(f, name, map_of_lists):
    f.write(f'{name} = [\n')
    for key, lst in map_of_lists.items():
        # Convert list to OPL set syntax with quotes
        quoted_list = ', '.join(f'"{elem}"' for elem in lst)
        f.write(f'{{{quoted_list}}},\n')
    f.write('];\n\n')

def write_opl_map_of_numbers(f, name, map_of_nums):
    f.write(f'{name} = [\n')
    for key, val in map_of_nums.items():
        f.write(f'{val},\n')
    f.write('];\n\n')

def write_opl_tuples_of_floats(f, name, map_of_maps):
    """
    Write a set of tuples <key1, key2, float> representing a sparse matrix.
    Example:
    Costs = {
      <"cell_0_28", "adaptation_atelerix", 4.5>,
      <"cell_1_01", "adaptation_martes", 2.0>,
      ...
    };
    """
    f.write(f'{name} = {{\n')
    for outer_key, inner_map in map_of_maps.items():
        for inner_key, val in inner_map.items():
            f.write(f'  <"{outer_key}", "{inner_key}", {val}>,\n')
    f.write('};\n\n')

def write_opl_2d_float_array(f, name, data, rows, cols):
    """
    Write a 2D float array as an OPL matrix.
    'data' is a dict of dicts: data[row_key][col_key] = float value.
    'rows' and 'cols' define order of rows and columns.
    """
    f.write(f'{name} = [\n')
    for r in rows:
        row_vals = []
        for c in cols:
            val = data.get(r, {}).get(c, 0.0)  # default to 0.0 if missing
            row_vals.append(f'{val}')
        f.write('  [' + ', '.join(row_vals) + '],\n')
    f.write('];\n\n')

n = 2  # number of closest distances to keep
padding_value = 1e6

with open(f'opl_data/opl_model_data_n{n}.dat', 'w') as f:
    write_opl_set(f, 'Cells', data['Cells'])
    write_opl_set(f, 'Actions', data['Actions'])
    write_opl_set(f, 'Species', data['Species'])
    write_opl_set(f, 'Connections', data['Connections'])

    write_opl_2d_float_array(f, 'Costs', data['Costs'], data['Cells'], data['Actions'])
    write_opl_2d_float_array(f, 'SuitabilityScores', data['SuitabilityScores'], data['Cells'], data['Actions'])
    write_opl_map_of_list(f, 'Neighbors', data['Neighbors'])

    # Find the maximum length among all dist_lists
    max_length = 0
    for species_data in data['SpeciesDistances'].values():
        for dist_list in species_data.values():
            if len(dist_list) > max_length:
                max_length = len(dist_list)

    f.write('SpeciesDistances = [\n')
    for species, species_data in data['SpeciesDistances'].items():
        f.write('[\n')
        for cell, dist_list in species_data.items():
            # Indices of the n smallest distances
            sorted_indices = sorted(range(len(dist_list)), key=lambda i: dist_list[i])[:n]
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

    write_opl_map_of_numbers(f, 'Area', data['Area'])
