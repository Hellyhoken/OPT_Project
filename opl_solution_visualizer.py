from utils import *
import os
import re

print("Loading Menorca dataset...")
dataset_gpd = load_menorca_data()
print("Menorca dataset loaded.")

# List all solution files in opl_solutions directory
solution_dir = "opl_solutions"
solution_files = [f for f in os.listdir(solution_dir) if f.endswith('.dat')]

if not solution_files:
    print("No solution files found in opl_solutions directory!")
else:
    print("\nAvailable solution files:")
    for i, file in enumerate(solution_files, 1):
        print(f"{i}. {file}")
    
    # User selection
    while True:
        try:
            choice = int(input("\nEnter the number of the solution file to load: "))
            if 1 <= choice <= len(solution_files):
                selected_file = solution_files[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(solution_files)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Load the selected solution file
    solution_path = os.path.join(solution_dir, selected_file)
    print(f"\nLoading solution from: {selected_file}")
    
    with open(solution_path, 'r') as f:
        content = f.read()
    
    # Parse the 'add' array from the solution file
    # The 'add' array has format: add = [[row1] [row2] ... [rowN]]
    # Each row has 4 values representing actions for 4 species
    add_match = re.search(r'add = \[\[(.*?)\]\];', content, re.DOTALL)
    
    # Parse the 'cor' array for corridors (1D array with one value per cell)
    cor_match = re.search(r'cor = \[([\d\s]+)\];', content, re.DOTALL)
    
    species_names = ['atelerix_algirus', 'martes_martes', 'eliomys_quercinus', 'oryctolagus_cuniculus']
    
    if add_match:
        add_data = add_match.group(1)
        # Parse each row
        rows = re.findall(r'\[([\d\s]+)\]', add_data)
        
        # Initialize columns for each species action
        action_columns = [f'action_{name}' for name in species_names]
        
        for col in action_columns:
            dataset_gpd[col] = 0
        
        # Populate the dataframe with solution values
        for idx, row_str in enumerate(rows):
            if idx < len(dataset_gpd):
                values = [int(x) for x in row_str.split()]
                for j, col in enumerate(action_columns):
                    if j < len(values):
                        dataset_gpd.at[idx, col] = values[j]
        
        print(f"Successfully loaded 'add' array data!")
        print(f"Added columns: {', '.join(action_columns)}")
    else:
        print("Could not parse 'add' array from solution file")
    
    if cor_match:
        cor_data = cor_match.group(1)
        # Parse corridor values - it's a 1D array with one value per cell
        corridor_values = [int(x) for x in cor_data.split()]
        
        # Initialize corridor column
        dataset_gpd['corridor'] = 0
        
        # Populate the dataframe with corridor values
        for idx, value in enumerate(corridor_values):
            if idx < len(dataset_gpd):
                dataset_gpd.at[idx, 'corridor'] = value
        
        print(f"Successfully loaded 'cor' array data!")
        print(f"Added corridor column with {sum(corridor_values)} cells marked as corridors")
    else:
        print("Could not parse 'cor' array from solution file")
    
    if add_match or cor_match:
        print(f"\nDataset now has {len(dataset_gpd)} rows and {len(dataset_gpd.columns)} columns")
        if add_match:
            print(f"\nSample of action columns:")
            print(dataset_gpd[action_columns].head(10))
        if cor_match:
            print(f"\nSample of corridor column:")
            print(dataset_gpd['corridor'].head(10))
        
        # Create a summary column for cell type based on actions
        def get_cell_type(row):
            # Check for original populations
            has_population = any([row[f'has_{species}'] for species in species_names])
            
            if cor_match and row['corridor'] == 1:
                return 'corridor'
            elif has_population:
                # Check if any action is taken on this population cell
                if add_match:
                    actions = [row[col] for col in action_columns]
                    if sum(actions) > 0:
                        return 'population_with_action'
                    else:
                        return 'population_no_action'
                else:
                    return 'population_no_action'
            elif add_match:
                actions = [row[col] for col in action_columns]
                if sum(actions) == 0:
                    return 'no_action'
                else:
                    # Return which species have actions
                    active_species = [species_names[i].split('_')[0] for i, val in enumerate(actions) if val == 1]
                    return f"action: {', '.join(active_species)}"
            return 'no_action'
        
        dataset_gpd['cell_type'] = dataset_gpd.apply(get_cell_type, axis=1)
        
        # Define color mapping
        def get_cell_color(cell_type):
            if cell_type == 'corridor':
                return '#FFA500'  # Orange for corridors
            elif cell_type == 'population_with_action':
                return '#0066FF'  # Blue for populations with actions
            elif cell_type == 'population_no_action':
                return '#FF0000'  # Red for populations without actions
            elif cell_type == 'no_action':
                return '#E8E8E8'  # Light gray for no action
            else:
                return '#00CC00'  # Green for action cells
        
        dataset_gpd['color'] = dataset_gpd['cell_type'].apply(get_cell_color)
        
        # Create the map
        print("\nCreating map visualization...")
        map = folium.Map(
            location=[39.97, 4.0460],
            zoom_start=11,
            tiles='OpenStreetMap',
            width="90%",
            height="90%"
        )
        
        # Add cells to map
        for idx, row in dataset_gpd.iterrows():
            # Build tooltip with action information
            tooltip_lines = [
                f"Grid ID: {row['grid_id']}",
                f"Land Cover: {row['dominant_land_cover_name']}"
            ]
            
            # Add original population information
            has_any_population = False
            tooltip_lines.append("<br><b>Original Populations:</b>")
            for species in species_names:
                if row[f'has_{species}']:
                    has_any_population = True
                    tooltip_lines.append(f"  • {species}: YES")
            if not has_any_population:
                tooltip_lines.append("  None")
            
            if add_match:
                tooltip_lines.append("<br><b>Actions:</b>")
                has_any_action = False
                for i, species in enumerate(species_names):
                    action_val = row[action_columns[i]]
                    if action_val == 1:
                        has_any_action = True
                        tooltip_lines.append(f"  • {species}: YES")
                if not has_any_action:
                    tooltip_lines.append("  None")
            
            if cor_match:
                corridor_val = row['corridor']
                tooltip_lines.append(f"<br><b>Corridor:</b> {'YES' if corridor_val == 1 else 'NO'}")
            
            tooltip_lines.append(f"<br><b>Cell Type:</b> {row['cell_type']}")
            
            tooltip_html = "<br>".join(tooltip_lines)
            
            folium.GeoJson(
                row.geometry,
                style_function=lambda x, color=row['color']: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.7
                },
                tooltip=tooltip_html
            ).add_to(map)
        
        # Save the map
        output_file = f"solution_map_{selected_file.replace('.dat', '.html')}"
        map.save(output_file)
        print(f"\nMap saved to: {output_file}")
        print(f"Open this file in a web browser to view the solution visualization.")
        
        # Print summary statistics
        print(f"\n--- Solution Summary ---")
        if cor_match:
            print(f"Corridor cells: {dataset_gpd['corridor'].sum()}")
        if add_match:
            for i, species in enumerate(species_names):
                count = dataset_gpd[action_columns[i]].sum()
                print(f"Actions for {species}: {count}")
        
        # Print population statistics
        print(f"\n--- Population Statistics ---")
        for species in species_names:
            total_pop = dataset_gpd[f'has_{species}'].sum()
            if add_match:
                pop_with_action = dataset_gpd[dataset_gpd[f'has_{species}'] == True][f'action_{species}'].sum()
                print(f"{species}: {total_pop} cells (with action: {pop_with_action}, without: {total_pop - pop_with_action})")
            else:
                print(f"{species}: {total_pop} cells")



