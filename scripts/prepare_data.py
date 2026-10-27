import pandas as pd
import duckdb

from nba_archetypes.config import (
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    METADATA_DIR,
    SQL_DIR,
    MIN_MINUTES,
)

from nba_archetypes.data_validation import (dataset_inventory, missing_value_report)

from nba_archetypes.data_collection import (save_parquet_file, save_csv_file)

def main():
    # Loads collected datasets.
    datasets = {}

    for file in sorted(RAW_DATA_DIR.glob("*.parquet")):
        datasets[file.stem] = pd.read_parquet(file)

    for name in ["base_stats", "advanced_stats"]:
        if name not in datasets:
            raise FileNotFoundError(f"Missing dataset: {name}")

    # Executes eligible players SQL query.
    core_data = {
    "base_stats": (RAW_DATA_DIR / "base_stats.parquet"),
    "advanced_stats": (RAW_DATA_DIR / "advanced_stats.parquet")
    }

    sql_query = (SQL_DIR / "01_eligible_players.sql").read_text()

    with duckdb.connect() as con:
        for view_name, file_path in core_data.items():
            con.execute(f"""
            CREATE OR REPLACE VIEW {view_name} AS
            SELECT *
            FROM read_parquet('{file_path.as_posix()}')
            """)
        eligible_players = con.execute(sql_query, {"MIN_MINUTES": MIN_MINUTES}).df()

    # Validates SQL results.
    expected_count = (datasets["base_stats"]["MIN"] >= MIN_MINUTES).sum()

    if len(eligible_players) != expected_count:
        raise ValueError("SQL join changed the player count.")

    if not eligible_players["PLAYER_ID"].is_unique:
        raise ValueError("Duplicate eligible player IDs.")

    if (
        eligible_players["POSS"].isna().any()
        or (eligible_players["POSS"] <= 0).any()
    ):
        raise ValueError("Invalid player possessions.")

    # Build data-quality reports.
    inventory = dataset_inventory(datasets)
    missing_report = missing_value_report(datasets)

    column_rows = []

    for name, df in datasets.items():
        for column in df.columns:
            column_rows.append({
                "dataset": name,
                "column": column,
            })

    column_inventory = pd.DataFrame(column_rows)

    # Save outputs.
    save_parquet_file(
        eligible_players,
        "eligible_players",
        INTERIM_DATA_DIR,
        overwrite=True,
    )

    reports = {
        "dataset_inventory": inventory,
        "missing_value_report": missing_report,
        "column_inventory": column_inventory
    }

    for name, df in reports.items():
        save_csv_file(
            df,
            name,
            METADATA_DIR,
            overwrite=True,
        )

    print("Data preparation completed successfully.")
    print("Eligible players:", len(eligible_players))


if __name__ == "__main__":
    main()
