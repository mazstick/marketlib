import os
from typing import Optional, List, Union
import pandas as pd

class FileReader:
    """
    A class to read and write financial market data files.

    Supports CSV, JSON, and Excel files.

    Parameters:
        filepath (str): Default path of the file to read/write.

    Methods:
        read: Reads the file into a pandas DataFrame.
        write: Writes a pandas DataFrame to a file (default or new path).
    """

    def __init__(self, filepath: str):
        if not isinstance(filepath, str):
            raise TypeError("filepath must be a string.")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        self.filepath = filepath
        self._cache: Optional[pd.DataFrame] = None

    def read(
        self,
        date_columns: Optional[List[str]] = None,
        index_column: Optional[Union[str, int]] = None,
        use_columns: Optional[List[str]] = None,
        cache: bool = True,
        force_reload: bool = False
    ) -> pd.DataFrame:
        """
        Reads the file and returns a pandas DataFrame.

        Parameters:
            date_columns: List of column names to parse as datetime.
            index_column: Column name or index to set as DataFrame index.
            use_columns: List of columns to load.
            cache: If True, cache the loaded DataFrame for future calls.
            force_reload: If True, reload data ignoring cache.

        Returns:
            pd.DataFrame: The loaded DataFrame.

        Raises:
            RuntimeError: If reading the file fails.
            KeyError: If specified columns for dates or use_columns are missing.
            ValueError: If file format is unsupported.
        """

        if cache and self._cache is not None and not force_reload:
            return self._cache

        try:
            if self.filepath.endswith('.csv'):
                df = pd.read_csv(
                    self.filepath,
                    usecols=use_columns,
                    parse_dates=date_columns,
                    index_col=index_column
                )
            elif self.filepath.endswith('.json'):
                df = pd.read_json(self.filepath)
                if index_column is not None:
                    if isinstance(index_column, int):
                        try:
                            index_column = df.columns[index_column]
                        except IndexError:
                            raise ValueError(f"Column index {index_column} is out of bounds.")
                    if index_column not in df.columns:
                        raise ValueError(f"Index column '{index_column}' not found in columns: {df.columns.tolist()}")
                    df.set_index(index_column, inplace=True)
                    
                if date_columns:
                    for col in date_columns:
                        if col not in df.columns:
                            raise KeyError(f"Date column '{col}' not found in JSON file.")
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        
                if use_columns:
                    missing = set(use_columns) - set(df.columns)
                    if missing:
                        raise KeyError(f"Missing columns in JSON file: {missing}")
                    df = df[use_columns]
                
            elif self.filepath.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(
                    self.filepath,
                    usecols=use_columns,
                    parse_dates=date_columns,
                    index_col=index_column
                )
            else:
                raise ValueError("Unsupported file format. Supported: csv, json, xls, xlsx.")

            if cache:
                self._cache = df

            return df

        except Exception as e:
            raise RuntimeError(f"Error reading file '{self.filepath}': {e}")

    def write(
        self,
        df: pd.DataFrame,
        filepath: Optional[str] = None
    ) -> None:
        """
        Writes the given DataFrame to a file.

        Parameters:
            df (pd.DataFrame): DataFrame to write.
            filepath (Optional[str]): Path to save the file. If None, uses default path.

        Raises:
            ValueError: If file format is unsupported or filepath extension missing.
            RuntimeError: If writing to file fails.
            TypeError: If df is not a pandas DataFrame.
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        path = filepath if filepath is not None else self.filepath

        if not isinstance(path, str):
            raise TypeError("filepath must be a string.")

        ext = os.path.splitext(path)[1].lower()

        try:
            if ext == '.csv':
                df.to_csv(path, index=True)
            elif ext == '.json':
                df.reset_index(inplace=True)
                df.to_json(path, orient='records', date_format='iso')
            elif ext in ('.xls', '.xlsx'):
                df.to_excel(path, index=True)
            else:
                raise ValueError("Unsupported file format for writing. Supported: csv, json, xls, xlsx.")
        except Exception as e:
            raise RuntimeError(f"Error writing file '{path}': {e}")
