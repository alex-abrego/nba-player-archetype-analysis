import pandas as pd


def check_unique_ids(df: pd.DataFrame, id: str) -> bool:
    """
    Check whether a DataFrame contains unique player identifiers.

    Args:
        df (pd.DataFrame): Dataset to validate.
        id (str): Name of the identifier column to check.

    Returns:
        bool: True if all values in the column are unique. False if duplicates are present.
    """
    return df[id].is_unique
    

def check_required_cols(df: pd.DataFrame, required: list[str]) -> bool:
    """
    Check whether a dataset contains all required columns.

    Args:
        df (pd.DataFrame): Dataset to validate.
        required (list[str]): Column names expected in the dataset.

    Returns:
        bool: True if every required column exists. False if one or more columns are missing.
    """
    for column in required:
        if column not in df.columns:
            return False
    return True


def validate_api_data(df, required_columns, id_columns=("PLAYER_ID",), unique=True):
    """
    Validate an NBA API dataset before saving it.

    Checks that the dataset is not empty, contains all required columns, and has no missing values in its identifier columns.

    By default, also checks that player identifiers are unique. This uniqueness requirement can be disabled for datasets
    containing multiple observations per player, such as matchups.

    Args:
        df (pd.DataFrame): Dataset returned by the NBA API.
        required_columns (list[str]): Columns required for the dataset.
        id_columns (tuple[str, ...]): Identifier columns to validate. Defaults to ("PLAYER_ID",).
        unique (bool): Whether to require unique values in the first identifier column. Defaults to True.

    Returns:
        None. Completes without an error when validation succeeds.

    Raises:
        ValueError: If the dataset is empty, required columns are missing, identifier values are missing, or duplicate
            identifiers are found when uniqueness is required.
    """
    if df.empty:
        raise ValueError("The API returned an empty dataset.")
    if not check_required_cols(df, list(required_columns) + list(id_columns)):
        raise ValueError("The dataset is missing required columns.")
    for column in id_columns:
        if df[column].isna().any():
            raise ValueError(f"{column} contains missing values.")
    if unique:
        if not check_unique_ids(df, id_columns[0]):
            raise ValueError("Duplicate player IDs found.")


def dataset_inventory(datasets: dict[str, pd.DataFrame]):
    """
    Generate a summary inventory of collected datasets.

    Calculates the number of rows, columns, and total missing values for each dataset.

    Args:
        datasets (dict[str, pd.DataFrame]): Dictionary mapping dataset names to their corresponding DataFrames.

    Returns:
        pd.DataFrame: Summary table containing the dataset name, row count, column count, and total missing values.
    """
    inventory = []

    for dataset_name, df in datasets.items():
        inventory.append({
            "dataset": dataset_name,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": df.isna().sum().sum()
        })

    inventory = pd.DataFrame(inventory)
    return inventory


def missing_value_report(datasets: dict[str, pd.DataFrame]):
    """
    Generate a missing-value report for collected datasets.

    Identifies columns containing missing values and calculates the percentage of missing observations in each column.
    Columns without missing values are excluded from the report.

    Args:
        datasets (dict[str, pd.DataFrame]): Dictionary mapping dataset names to their corresponding DataFrames.

    Returns:
        pd.DataFrame: Report containing the dataset name, column name, and percentage of missing values, sorted by dataset and missingness.
    """
    mv_report = []
    for dataset_name, df in datasets.items():
        total_rows = len(df)
        missing_counts = df.isna().sum()

        for col, missing_count in missing_counts.items():
            if missing_count > 0:
                missing_pct = (missing_count / total_rows) * 100
                mv_report.append({
                    "dataset": dataset_name,
                    "column": col,
                    "missing_percentage": round(missing_pct, 2)
                })
    mv_report = pd.DataFrame(mv_report, columns=["dataset", "column", "missing_percentage"])
    mv_report = mv_report.sort_values(by=["dataset", "missing_percentage"], ascending=[True, False]).reset_index(drop=True)
    return mv_report


def player_coverage_report(datasets: dict[str, pd.DataFrame], eligible_players: pd.DataFrame) -> pd.DataFrame:
    """
    Measure eligible-player coverage across player-level datasets.

    Compares the eligible player population with the player IDs available in each dataset and calculates the percentage of
    eligible players represented.

    This function is intended for datasets with a PLAYER_ID column. Matchup data should be evaluated separately because they contain
    multiple player identifiers and a different observation structure.

    Args:
        datasets (dict[str, pd.DataFrame]): Dictionary of player-level datasets to evaluate.
        eligible_players (pd.DataFrame): DataFrame containing the eligible player population and their PLAYER_ID values.

    Returns:
        pd.DataFrame: Dataset names and their eligible-player coverage percentages, sorted from highest to lowest coverage.
    """
    coverage_report = []
    eligible_ids = set(eligible_players["PLAYER_ID"])
    if not eligible_ids:
        raise ValueError("Eligible player dataset is empty.")

    for name, df in datasets.items():
        dataset_ids = set(df["PLAYER_ID"])
        coverage_percentage = len((eligible_ids.intersection(dataset_ids))) / len(eligible_ids) * 100
        coverage_report.append({
            "dataset": name,
            "coverage_percentage": coverage_percentage
        })

    coverage_report = pd.DataFrame(coverage_report).sort_values("coverage_percentage", ascending=False)
    return coverage_report


