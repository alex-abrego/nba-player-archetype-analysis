import pandas as pd
from pathlib import Path
from time import sleep
from datetime import datetime, timezone
from nba_archetypes.config import SEASON, SEASON_TYPE, RAW_DATA_DIR, METADATA_DIR
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
     Convert an existing CSV dataset into Parquet format.

    Reads a CSV file from the raw data directory and saves it as a Parquet file in the specified destination directory.

    Args:
        csv_file_name (str): Source filename without the .csv extension.
        parquet_file_name (str): Output filename without the .parquet extension.
        target_dir (Path): Directory where the Parquet file will be saved.

    Returns:
        None. Saves the converted file and prints a confirmation.
    """
    df = pd.read_csv(RAW_DATA_DIR / f"{csv_file_name}.csv")
    save_parquet_file(df, parquet_file_name, target_dir)

    print(f"Converted {parquet_file_name} to Parquet: {len(df)} rows and {len(df.columns)} columns")


def save_parquet_file(df: pd.DataFrame, file_name: str, target_dir: Path, overwrite: bool = False) -> Path:
    """
    Save a pandas DataFrame as a Parquet file.

    Creates the destination directory if necessary and writes to a temporary file before replacing the destination. Existing files
    are protected unless overwriting is explicitly allowed.

    Args:
        df (pd.DataFrame): DataFrame containing the data to save.
        file_name (str): Output filename without the .parquet extension.
        target_dir (Path): Directory where the file will be saved.
        overwrite (bool): Whether to replace an existing file. Defaults to False.

    Returns:
        Path: Location of the saved Parquet file.

    Raises:
        FileExistsError: If the destination already exists and overwrite is False.
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
    Save a pandas DataFrame as a CSV file.

    Creates the destination directory if necessary and writes to a temporary file before replacing the destination. Existing files
    are protected unless overwriting is explicitly allowed.

    Args:
        df (pd.DataFrame): DataFrame containing the data to save.
        file_name (str): Output filename without the .csv extension.
        target_dir (Path): Directory where the file will be saved.
        overwrite (bool): Whether to replace an existing file. Defaults to False.

    Returns:
        Path: Location of the saved CSV file.

    Raises:
        FileExistsError: If the destination already exists and overwrite is False.
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


def record_source(file_path: Path, endpoint: str, measure_type: str = "", distance_range: str = "") -> None:
    """
    Record the collection details of a downloaded NBA dataset.

    Adds or updates an entry in source_manifest.csv to document the dataset's source, API endpoint, season, collection settings,
    timestamp, and file size.

    Args:
        file_path (Path): Location of the successfully saved dataset.
        endpoint (str): NBA API endpoint used to collect the data.
        measure_type (str): Statistical measure requested, if applicable.
        distance_range (str): Shot-distance grouping, if applicable.

    Returns:
        None. Creates or updates the source manifest CSV file.
    """
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = METADATA_DIR / "source_manifest.csv"

    record = {
        "file": file_path.name,
        "source": "NBA Stats API via nba_api",
        "endpoint": endpoint,
        "season": SEASON,
        "season_type": SEASON_TYPE,
        "per_mode": "Totals",
        "measure_type": measure_type,
        "distance_range": distance_range,
        "collected_at_utc": datetime.now(
            timezone.utc
        ).isoformat(timespec="seconds"),
        "file_size_bytes": file_path.stat().st_size,
    }

    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)

        if not set(record).issubset(manifest.columns):
            manifest = pd.DataFrame(columns=record.keys())
        else:
            manifest = manifest[
                manifest["file"] != file_path.name
            ]
    else:
        manifest = pd.DataFrame(columns=record.keys())

    manifest = pd.concat(
        [manifest, pd.DataFrame([record])],
        ignore_index=True,
    )

    manifest.to_csv(manifest_path, index=False)


def get_player_stats(measure_type: list[str] | None = None, force: bool = False) -> list[str]:
    """
     Download traditional and advanced NBA player statistics.

    Retrieves the selected statistical categories from the NBA Stats API, validates the returned data, and saves each dataset as a
    Parquet file. Records collection metadata for new downloads.

    Existing files are skipped unless a refresh is requested.

    Args:
        measure_type (list[str] | None): Statistical categories to collect. Defaults to Base, Advanced, Scoring, and Usage.
        force (bool): Whether to download and replace existing datasets. Defaults to False.

    Returns:
        list[str]: Filenames of the requested Parquet datasets.
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
            file_path = save_parquet_file(df, f"{type.lower()}_stats", RAW_DATA_DIR, overwrite=force)
            record_source(file_path, endpoint="LeagueDashPlayerStats", measure_type=type)
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
            raise
    return [f"{type.lower()}_stats.parquet" for type in measure_type]


def get_tracking_stats(tracking_type: list[str] | None = None, force = False) -> list[str]:
    """
     Download NBA player tracking statistics.

    Retrieves the selected tracking categories from the NBA Stats API, validates player identifiers, and saves each dataset as a
    Parquet file. Records collection metadata for new downloads.

    Existing files are skipped unless a refresh is requested.

    Args:
        tracking_type (list[str] | None): Tracking categories to collect. Defaults to the ten tracking categories used in this project.
        force (bool): Whether to download and replace existing datasets. Defaults to False.

    Returns:
        list[str]: Filenames of the requested Parquet datasets.
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
            file_path = save_parquet_file(df, f"{type.lower()}_stats", RAW_DATA_DIR, overwrite=force)
            record_source(file_path, endpoint="LeagueDashPtStats", measure_type=type)
            sleep(1.5)
        except Exception as e:
            print(f"Error occurred while collecting {type} stats: {e}")
            raise
    return [f"{type.lower()}_stats.parquet" for type in tracking_type]


