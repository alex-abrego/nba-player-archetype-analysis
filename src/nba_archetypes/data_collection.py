import pandas as pd
from time import sleep
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


def get_advanced_stats(force=False) -> str:
    """
    Retrieves advanced player stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "advanced_stats.parquet").exists():
        print("Dataset already exists. Keeping existing file.")
        return str(RAW_DATA_DIR / "advanced_stats.parquet")
    
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        measure_type_detailed_defense="Advanced",
        per_mode_detailed="Totals",
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        timeout=60
    ).get_data_frames()[0]
    
    return save_raw_data(df, "advanced_stats")


def get_scoring_splits(force=False) -> str:
    """
    Retrieves scoring split stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "scoring_splits.parquet").exists():
        print("Dataset already exists. Keeping existing file.")
        return str(RAW_DATA_DIR / "scoring_splits.parquet")
    
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        measure_type_detailed_defense="Scoring",
        per_mode_detailed="Totals",
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        timeout=60
    ).get_data_frames()[0]
    
    return save_raw_data(df, "scoring_splits")


def get_tracking_stats(tracking_type: list[str] | None = None, force = False) -> list[str]:
    """
    Retrieves tracking stats from the NBA_API and saves them as Parquet files.
    
    Args:
        tracking_type (list[str] | None): A list of tracking stat types to retrieve. If None, retrieves all types needed.
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force:
        return print("Datasets already exist. Keeping existing files. Change force to True if this is an error.")
    if tracking_type is None:
        tracking_type = [
            "Passing", 
            "Rebounding", 
            "SpeedDistance", 
            "Possessions", 
            "Drives", 
            "CatchShoot", 
            "PullUpShot", 
            "PostTouch",  
            "PaintTouch", 
            "Efficiency"
            ]
    for type in tracking_type:
        print(f"Collecting {type} stats...")
        try:
            df = leaguedashptstats.LeagueDashPtStats(
                pt_measure_type=type,
                player_or_team="Player",
                per_mode_simple="Totals",
                season=SEASON,
                season_type_all_star=SEASON_TYPE,
                timeout=60
            ).get_data_frames()[0]
            save_raw_data(df, f"{type.lower()}_stats")
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
    return [f"{type.lower()}_stats.parquet" for type in tracking_type]


