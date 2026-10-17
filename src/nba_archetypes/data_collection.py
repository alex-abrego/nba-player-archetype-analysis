import pandas as pd
from pathlib import Path
from time import sleep
from nba_archetypes.config import SEASON, SEASON_TYPE, RAW_DATA_DIR
from nba_archetypes.data_validation import validate_api_data
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguedashptstats,
    leaguedashplayershotlocations,
    leaguehustlestatsplayer,
    leagueseasonmatchups
)


def csv_to_parquet(csv_file_name: str, parquet_file_name: str, target_dir: Path) -> None:
    """
    Converts a CSV file to a Parquet file.
    
    Args:
        csv_file_name (str): The name of the CSV file to convert (without .csv extension).
        parquet_file_name (str): The name of the Parquet file to create (without .parquet extension).

    Results:
        A Parquet file saved in the RAW_DATA_DIR directory.
    """
    df = pd.read_csv(RAW_DATA_DIR / f"{csv_file_name}.csv")
    save_parquet_file(df, parquet_file_name, target_dir)

    print(f"Converted {parquet_file_name} to Parquet: {len(df)} rows and {len(df.columns)} columns")


def save_parquet_file(df: pd.DataFrame, file_name: str, target_dir: Path, overwrite: bool = False) -> Path:
    """
    Saves a DataFrame as a Parquet file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_name (str): The name of the Parquet file to create (without .parquet extension).
        target_dir (Path): The file Path that the saved file should be stored in.

    Results:
        A Parquet file saved in the target_dir directory.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{file_name}.parquet"
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"{file_name} already exists. Set overwrite = True to replace it.")
    temp_path = target_dir / f"{file_name}_temp.parquet"
    try:
        df.to_parquet(temp_path, index=False)
        temp_path.replace(file_path)
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"Saved {file_name}: {len(df)} rows and {len(df.columns)} columns")
    return file_path


def save_csv_file(df: pd.DataFrame, file_name: str, target_dir: Path, overwrite: bool = False) -> Path:
    """
    Saves a DataFrame as a csv file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        file_name (str): The name of the csv file to create (without .csv extension).
        dir (Path): The file Path that the saved file should be stored in.

    Results:
        A csv file saved in the target_dir directory.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{file_name}.csv"
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"{file_name} already exists. Set overwrite = True to replace it.")
    temp_path = target_dir / f"{file_name}_temp.csv"
    try:
        df.to_csv(temp_path, index=False)
        temp_path.replace(file_path)
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"Saved {file_name}: {len(df)} rows and {len(df.columns)} columns")
    return file_path


def get_player_stats(measure_type: list[str] | None = None, force: bool = False) -> list[str]:
    """
    Retrieves player stats (base, advanced, scoring, and usage) from the NBA API and saves them as a Parquet file.
    
    Args:
        measure_type (list[str] | None): A list of measure types to retrieve. If None, retrieves all types needed.
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if measure_type is None:
        measure_type = [
            "Base",
            "Advanced",
            "Scoring",
            "Usage"
            ]
    for type in measure_type:
        file_name = f"{type.lower()}_stats.parquet"
        file_path = RAW_DATA_DIR / file_name
        if file_path.exists() and not force:
            print(f"{file_name} already exists. Skipping download.")
            continue
        print(f"Collecting {type} stats...")
        try:
            df = leaguedashplayerstats.LeagueDashPlayerStats(
                measure_type_detailed_defense=type,
                per_mode_detailed="Totals",
                season=SEASON,
                season_type_all_star=SEASON_TYPE,
                timeout=60
            ).get_data_frames()[0]
            validate_api_data(df, required_columns=["PLAYER_ID", "PLAYER_NAME", "MIN"])
            save_parquet_file(df, f"{type.lower()}_stats", RAW_DATA_DIR, overwrite=force)
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
            raise
    return [f"{type.lower()}_stats.parquet" for type in measure_type]


def get_tracking_stats(tracking_type: list[str] | None = None, force = False) -> list[str]:
    """
    Retrieves tracking stats from the NBA_API and saves them as Parquet files.
    
    Args:
        tracking_type (list[str] | None): A list of tracking stat types to retrieve. If None, retrieves all types needed.
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
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
        file_name = f"{type.lower()}_stats.parquet"
        file_path = RAW_DATA_DIR / file_name
        if file_path.exists() and not force:
            print(f"{file_name} already exists. Skipping download.")
            continue
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
            validate_api_data(df, required_columns=["PLAYER_ID", "PLAYER_NAME"])
            save_parquet_file(df, f"{type.lower()}_stats", RAW_DATA_DIR, overwrite=force)
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
            raise
    return [f"{type.lower()}_stats.parquet" for type in tracking_type]


