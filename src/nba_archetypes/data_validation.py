import pandas as pd
from nba_archetypes.config import METADATA_DIR


def check_unique_ids(df: pd.DataFrame, key="PLAYER_ID") -> None:
    """
    Checks if the specified key column has only unique values in the DataFrame. Raises an error if duplicates are found.
    
    Args:
        df (pd.DataFrame): The DataFrame to check.
        key (str): The column name to check for uniqueness. Defaults to "PLAYER_ID".

    Returns:
        None. Raises an error if duplicates are found.
    """
    if not df[key].is_unique:
        raise ValueError(f"Duplicate values found in the {key} column.")
    

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
        dataset_ids = set(df[[col for col in df.columns if "PLAYER_ID" in str(col)][0]])
        coverage_percentage = len((eligible_ids.intersection(dataset_ids))) / len(eligible_ids) * 100
        coverage_report.append({
            "dataset": name,
            "coverage_percentage": coverage_percentage
        })

    coverage_report = pd.DataFrame(coverage_report)
    coverage_report.sort_values("coverage_percentage", ascending=False)
    return coverage_report

