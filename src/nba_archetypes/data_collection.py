import pandas as pd
from nba_archetypes.config import SEASON, SEASON_TYPE, RAW_DATA_DIR
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguedashptstats,
    leaguedashplayershotlocations,
    leaguehustlestatsplayer
)


def csv_to_parquet(csv_file_name: str, parquet_file_name: str) -> None:
    """
    Converts a CSV file to a Parquet file.
    
    Args:
        csv_file_name (str): The name of the CSV file to convert (without .csv extension).
        parquet_file_name (str): The name of the Parquet file to create (without .parquet extension).

    Results:
        A Parquet file saved in the RAW_DATA_DIR directory.
    """
    df = pd.read_csv(RAW_DATA_DIR / f"{csv_file_name}.csv")
    df.to_parquet(RAW_DATA_DIR / f"{parquet_file_name}.parquet", index = False)

    print(f"Converted {parquet_file_name} to Parquet: {len(df)} rows and {len(df.columns)} columns")


def save_raw_data(df: pd.DataFrame, file_name: str) -> None:
    """
    Saves a raw NBA API DataFrame as a Parquet file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_name (str): The name of the Parquet file to create (without .parquet extension).

    Results:
        A Parquet file saved in the RAW_DATA_DIR directory.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(RAW_DATA_DIR / f"{file_name}.parquet", index=False)

    print(f"Saved {file_name}: {len(df)} rows and {len(df.columns)} columns")


def get_base_stats(force=False) -> str:
    """
    Retrieves base player stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "base_stats.parquet").exists():
        print("Dataset already exists. Keeping existing file.")
        return str(RAW_DATA_DIR / "base_stats.parquet")
    
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        measure_type_detailed_defense="Base",
        per_mode_detailed="Totals",
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        timeout=60
    ).get_data_frames()[0]
    
    return save_raw_data(df, "base_stats")