import pandas as pd
import os
from io import StringIO, BytesIO
import numpy as np

def load_data(file_path_or_object):
    \"\"\"
    Accepts a file path or file-like object, detects file type by extension,
    loads into a pandas DataFrame, and handles common issues.

    Args:
        file_path_or_object: Path to the file (str) or a file-like object.

    Returns:
        pandas.DataFrame: Loaded DataFrame.
    \"\"\"
    if isinstance(file_path_or_object, str):
        file_extension = os.path.splitext(file_path_or_object)[1].lower()
        file_obj = file_path_or_object
    else:  # Assume it's a file-like object
        if hasattr(file_path_or_object, 'name'):
            file_extension = os.path.splitext(file_path_or_object.name)[1].lower()
        else:
            file_extension = '.csv' 
        file_obj = file_path_or_object

    df = None
    
    encodings = ['utf-8', 'latin1', 'iso-8859-1']

    for encoding in encodings:
        try:
            if file_extension in ['.csv', '.tsv', '.txt']:
                delimiters = [',', '\\t', ';', '|']
                for delimiter in delimiters:
                    try:
                        if isinstance(file_obj, str):
                            df = pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding, engine='python')
                        else:
                            file_obj.seek(0)
                            df = pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding, engine='python')
                        if df.empty or df.shape[1] == 1:
                            continue
                        break
                    except Exception:
                        continue
                if df is not None:
                    break
            elif file_extension in ['.xlsx', '.xls']:\
                if isinstance(file_obj, str):
                    df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                else:
                    file_obj.seek(0)
                    df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                break
        except Exception:
            continue
    
    if df is None:
        raise ValueError("Could not load the file with common encodings or delimiters.")

    df.dropna(axis=0, how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    return df

def infer_and_coerce_datatypes(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"
    Infers and coerces data types from values, handling missing values,
    mixed types, and multiple date formats.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with coerced data types.
    \"\"\"
    df_coerced = df.copy()

    for col in df_coerced.columns:
        # Try to convert to numeric (Int64 or Float64)
        # Use errors='coerce' to turn unparseable values into NaN
        numeric_series = pd.to_numeric(df_coerced[col], errors='coerce')
        
        # If nearly all values are numeric, coerce to numeric type
        if numeric_series.notna().sum() / len(df_coerced) > 0.8: # Heuristic: 80% non-null numeric values
            if (numeric_series == numeric_series.astype(pd.Int64Dtype())).all(): # Check if all are integers
                df_coerced[col] = numeric_series.astype(pd.Int64Dtype())
            else:
                df_coerced[col] = numeric_series.astype(pd.Float64Dtype())
            continue

        # Try to convert to datetime
        datetime_series = pd.to_datetime(df_coerced[col], errors='coerce', dayfirst=True)
        if datetime_series.notna().sum() / len(df_coerced) > 0.8: # Heuristic: 80% non-null datetime values
            df_coerced[col] = datetime_series
            continue

        # Try to convert to boolean
        # Robustly handle different boolean representations
        # Create a temporary series to hold boolean conversions
        bool_temp_series = df_coerced[col].astype(str).str.lower().str.strip()
        
        # Map common true/false strings to boolean values
        true_values = ['true', '1', 'yes', 'y']
        false_values = ['false', '0', 'no', 'n']

        if (bool_temp_series.isin(true_values + false_values)).sum() / len(df_coerced) > 0.8:
            df_coerced[col] = bool_temp_series.map(lambda x: True if x in true_values else (False if x in false_values else np.nan)).astype(pd.BooleanDtype())
            continue

        # Fallback to string or category
        # If unique values are less than 50% of total rows, consider it categorical
        if df_coerced[col].nunique() / len(df_coerced) < 0.5 and df_coerced[col].nunique() > 1: # Avoid coercing unique identifiers to category
            df_coerced[col] = df_coerced[col].astype('category')
        else:
            df_coerced[col] = df_coerced[col].astype(pd.StringDtype()) # Use nullable string dtype
            
    return df_coerced

def infer_column_roles(df: pd.DataFrame) -> dict:
    \"\"\"
    Automatically classifies each column as Date/time, Numeric metric,
    Categorical dimension, or Identifier.

    Args:
        df (pd.DataFrame): The input DataFrame (preferably after type coercion).

    Returns:
        dict: A dictionary where keys are column names and values are their inferred roles.
    \"\"\"
    column_roles = {}
    
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            column_roles[col] = 'Date/time'
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Heuristic for numeric metric vs. identifier
            # If a numeric column has many unique values relative to its size, it might be an identifier.
            # Or if it's a numeric column with few unique values, it could still be a categorical dimension (e.g., membership level 1, 2, 3)
            
            # For now, let's classify highly unique numeric columns as Identifier, otherwise Numeric metric
            if df[col].nunique() / len(df[col]) > 0.9: # More than 90% unique values
                column_roles[col] = 'Identifier'
            else:
                column_roles[col] = 'Numeric metric'
        elif pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            # Heuristic for categorical dimension vs. identifier (for string/object types)
            # If a string column has many unique values, it's likely an identifier.
            # If it has few unique values, it's a categorical dimension.
            if df[col].nunique() / len(df[col]) > 0.9: # More than 90% unique values
                column_roles[col] = 'Identifier'
            else:
                column_roles[col] = 'Categorical dimension'
        else:
            column_roles[col] = 'Other' # Should not happen often after type coercion

    return column_roles

def detect_orientation(df: pd.DataFrame) -> str:
    \"\"\"\
    Infers whether the data is \'wide\' (metrics as columns) or \'long\' (variable/value structure).\
\
    Args:\
        df (pd.DataFrame): The input DataFrame.\
\
    Returns:\
        str: \'wide\' or \'long\'.\
    \"\"\"\
    # Heuristic: If there are many non-numeric columns and few numeric, it might be long.\
    # Or if a significant portion of columns have very few unique values (potential ID or category columns)\
    \
    numeric_cols = df.select_dtypes(include=['number']).columns\
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns\
\
    # Rule 1: Check for common \'value\' or \'metric\' column names in non-numeric data,\
    # and a corresponding \'variable\' or \'category\' column.\
    \
    potential_value_cols = ['value', 'metric', 'data', 'count']\
    potential_variable_cols = ['variable', 'category', 'type', 'attribute']\
\
    has_value_col = any(col.lower() in potential_value_cols for col in non_numeric_cols)\
    has_variable_col = any(col.lower() in potential_variable_cols for col in non_numeric_cols)\
\
    if has_value_col and has_variable_col and len(numeric_cols) <=2 : # If there\'s only 1-2 numeric columns, usually it\'s long data (e.g., ID and value)\
        return 'long'\
    \
    # Rule 2: Proportion of unique values in non-numeric columns.\
    # In long format, often there\'s a column with many repeating categories (the \'variable\' column)\
    # and a column with the actual values.\
    \
    # This rule is tricky without domain knowledge, let\'s refine.\
    # A simple heuristic for now: if there are many columns and most are numeric, it\'s wide.\
    # If there are few numeric columns and many non-numeric, it might be long.\
\
    if len(numeric_cols) / df.shape[1] > 0.7: # More than 70% numeric columns\
        return 'wide'\
    elif len(non_numeric_cols) / df.shape[1] > 0.5 and len(numeric_cols) <= 2: # More than 50% non-numeric and few numeric\
        return 'long'\
    \
    # Fallback: If still uncertain, assume wide. Most datasets start wide.\
    return 'wide'
    
def process_gym_data(file_path_or_object):
    \"\"\"
    Orchestrates the data ingestion, type inference, and column role classification.

    Args:
        file_path_or_object: Path to the file (str) or a file-like object.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The processed DataFrame with inferred types.
            - dict: A dictionary of column roles.
            - str: The inferred orientation ('wide' or 'long').
    \"\"\"
    df_raw = load_data(file_path_or_object)
    df_processed = infer_and_coerce_datatypes(df_raw)
    column_roles = infer_column_roles(df_processed)
    orientation = detect_orientation(df_processed)

    return df_processed, column_roles, orientation
