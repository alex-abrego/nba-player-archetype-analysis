import pandas as pd


def check_unique_ids(df: pd.DataFrame, id: str) -> bool:
    """
    Checks if the specified key column has only unique values in the DataFrame. Raises an error if duplicates are found.
    
    Args:
        df (pd.DataFrame): The DataFrame to check.
        id (str): The column name to check for uniqueness.

    Returns:
        bool
    """
    return df[id].is_unique
    

def check_required_cols(df: pd.DataFrame, required: list[str]) -> bool:
    for column in required:
        if column not in df.columns:
            return False
    return True


def validate_api_data(df, required_columns, id_columns=("PLAYER_ID",), unique=True):
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
                    "missing_percentage": round(missing_pct, 2)
                })
    mv_report = pd.DataFrame(mv_report, columns=["dataset", "column", "missing_percentage"])
    mv_report = mv_report.sort_values(by=["dataset", "missing_percentage"], ascending=[True, False]).reset_index(drop=True)
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


