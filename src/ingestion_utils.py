import pandas as pd
import os
from io import StringIO, BytesIO
import numpy as np
import warnings as warnings_module
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Union
from pandas import CategoricalDtype

@dataclass
class IngestionMetadata:
    file_type: str = ""
    orientation: str = ""
    column_roles: Dict[str, str] = field(default_factory=dict)
    original_dtypes: Dict[str, str] = field(default_factory=dict)
    inferred_dtypes: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

def load_data(file_path_or_object: Union[str, StringIO, BytesIO]) -> Tuple[pd.DataFrame, str, List[str]]:
    """
    Accepts a file path or file-like object, detects file type by extension,
    loads into a pandas DataFrame, and handles common issues.

    Args:
        file_path_or_object: Path to the file (str) or a file-like object.

    Returns:
        Tuple[pd.DataFrame, str, List[str]]: A tuple containing:
            - pd.DataFrame: Loaded DataFrame.
            - str: Detected file type (e.g., 'csv', 'xlsx').
            - List[str]: List of warnings encountered during loading.
    """
    warnings: List[str] = []
    file_type: str = "unknown"

    if isinstance(file_path_or_object, str):
        file_extension = os.path.splitext(file_path_or_object)[1].lower()
        file_obj = file_path_or_object
    else:
        if hasattr(file_path_or_object, 'name'):
            file_extension = os.path.splitext(file_path_or_object.name)[1].lower()
        else:
            file_extension = '.csv'
        file_obj = file_path_or_object

    df = None
    
    encodings = ['utf-8', 'latin1', 'iso-8859-1']

    if file_extension in ['.csv', '.tsv', '.txt']:
        file_type = file_extension[1:]
        delimiters = [',', '\t', ';', '|']

        # First, try to read the file content to analyze delimiters
        file_content = None
        for encoding in encodings:
            try:
                if isinstance(file_obj, str):
                    with open(file_obj, 'r', encoding=encoding) as f:
                        file_content = f.read()
                else:
                    file_obj.seek(0)
                    file_content = file_obj.read().decode(encoding)
                break
            except Exception:
                continue

        if file_content:
            # Count delimiter occurrences to find the most common one
            delimiter_counts = {}
            for delimiter in delimiters:
                count = file_content.count(delimiter)
                if count > 0:
                    delimiter_counts[delimiter] = count

            if delimiter_counts:
                # Sort delimiters by frequency (most frequent first)
                sorted_delimiters = sorted(delimiter_counts.items(), key=lambda x: x[1], reverse=True)
                delimiters = [d[0] for d in sorted_delimiters] + [d for d in delimiters if d not in delimiter_counts]

        # Now try loading with the prioritized delimiters
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    if isinstance(file_obj, str):
                        df = pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding, engine='python')
                    else:
                        file_obj.seek(0)
                        df = pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding, engine='python')

                    if df.empty or df.shape[1] == 1:
                        if df.shape[1] == 1: # If only one column, delimiter was likely wrong
                            warnings.append(f"Attempted to load with delimiter '{delimiter}' and encoding '{encoding}', but resulted in a single column. Trying other options.")
                        continue # Try next delimiter/encoding

                    # Additional check: ensure consistent number of columns across non-empty rows
                    non_empty_rows = df.dropna(how='all')
                    if len(non_empty_rows) > 1:
                        col_counts = non_empty_rows.apply(lambda row: row.notna().sum(), axis=1)
                        if col_counts.std() > 1:  # If there's significant variation in column counts
                            warnings.append(f"Delimiter '{delimiter}' with encoding '{encoding}' resulted in inconsistent column counts across rows. Trying other options.")
                            continue

                    break # Successfully loaded
                except Exception as e:
                    warnings.append(f"Failed to load with delimiter '{delimiter}' and encoding '{encoding}': {e}")
            if df is not None: # If loaded with any delimiter for this encoding, break encoding loop
                break

        # If no delimiter worked consistently, try a fallback approach for mixed delimiters
        if df is None or (df.shape[1] == 1 and len(df) > 1):
            warnings.append("File appears to have inconsistent delimiters. Attempting fallback parsing.")
            # Try to parse manually by detecting delimiters per row
            try:
                if file_content:
                    lines = file_content.strip().split('\n')
                    if len(lines) > 1:
                        # Try to determine expected number of columns from header
                        header = lines[0]
                        max_cols = 0
                        best_delimiter = None

                        for delimiter in delimiters:
                            col_count = len(header.split(delimiter))
                            if col_count > max_cols:
                                max_cols = col_count
                                best_delimiter = delimiter

                        if best_delimiter and max_cols > 1:
                            # Parse each line with the best delimiter, fallback to others if needed
                            parsed_rows = []
                            for line in lines:
                                # Try the best delimiter first
                                parts = line.split(best_delimiter)
                                if len(parts) == max_cols:
                                    parsed_rows.append(parts)
                                else:
                                    # Try other delimiters
                                    found = False
                                    for alt_delim in delimiters:
                                        if alt_delim != best_delimiter:
                                            alt_parts = line.split(alt_delim)
                                            if len(alt_parts) == max_cols:
                                                parsed_rows.append(alt_parts)
                                                found = True
                                                break
                                    if not found:
                                        # If no delimiter works, keep as single column
                                        parsed_rows.append([line])

                            if parsed_rows:
                                df = pd.DataFrame(parsed_rows[1:], columns=parsed_rows[0])  # Skip header row for data
                                warnings.append(f"Successfully parsed file with mixed delimiters using fallback method.")
            except Exception as e:
                warnings.append(f"Fallback parsing also failed: {e}")

    elif file_extension in ['.xlsx', '.xls']:
        file_type = file_extension[1:]
        for encoding in encodings: # Encodings are less relevant for Excel but can sometimes be a factor for text within cells
            try:
                if isinstance(file_obj, str):
                    df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                else:
                    file_obj.seek(0)
                    df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                break # Successfully loaded
            except Exception as e:
                warnings.append(f"Failed to load Excel file with encoding '{encoding}': {e}")
    else:
        warnings.append(f"Unsupported file type detected: {file_extension}. Attempting to load as CSV.")
        file_type = "csv_fallback"
        # Fallback to CSV loading if extension is unknown
        delimiters = [',', '\t', ';', '|']
        for encoding in encodings:
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
                except Exception as e:
                    warnings.append(f"Fallback CSV loading failed with delimiter '{delimiter}' and encoding '{encoding}': {e}")
            if df is not None:
                break

    if df is None:
        raise ValueError("Could not load the file with common encodings or delimiters after multiple attempts.")

    # Drop empty rows and columns - handles "junk columns from exports"
    initial_rows, initial_cols = df.shape
    df.dropna(axis=0, how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)
    if df.shape[0] < initial_rows:
        warnings.append(f"Dropped {initial_rows - df.shape[0]} entirely empty rows.")
    if df.shape[1] < initial_cols:
        warnings.append(f"Dropped {initial_cols - df.shape[1]} entirely empty columns.")

    return df, file_type, warnings