def format_shot_locations(response):
    """
    Convert NBA shot-location API results into a structured DataFrame.

    Reads the API's hierarchical column headers and creates flat, descriptive names for each shooting zone and statistic.

    Supports the recognized shooting zones and preserves all player records without removing rows.

    Args:
        response (dict): Raw response returned by the NBA shot-location endpoint using get_dict().

    Returns:
        pd.DataFrame: Player-level shooting statistics with standardized column names.

    Raises:
        ValueError: If the response contains an unexpected shooting-zone structure or inconsistent column counts.
    """
    results = response["resultSets"]
    if isinstance(results, list):
        results = results[0]
    zone_info, column_info = results["headers"]

    zone_names = {
        "Restricted Area": "RA",
        "In The Paint (Non-RA)": "PAINT_NON_RA",
        "Mid-Range": "MIDRANGE",
        "Left Corner 3": "LEFT_CORNER_3",
        "Right Corner 3": "RIGHT_CORNER_3",
        "Above the Break 3": "ABOVE_BREAK_3",
        "Backcourt": "BACKCOURT",
        "Corner 3": "CORNER_3"
    }
    zones = zone_info["columnNames"]
    if (
        zone_info["columnSpan"] != 3
        or len(zones) != len(set(zones))
        or not set(zones).issubset(zone_names)
        or len(zones) not in (7, 8)
    ):
        raise ValueError("Unexpected shot-location format.")
    
    num_player_cols = zone_info["columnsToSkip"]
    columns = column_info["columnNames"][:num_player_cols].copy()
    for zone in zones:
        for stat in ["FGM", "FGA", "FG_PCT"]:
            columns.append(f"{zone_names[zone]}_{stat}")
    if len(columns) != len(column_info["columnNames"]):
        raise ValueError("Shot-location columns do not match.")
    return pd.DataFrame(results["rowSet"], columns=columns)


def get_shot_location_stats(force=False) -> Path:
    """
    Download NBA player shot-location statistics.

    Retrieves shooting statistics by court zone, converts the API response into a structured DataFrame, and validates the result
    before saving it as a Parquet file.

    Records the collection settings in the source manifest. Existing data are reused unless a refresh is requested.

    Args:
        force (bool): Whether to download and replace the existing shot-location dataset. Defaults to False.

    Returns:
        Path: Location of the saved or previously cached Parquet file.
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
    file_path = save_parquet_file(df, "shot_locations", RAW_DATA_DIR, overwrite=force)
    record_source(file_path, endpoint="LeagueDashPlayerShotLocations", measure_type="Base", distance_range="By Zone")
    return file_path


def get_hustle_stats(force=False) -> Path:
    """
    Download NBA player hustle statistics.

    Retrieves season-level hustle statistics from the NBA Stats API, validates the returned player data, and saves the results as a
    Parquet file.

    Records collection metadata and reuses existing data unless a refresh is requested.

    Args:
        force (bool): Whether to download and replace the existing hustle dataset. Defaults to False.

    Returns:
        Path: Location of the saved or previously cached Parquet file.
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
    file_path = save_parquet_file(df, "hustle_stats", RAW_DATA_DIR, overwrite=force)
    record_source(file_path, endpoint="LeagueHustleStatsPlayer")
    return file_path


def get_matchup_stats(force=False) -> Path:
    """
     Download NBA player matchup statistics.

    Retrieves season-level offensive and defensive player matchups from the NBA Stats API and validates the required columns.

    Unlike other datasets, matchup data contain multiple observations per player because players face different opponents throughout
    the season. Duplicate player identifiers are therefore allowed.

    Args:
        force (bool): Whether to download and replace the existing matchup dataset. Defaults to False.

    Returns:
        Path: Location of the saved or previously cached Parquet file.
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
    file_path = save_parquet_file(df, "matchup_stats", RAW_DATA_DIR, overwrite=force)
    record_source(file_path, endpoint="LeagueSeasonMatchups")
    return file_path