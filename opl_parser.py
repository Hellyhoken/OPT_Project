"""
OPL Data Format Parser

This module provides functions to parse various OPL (Optimization Programming Language)
data structures from .dat files, including sets, arrays, and nested structures.
"""

import re


def parse_opl_set(content, name):
    """
    Parse an OPL set from file content.
    
    Args:
        content (str): The file content to parse
        name (str): The name of the set variable
        
    Returns:
        list: List of string items in the set, or None if not found
        
    Example:
        Name = { "item1", "item2", "item3" };
    """
    pattern = rf'{name}\s*=\s*\{{\s*(.*?)\s*\}};'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        items_str = match.group(1)
        items = re.findall(r'"([^"]+)"', items_str)
        return items
    return None


def parse_opl_1d_array(content, name):
    """
    Parse a 1D integer array from file content.
    
    Args:
        content (str): The file content to parse
        name (str): The name of the array variable
        
    Returns:
        list: List of integers, or None if not found
        
    Example:
        Name = [1, 0, 1, 0, 1];
    """
    pattern = rf'{name}\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        values_str = match.group(1)
        values = [int(x) for x in values_str.split() if x.strip()]
        return values
    return None


def parse_opl_array_of_sets(content, name):
    """
    Parse an array of sets from file content.
    
    Args:
        content (str): The file content to parse
        name (str): The name of the array variable
        
    Returns:
        list: List of lists, where each inner list contains set items, or None if not found
        
    Example:
        Name = [{"item1", "item2"}, {"item3"}, {}];
    """
    pattern = rf'{name}\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        sets_str = match.group(1)
        # Find all sets {...}
        set_pattern = r'\{([^}]*)\}'
        set_matches = re.findall(set_pattern, sets_str)
        result = []
        for set_content in set_matches:
            items = re.findall(r'"([^"]+)"', set_content)
            result.append(items)
        return result
    return None


def parse_opl_2d_array(content, name):
    """
    Parse a 2D integer array from file content.
    
    Args:
        content (str): The file content to parse
        name (str): The name of the array variable
        
    Returns:
        list: List of lists (2D array), or None if not found
        
    Example:
        Name = [[1, 0, 1], [0, 1, 0], [1, 1, 0]];
    """
    pattern = rf'{name}\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        rows_str = match.group(1)
        rows = re.findall(r'\[([\d\s]+)\]', rows_str)
        result = []
        for row_str in rows:
            values = [int(x) for x in row_str.split()]
            result.append(values)
        return result
    return None


def parse_opl_3d_array(content, name):
    """
    Parse a 3D integer array from file content.
    
    This function specifically handles arrays with 4 species per cell,
    which is the structure used for connection origins (con_o).
    
    Args:
        content (str): The file content to parse
        name (str): The name of the array variable
        
    Returns:
        list: 3D list structure [cell][species][origin], or None if not found
        
    Example:
        Name = [[[1 0] [0 1]] [[0 0] [1 1]]];
    """
    pattern = rf'{name}\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        data = match.group(1)
        clean_data = re.sub(r'\s+', ' ', data)
        
        # Match each cell block: [[...] [...] [...] [...]]
        # Assuming 4 species per cell structure
        cell_pattern = r'\[\s*\[([0-9\s]+)\]\s*\[([0-9\s]+)\]\s*\[([0-9\s]+)\]\s*\[([0-9\s]+)\]\s*\]'
        cell_matches = re.findall(cell_pattern, clean_data)
        
        result = []
        for cell_data in cell_matches:
            cell_arrays = []
            for species_row in cell_data:
                values = [int(x) for x in species_row.split()]
                cell_arrays.append(values)
            result.append(cell_arrays)
        return result
    return None


def load_opl_file(filepath):
    """
    Load and return the content of an OPL .dat file.
    
    Args:
        filepath (str): Path to the .dat file
        
    Returns:
        str: File content
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If the file cannot be read
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()