def infer_and_coerce_datatypes(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str], Dict[str, str], List[str]]:
    """
    Infers and coerces data types from values, handling missing values,
    mixed types, and multiple date formats.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        Tuple[pd.DataFrame, Dict[str, str], Dict[str, str], List[str]]: A tuple containing:
            - pd.DataFrame: DataFrame with coerced data types.
            - Dict[str, str]: Original dtypes before coercion.
            - Dict[str, str]: Inferred dtypes after coercion.
            - List[str]: List of warnings encountered during type inference.
    """
    df_coerced = df.copy()
    original_dtypes = {col: str(df[col].dtype) for col in df.columns}
    inferred_dtypes: Dict[str, str] = {}
    warnings: List[str] = []

    for col in df_coerced.columns:
        # Try to convert to numeric (Int64 or Float64)
        numeric_series = pd.to_numeric(df_coerced[col], errors='coerce')
        numeric_ratio = numeric_series.notna().sum() / len(df_coerced)
        
        if numeric_ratio > 0.8: # Heuristic: 80% non-null numeric values
            # Check if all non-null numeric values are integers
            if (numeric_series.dropna() % 1 == 0).all():
                df_coerced[col] = numeric_series.astype(pd.Int64Dtype())
                inferred_dtypes[col] = 'Int64'
            else:
                df_coerced[col] = numeric_series.astype(pd.Float64Dtype())
                inferred_dtypes[col] = 'Float64'
            if numeric_ratio < 1.0:
                warnings.append(f"Column '{col}' was coerced to numeric, but {100 * (1 - numeric_ratio):.2f}% of values were unparseable.")
            continue

        # Try to convert to datetime
        with warnings_module.catch_warnings():
            warnings_module.filterwarnings("ignore", message="Could not infer format", category=UserWarning)
            warnings_module.filterwarnings("ignore", message="Parsing dates in .* format when dayfirst=True was specified", category=UserWarning)
            datetime_series = pd.to_datetime(df_coerced[col], errors='coerce', dayfirst=True)
        datetime_ratio = datetime_series.notna().sum() / len(df_coerced)

        if datetime_ratio > 0.8: # Heuristic: 80% non-null datetime values
            df_coerced[col] = datetime_series
            inferred_dtypes[col] = 'datetime64[ns]'
            if datetime_ratio < 1.0:
                warnings.append(f"Column '{col}' was coerced to datetime, but {100 * (1 - datetime_ratio):.2f}% of values were unparseable or in inconsistent formats.")
            continue

        # Try to convert to boolean
        bool_temp_series = df_coerced[col].astype(str).str.lower().str.strip()
        true_values = ['true', '1', 'yes', 'y']
        false_values = ['false', '0', 'no', 'n']
        bool_coerced_series = bool_temp_series.map(lambda x: True if x in true_values else (False if x in false_values else np.nan))
        boolean_ratio = bool_coerced_series.notna().sum() / len(df_coerced)

        if boolean_ratio > 0.8:
            df_coerced[col] = bool_coerced_series.astype(pd.BooleanDtype())
            inferred_dtypes[col] = 'boolean'
            if boolean_ratio < 1.0:
                warnings.append(f"Column '{col}' was coerced to boolean, but {100 * (1 - boolean_ratio):.2f}% of values were unparseable.")
            continue

        # Fallback to string or category
        # If unique values are less than 50% of total rows and more than 1, consider it categorical
        if df_coerced[col].nunique() / len(df_coerced) < 0.5 and df_coerced[col].nunique() > 1:
            df_coerced[col] = df_coerced[col].astype('category')
            inferred_dtypes[col] = 'category'
        else:
            df_coerced[col] = df_coerced[col].astype(pd.StringDtype())
            inferred_dtypes[col] = 'string'
            
    return df_coerced, original_dtypes, inferred_dtypes, warnings

