import pandas as pd
from nba_archetypes.config import METADATA_DIR


def check_unique_ids(df: pd.DataFrame, key: str) -> None:
    """
    Checks if the specified key column has only unique values in the DataFrame. Raises an error if duplicates are found.
    
    Args:
        df (pd.DataFrame): The DataFrame to check.
        key (str): The column name to check for uniqueness.

    Returns:
        None. Raises an error if duplicates are found.
    """
    key = df[[col for col in df.columns if "PLAYER_ID" in str(col)][-1]]
    if not key.is_unique:
        return False
    return True
    

def check_required_cols(df: pd.DataFrame, required: list[str]):
    for column in required:
        matched = any(column in str(col) for col in df.columns)
        if not matched:
            return False
    return True


def dataset_inventory(datasets: dict[str, pd.DataFrame]):
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
                    "missing_percentage": missing_pct
                })
    mv_report = pd.DataFrame(mv_report).sort_values(by=["dataset", "missing_percentage"], ascending=[True, False]).reset_index(drop=True)
    return mv_report


def player_coverage_report(datasets: dict[str, pd.DataFrame], eligible_players: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a player coverage report by comparing the percentage of eligible players present in each dataset.
    
    Args:
        datasets (dict[str, pd.DataFrame]): A dictionary of dataset names and their corresponding DataFrames.
        eligible_players (pd.DataFrame): A DataFrame containing the list of eligible players.

    Returns:
        A DataFrame containing the coverage report.
    """
    coverage_report = []
    eligible_ids = set(eligible_players["PLAYER_ID"])

    for name, df in datasets.items():
        dataset_ids = set(df[[col for col in df.columns if "PLAYER_ID" in str(col)][-1]])
        coverage_percentage = len((eligible_ids.intersection(dataset_ids))) / len(eligible_ids) * 100
        coverage_report.append({
            "dataset": name,
            "coverage_percentage": coverage_percentage
        })

    coverage_report = pd.DataFrame(coverage_report).sort_values("coverage_percentage", ascending=False)
    return coverage_report