def format_shot_locations(response):
    results = response["resultSets"]
    if isinstance(results, list):
        results = results[0]
    headers = results["headers"]
    zone_info = headers[0]
    column_info = headers[1]
    zone_names = {
        "Restricted Area": "RA",
        "In The Paint (Non-RA)": "PAINT_NON_RA",
        "Mid-Range": "MIDRANGE",
        "Left Corner 3": "LEFT_CORNER_3",
        "Right Corner 3": "RIGHT_CORNER_3",
        "Above the Break 3": "ABOVE_BREAK_3",
        "Backcourt": "BACKCOURT",
    }
    if (zone_info["columnNames"] != list(zone_names) or zone_info["columnSpan"] != 3):
        raise ValueError("Unexpected shot-location format.")
    num_player_cols = zone_info["columnsToSkip"]
    columns = column_info["columnNames"][:num_player_cols]
    for zone in zone_info["columnNames"]:
        for stat in ["FGM", "FGA", "FG_PCT"]:
            columns.append(f"{zone_names[zone]}_{stat}")
    if len(columns) != len(column_info["columnNames"]):
        raise ValueError("Shot-location columns do not match.")
    return pd.DataFrame(results["rowSet"], columns=columns)


def get_shot_location_stats(force=False) -> Path:
    """
    Retrieves shot location stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "shot_locations.parquet").exists():
        print("shot_locations.parquet already exists. Skipping download.")
        return RAW_DATA_DIR / "shot_locations.parquet"
    
    response = leaguedashplayershotlocations.LeagueDashPlayerShotLocations(
        measure_type_simple="Base",
        per_mode_detailed="Totals",
        distance_range="By Zone",
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        timeout=60
    )
    df = format_shot_locations(response.get_dict())
    validate_api_data(df, required_columns=["PLAYER_ID", "PLAYER_NAME", "RA_FGA"])
    return save_parquet_file(df, "shot_locations", RAW_DATA_DIR, overwrite=force)


def get_hustle_stats(force=False) -> Path:
    """
    Retrieves hustle stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "hustle_stats.parquet").exists():
        print("hustle_stats.parquet already exists. Skipping download.")
        return RAW_DATA_DIR / "hustle_stats.parquet"

    df = leaguehustlestatsplayer.LeagueHustleStatsPlayer(
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        per_mode_time="Totals",
        timeout=60
        ).get_data_frames()[0]
    validate_api_data(df, required_columns=["PLAYER_ID", "PLAYER_NAME"])
    return save_parquet_file(df, "hustle_stats", RAW_DATA_DIR, overwrite=force)


def get_matchup_stats(force=False) -> Path:
    """
    Retrieves matchup stats from the NBA API and saves them as a Parquet file.
    
    Args:
        force (bool): If True, forces the retrieval of data even if it already exists. Default is False.
    """
    if not force and (RAW_DATA_DIR / "matchup_stats.parquet").exists():
        print("matchup_stats.parquet already exists. Skipping download.")
        return RAW_DATA_DIR / "matchup_stats.parquet"

    df = leagueseasonmatchups.LeagueSeasonMatchups(
        season=SEASON,
        season_type_playoffs=SEASON_TYPE,
        per_mode_simple="Totals",
        league_id="00",
        timeout=60
        ).get_data_frames()[0]
    validate_api_data(df, required_columns=["OFF_PLAYER_ID", "DEF_PLAYER_ID", "PARTIAL_POSS"], id_columns=("OFF_PLAYER_ID", "DEF_PLAYER_ID"), unique=False)
    return save_parquet_file(df, "matchup_stats", RAW_DATA_DIR, overwrite=force)