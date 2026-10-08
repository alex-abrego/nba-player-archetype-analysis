import pandas as pd
from nba_archetypes.config import METADATA_DIR

def summarize_data(df: pd.DataFrame) -> None:
    """
    Prints a summary of the DataFrame, including the number of rows, columns, and missing values.
    """
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")
    print(f"Missing values: {df.isna().sum().sum():,}")
    

def check_unique_key(df: pd.DataFrame, key: str) -> None:
    """
    Checks if the specified key column has only unique values in the DataFrame. Raises an error if duplicates are found.
    
    Args:
        df (pd.DataFrame): The DataFrame to check.
        key (str): The name of the column to check for purely unique values.
    """
    if not df[key].is_unique:
        raise ValueError(f"Duplicate values found in the {key} column.")
    

def player_coverage_report(datasets: dict[str, pd.DataFrame], eligible_players: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a player coverage report by comparing the percentage of eligible players present in each dataset.
    
    Args:
        datasets (dict[str, pd.DataFrame]): A dictionary of dataset names and their corresponding DataFrames.
        eligible_players (pd.DataFrame): A DataFrame containing the list of eligible players.
    """
    coverage_report = pd.DataFrame(columns=["dataset", "total_eligible", "dataset_count", "coverage_percentage"])

    total_eligible = len(eligible_players)
    for name, df in datasets.items():
        dataset_count = df["PLAYER_ID"].nunique()
        coverage_percentage = (dataset_count / total_eligible) * 100
        coverage_report = coverage_report.append({
            "dataset": name,
            "total_eligible": total_eligible,
            "dataset_count": dataset_count,
            "coverage_percentage": coverage_percentage
        }, ignore_index=True)

    coverage_report.sort_values("coverage_percentage", ascending=False)
    coverage_report.to_csv(METADATA_DIR / "player_coverage_report.csv", index=False)
    return coverage_report