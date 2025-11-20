import pandas as pd
import geopandas as gpd
import numpy as np
import collections
import folium
from data import suitability_score_dict, suitability_color_map

def get_neighbors(grid_id, all_grid_ids):
    col, row = map(int, grid_id.split('_')[1:])
    neighbors = []

    # Define potential neighbor offsets (up, down, left, right)
    potential_neighbors_coords = [
        (row - 1, col), # Up
        (row + 1, col), # Down
        (row, col - 1), # Left
        (row, col + 1),  # Right
        (row - 1, col - 1), # Up-Left
        (row + 1, col + 1), # Down-Right
        (row + 1, col - 1), # Left-Down
        (row - 1, col + 1)  # Right-Up
    ]

    for r, c in potential_neighbors_coords:
        neighbor_id = f"cell_{c}_{r}"
        if neighbor_id in all_grid_ids:
            neighbors.append(neighbor_id)

    return neighbors

def add_neighbors_column(dataset_gpd):
    all_grid_ids = set(dataset_gpd['grid_id'])

    dataset_gpd['neighbors'] = dataset_gpd['grid_id'].apply(lambda x: get_neighbors(x, all_grid_ids))
    return dataset_gpd

def add_species_distance_column(dataset_gpd):
    # Flood fill of species distances
    for species in ['atelerix_algirus','martes_martes','eliomys_quercinus','oryctolagus_cuniculus']:
        short_spec = species.split('_')[0]
        starting_points = dataset_gpd.loc[dataset_gpd[f"has_{species}"],'grid_id'].tolist()
        dataset_gpd[f"{short_spec}_distances"] = [[0 for _ in range(len(starting_points))] for _ in range(len(dataset_gpd))]

        # For each starting population, perform a BFS to find distances to all other cells.
        for i, source_grid_id in enumerate(starting_points):
            queue = collections.deque([(source_grid_id, 0)]) # (grid_id, distance)
            visited = set([source_grid_id])

            while queue:
                current_grid_id, current_dist = queue.popleft()

                dataset_gpd.loc[dataset_gpd['grid_id'] == current_grid_id, f"{short_spec}_distances"].iloc[0][i] = current_dist

                # Get neighbors of the current cell
                current_row_idx = dataset_gpd[dataset_gpd['grid_id'] == current_grid_id].index[0]
                neighbors = dataset_gpd.loc[current_row_idx, 'neighbors']

                for neighbor_grid_id in neighbors:
                    if neighbor_grid_id not in visited:
                        new_dist = current_dist + 1
                        visited.add(neighbor_grid_id)
                        queue.append((neighbor_grid_id, new_dist))
    return dataset_gpd

def get_suitability_color(land_cover_name, suitability_df):
    suitability_row = suitability_df[suitability_df['land_cover_type'] == land_cover_name]
    if suitability_row.empty:
        return "#aaaaaa", "unknown"
    suitability_row = suitability_row.iloc[0]
    suitability = suitability_row['suitability']
    color = suitability_color_map[suitability.lower()]
    return color, suitability

def get_suitability_score(action, land_cover_name, suitability_dict):
    if action == 'corridor':
        return 0
    suitability_df = suitability_dict[action]
    _, suitability = get_suitability_color(land_cover_name, suitability_df)
    if suitability == 'unknown':
        return 0
    return suitability_score_dict[suitability.lower()]

def plot_suitability_map(dataset_gpd, suitability_df, species):
    map = folium.Map(
        location=[39.97, 4.0460],
        zoom_start=11,
        tiles='OpenStreetMap',
        width="60%"
    )

    for idx, row in dataset_gpd.iterrows():
        land_cover_name = row['dominant_land_cover_name']
        color, suitability = get_suitability_color(land_cover_name, suitability_df)

        if row[f'has_{species}']:
            color = 'green'

        folium.GeoJson(
            row.geometry,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7
            },
            tooltip=f"""
            Grid ID: {row['grid_id']}<br>
            Dominant Land Cover: {land_cover_name}<br>
            Suitability: {suitability}<br>
            """
        ).add_to(map)
    return map

def load_menorca_data():
    dataset_gpd = gpd.read_file("https://gitlab.com/drvicsana/opt-milp-project-2025/-/raw/main/datasets/dataset.geojson")
    dataset_gpd["dominant_land_cover_name"] = dataset_gpd['dominant_land_cover_name'].replace(
        "Land Principally Occupied by Agriculture with Significant Areas of Natural Vegetation",
        "Agriculture with Natural Vegetation"
    )

    return dataset_gpd
