import pandas as pd
from nba_archetypes.config import RAW_DATA_DIR

def csv_to_parquet(csv_file_name: str, parquet_file_name: str) -> None:
    """
    Converts a CSV file to a Parquet file.
    
    Args:
        csv_file_name (str): The name of the CSV file to convert.
        parquet_file_name (str): The name of the Parquet file to create.
    """
    
    df = pd.read_csv(RAW_DATA_DIR / csv_file_name)
    df.to_parquet(RAW_DATA_DIR / parquet_file_name, index = False)

def save_raw_data(df: pd.DataFrame, file_name: str) -> None:
    """
    Saves a raw NBA API DataFrame as a Parquet file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_name (str): The name of the Parquet file to create (without .parquet extension).
    """

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(RAW_DATA_DIR / f"{file_name}.parquet", index=False)

    print(f"Saved {file_name}: {len(df)} rows")