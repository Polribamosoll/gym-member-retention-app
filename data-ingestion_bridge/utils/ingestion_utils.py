import pandas as pd
import os
from io import StringIO, BytesIO

def load_data(file_path_or_object):
    """
    Accepts a file path or file-like object, detects file type by extension,
    loads into a pandas DataFrame, and handles common issues.

    Args:
        file_path_or_object: Path to the file (str) or a file-like object.

    Returns:
        pandas.DataFrame: Loaded DataFrame.
    """
    if isinstance(file_path_or_object, str):
        file_extension = os.path.splitext(file_path_or_object)[1].lower()
        file_obj = file_path_or_object
    else:  # Assume it's a file-like object
        # Try to infer extension from name attribute if available
        if hasattr(file_path_or_object, 'name'):
            file_extension = os.path.splitext(file_path_or_object.name)[1].lower()
        else:
            # Default to CSV if no extension can be inferred from file-like object
            file_extension = '.csv' 
        file_obj = file_path_or_object

    df = None
    
    # Try common encodings
    encodings = ['utf-8', 'latin1', 'iso-8859-1']

    for encoding in encodings:
        try:
            if file_extension in ['.csv', '.tsv', '.txt']:
                # Try common delimiters for CSV/TSV/TXT
                delimiters = [',', '\t', ';', '|']
                for delimiter in delimiters:
                    try:
                        if isinstance(file_obj, str):
                            df = pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding)
                        else:
                            # For file-like objects, we need to reset their position after each read attempt
                            file_obj.seek(0)
                            df = pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding)
                        if df.empty or df.shape[1] == 1: # If only one column, delimiter was likely wrong
                            continue
                        break # Successfully loaded with a delimiter
                    except Exception:
                        continue
                if df is not None:
                    break # Successfully loaded with an encoding
            elif file_extension in ['.xlsx', '.xls']:
                if isinstance(file_obj, str):
                    df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                else:
                    file_obj.seek(0)
                    df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                break # Successfully loaded excel
        except Exception:
            continue
    
    if df is None:
        raise ValueError("Could not load the file with common encodings or delimiters.")

    # Drop empty rows and columns
    df.dropna(axis=0, how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    return df

def detect_orientation(df: pd.DataFrame) -> str:
    """
    Infers whether the data is 'wide' (metrics as columns) or 'long' (variable/value structure).

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        str: 'wide' or 'long'.
    """
    # Heuristic: If there are many non-numeric columns and few numeric, it might be long.
    # Or if a significant portion of columns have very few unique values (potential ID or category columns)
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns

    # Rule 1: Check for common 'value' or 'metric' column names in non-numeric data,
    # and a corresponding 'variable' or 'category' column.
    
    potential_value_cols = ['value', 'metric', 'data', 'count']
    potential_variable_cols = ['variable', 'category', 'type', 'attribute']

    has_value_col = any(col.lower() in potential_value_cols for col in non_numeric_cols)
    has_variable_col = any(col.lower() in potential_variable_cols for col in non_numeric_cols)

    if has_value_col and has_variable_col and len(numeric_cols) <=2 : # If there's only 1-2 numeric columns, usually it's long data (e.g., ID and value)
        return 'long'
    
    # Rule 2: Proportion of unique values in non-numeric columns.
    # In long format, often there's a column with many repeating categories (the 'variable' column)
    # and a column with the actual values.
    
    # This rule is tricky without domain knowledge, let's refine.
    # A simple heuristic for now: if there are many columns and most are numeric, it's wide.
    # If there are few numeric columns and many non-numeric, it might be long.

    if len(numeric_cols) / df.shape[1] > 0.7: # More than 70% numeric columns
        return 'wide'
    elif len(non_numeric_cols) / df.shape[1] > 0.5 and len(numeric_cols) <= 2: # More than 50% non-numeric and few numeric
        return 'long'
    
    # Fallback: If still uncertain, assume wide. Most datasets start wide.
    return 'wide'