def infer_column_roles(df: pd.DataFrame) -> Dict[str, str]:
    """
    Automatically classifies each column as Date/time, Numeric metric,
    Categorical dimension, or Identifier.

    Args:
        df (pd.DataFrame): The input DataFrame (preferably after type coercion).

    Returns:
        Dict[str, str]: A dictionary where keys are column names and values are their inferred roles.
    """
    column_roles: Dict[str, str] = {}
    
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            column_roles[col] = 'Date/time'
        elif pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() / len(df[col]) > 0.9 and len(df[col]) > 10: # Heuristic for identifier: >90% unique and more than 10 rows
                column_roles[col] = 'Identifier'
            else:
                column_roles[col] = 'Numeric metric'
        elif isinstance(df[col].dtype, CategoricalDtype) or pd.api.types.is_string_dtype(df[col]):
            if df[col].nunique() / len(df[col]) > 0.9 and len(df[col]) > 10: # Heuristic for identifier: >90% unique and more than 10 rows
                column_roles[col] = 'Identifier'
            else:
                column_roles[col] = 'Categorical dimension'
        else:
            column_roles[col] = 'Other'

    return column_roles

def detect_orientation(df: pd.DataFrame) -> str:
    """
    Infers whether the data is 'wide' (metrics as columns) or 'long' (variable/value structure).

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        str: 'wide' or 'long'.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns

    potential_value_cols = ['value', 'metric', 'data', 'count']
    potential_variable_cols = ['variable', 'category', 'type', 'attribute']

    has_value_col = any(col.lower() in potential_value_cols for col in non_numeric_cols)
    has_variable_col = any(col.lower() in potential_variable_cols for col in non_numeric_cols)

    if has_value_col and has_variable_col and len(numeric_cols) <=2 :
        return 'long'
    
    if len(numeric_cols) / df.shape[1] > 0.7:
        return 'wide'
    elif len(non_numeric_cols) / df.shape[1] > 0.5 and len(numeric_cols) <= 2:
        return 'long'
    
    return 'wide'
    
def process_gym_data(file_path_or_object: Union[str, StringIO, BytesIO]) -> Tuple[pd.DataFrame, IngestionMetadata]:
    """
    Orchestrates the data ingestion, type inference, and column role classification.

    Args:
        file_path_or_object: Path to the file (str) or a file-like object.

    Returns:
        Tuple[pd.DataFrame, IngestionMetadata]: A tuple containing:
            - pd.DataFrame: The processed DataFrame with inferred types.
            - IngestionMetadata: A dataclass object containing all inferred metadata and warnings.
    """
    metadata = IngestionMetadata()

    df_raw, file_type, load_warnings = load_data(file_path_or_object)
    metadata.file_type = file_type
    metadata.warnings.extend(load_warnings)
    
    df_processed, original_dtypes, inferred_dtypes, type_warnings = infer_and_coerce_datatypes(df_raw)
    metadata.original_dtypes = original_dtypes
    metadata.inferred_dtypes = inferred_dtypes
    metadata.warnings.extend(type_warnings)

    metadata.column_roles = infer_column_roles(df_processed)
    metadata.orientation = detect_orientation(df_processed)
    return df_processed, metadata
