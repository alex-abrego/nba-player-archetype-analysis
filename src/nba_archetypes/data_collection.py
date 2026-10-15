import pandas as pd
from time import sleep
from nba_archetypes.config import SEASON, SEASON_TYPE, RAW_DATA_DIR
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguedashptstats,
    leaguedashplayershotlocations,
    leaguehustlestatsplayer,
    leagueseasonmatchups
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


def save_parquet_file(df: pd.DataFrame, file_name: str, target_dir: str) -> None:
    """
    Saves a raw NBA API DataFrame as a Parquet file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_name (str): The name of the Parquet file to create (without .parquet extension).
        dir (str): The file Path that the saved file should be stored in.

    Results:
        A Parquet file saved in the RAW_DATA_DIR directory.
    """
    if target_dir != RAW_DATA_DIR and (target_dir / f"{file_name}.parquet").exists():
        print("File already exists. Keeping existing file.")
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(target_dir / f"{file_name}.parquet", index=False)

    print(f"Saved {file_name}: {len(df)} rows and {len(df.columns)} columns")


def save_csv_file(df: pd.DataFrame, file_name: str, target_dir: str) -> None:
    """
    Saves a raw NBA API DataFrame as a csv file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_name (str): The name of the csv file to create (without .csv extension).
        dir (str): The file Path that the saved file should be stored in.

    Results:
        A csv file saved in the RAW_DATA_DIR directory.
    """
    if target_dir != RAW_DATA_DIR and (target_dir / f"{file_name}.csv").exists():
        print("File already exists. Keeping existing file.")
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_dir / f"{file_name}.csv", index=False)

    print(f"Saved {file_name}: {len(df)} rows and {len(df.columns)} columns")


def get_player_stats(measure_type: list[str] | None = None, force=False) -> list[str]:
    """
    Retrieves player stats (base, advanced, scoring, and usage) from the NBA API and saves them as a Parquet file.
    
    Args:
        measure_type (list[str] | None): A list of measure types to retrieve. If None, retrieves all types needed.
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force:
        return print("Change force to True if datasets don't already exist.")
    if measure_type is None:
        measure_type = [
            "Base",
            "Advanced",
            "Scoring",
            "Usage"
            ]
    for type in measure_type:
        print(f"Collecting {type} stats...")
        try:
            df = leaguedashplayerstats.LeagueDashPlayerStats(
                measure_type_detailed_defense=type,
                per_mode_detailed="Totals",
                season=SEASON,
                season_type_all_star=SEASON_TYPE,
                timeout=60
            ).get_data_frames()[0]
            save_parquet_file(df, f"{type.lower()}_stats", RAW_DATA_DIR)
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
    return [f"{type.lower()}_stats.parquet" for type in measure_type]


def get_tracking_stats(tracking_type: list[str] | None = None, force = False) -> list[str]:
    """
    Retrieves tracking stats from the NBA_API and saves them as Parquet files.
    
    Args:
        tracking_type (list[str] | None): A list of tracking stat types to retrieve. If None, retrieves all types needed.
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force:
        return print("Change force to True if datasets don't already exist.")
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
            save_parquet_file(df, f"{type.lower()}_stats", RAW_DATA_DIR)
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
    return [f"{type.lower()}_stats.parquet" for type in tracking_type]


def get_shot_location_stats(force=False) -> str:
    """
    Retrieves shot location stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "shot_locations.parquet").exists():
        print("Dataset already exists. Keeping existing file. Change force to True if you want to overwrite it.")
        return str(RAW_DATA_DIR / "shot_locations.parquet")
    
    df = leaguedashplayershotlocations.LeagueDashPlayerShotLocations(
        measure_type_simple="Base",
        per_mode_detailed="Totals",
        distance_range="By Zone",
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        timeout=60
    ).get_data_frames()[0]

    shot_location_columns = [
    "PLAYER_ID",
    "PLAYER_NAME",
    "TEAM_ID",
    "TEAM_ABBREVIATION",
    "AGE",
    "NICKNAME",
    "RA_FGM",
    "RA_FGA",
    "RA_FG_PCT",
    "PAINT_NON_RA_FGM",
    "PAINT_NON_RA_FGA",
    "PAINT_NON_RA_FG_PCT",
    "MIDRANGE_FGM",
    "MIDRANGE_FGA",
    "MIDRANGE_FG_PCT",
    "LEFT_CORNER_3_FGM",
    "LEFT_CORNER_3_FGA",
    "LEFT_CORNER_3_FG_PCT",
    "RIGHT_CORNER_3_FGM",
    "RIGHT_CORNER_3_FGA",
    "RIGHT_CORNER_3_FG_PCT",
    "ABOVE_BREAK_3_FGM",
    "ABOVE_BREAK_3_FGA",
    "ABOVE_BREAK_3_FG_PCT",
    "BACKCOURT_FGM",
    "BACKCOURT_FGA",
    "BACKCOURT_FG_PCT",
    "CORNER_3_FGM",
    "CORNER_3_FGA",
    "CORNER_3_PCT"
    ]

    shot_location_clean = df.copy()
    shot_location_clean.columns = shot_location_columns
    shot_location_clean = shot_location_clean.iloc[1:]
    return save_parquet_file(shot_location_clean, "shot_locations", RAW_DATA_DIR)


def get_hustle_stats(force=False) -> str:
    """
    Retrieves hustle stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "hustle_stats.parquet").exists():
        print("Dataset already exists. Keeping existing file. Change force to True if you want to overwrite it.")
        return str(RAW_DATA_DIR / "hustle_stats.parquet")

    df = leaguehustlestatsplayer.LeagueHustleStatsPlayer(
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        per_mode_time="Totals",
        timeout=60
        ).get_data_frames()[0]

    return save_parquet_file(df, "hustle_stats", RAW_DATA_DIR)


def get_matchup_stats(force=False) -> str:
    """
    Retrieves matchup stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "matchup_stats.parquet").exists():
        print("Dataset already exists. Keeping existing file. Change force to True if you want to overwrite it.")
        return str(RAW_DATA_DIR / "matchup_stats.parquet")

    df = leagueseasonmatchups.LeagueSeasonMatchups(
        season=SEASON,
        season_type_playoffs=SEASON_TYPE,
        per_mode_simple="Totals",
        league_id="00",
        timeout=60
        ).get_data_frames()[0]

    return save_parquet_file(df, "matchup_stats", RAW_DATA_DIR)