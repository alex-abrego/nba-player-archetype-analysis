from pathlib import Path

import duckdb
import joblib
import numpy as np

from nba_archetypes.config import (RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, SQL_DIR,)

from nba_archetypes.feature_engineering import (build_dimension_scores, engineer_style_features,)


def main():
    output_dir = Path(PROCESSED_DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_tables = [
        "base_stats",
        "advanced_stats",
        "possessions_stats",
        "passing_stats",
        "drives_stats",
        "shot_locations",
        "pullupshot_stats",
        "scoring_stats",
        "catchshoot_stats",
        "painttouch_stats",
        "posttouch_stats",
        "hustle_stats",
        "rebounding_stats",
        ]

    source_paths = {name: RAW_DATA_DIR / f"{name}.parquet" for name in source_tables}

    source_paths["eligible_players"] = (INTERIM_DATA_DIR / "eligible_players.parquet")

    missing_files = [
        name for name, path in source_paths.items()
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(f"Missing Parquet files: {missing_files}")

    sql_query = (SQL_DIR / "02_style_features.sql").read_text()

    with duckdb.connect() as con:
        for view_name, file_path in source_paths.items():
            con.execute(f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT *
                FROM read_parquet('{file_path.as_posix()}')
            """)
        style_features = con.execute(sql_query).df()
        eligible_count = con.execute(
            "SELECT COUNT(*) FROM eligible_players"
        ).fetchone()[0]

    if len(style_features) != eligible_count:
        raise ValueError("SQL joins changed the eligible player count.")

    if (
        style_features["PLAYER_ID"].isna().any()
        or not style_features["PLAYER_ID"].is_unique
    ):
        raise ValueError("Invalid or duplicate PLAYER_ID values.")

    PER_100_FEATURES = {
        "TOUCHES": "TOUCHES_PER_100",
        "PASSES_MADE": "PASSES_PER_100",
        "AST_ADJ": "AST_ADJ_PER_100",
        "DRIVES": "DRIVES_PER_100",
        "RA_FGA": "RA_FGA_PER_100",
        "PULL_UP_FGA": "PULL_UP_FGA_PER_100",
        "CATCH_SHOOT_FG3A": "CATCH_SHOOT_3PA_PER_100",
        "PAINT_TOUCHES": "PAINT_TOUCHES_PER_100",
        "POST_TOUCHES": "POST_TOUCHES_PER_100",
        "SCREEN_ASSISTS": "SCREEN_ASSISTS_PER_100",
        "DEFLECTIONS": "DEFLECTIONS_PER_100",
        "CONTESTED_SHOTS_2PT": "CONTESTED_2PT_PER_100",
        "BLK": "BLK_PER_100",
        "OREB_CHANCES": "OREB_CHANCES_PER_100",
        "DREB_CHANCES": "DREB_CHANCES_PER_100",
        }

    ADJUSTMENT_FEATURES = [
        (
            "TOUCHES_PER_100",
            "PASSES_PER_100",
            "TOUCH_ADJUSTED_PASSING",
        ),
        (
            "PAINT_TOUCHES_PER_100",
            "OREB_CHANCES_PER_100",
            "PAINT_ADJUSTED_OREB",
        ),
        ]

    engineered, adjustment_models = engineer_style_features(
        style_features,
        PER_100_FEATURES,
        ADJUSTMENT_FEATURES,
        )

    STYLE_DIMENSIONS = {
        "BALL_DOMINANCE": [
            "USG_PCT",
            "TOUCHES_PER_100",
            "AVG_SEC_PER_TOUCH",
        ],
        "PLAYMAKING": [
            "AST_ADJ_PER_100",
        ],
        "BALL_MOVEMENT": [
            "TOUCH_ADJUSTED_PASSING",
        ],
        "RIM_PRESSURE": [
            "DRIVES_PER_100",
            "RA_FGA_PER_100",
        ],
        "ON_BALL_CREATION": [
            "PULL_UP_FGA_PER_100",
            "PCT_UAST_FGM",
        ],
        "PERIMETER_SHOOTING": [
            "3PA_SHARE",
            "CATCH_SHOOT_3PA_PER_100",
        ],
        "INTERIOR_OFFENSE": [
            "PAINT_TOUCHES_PER_100",
            "POST_TOUCHES_PER_100",
            "SCREEN_ASSISTS_PER_100",
        ],
        "OFFENSIVE_REBOUNDING": [
            "OREB_CHANCES_PER_100",
            "PAINT_ADJUSTED_OREB",
        ],
        "DEFENSIVE_DISRUPTION": [
            "DEFLECTIONS_PER_100",
        ],
        "PERIMETER_DEFENSE": [
            "CONTESTED_3PT_SHARE",
        ],
        "INTERIOR_DEFENSE": [
            "CONTESTED_2PT_PER_100",
            "BLK_PER_100",
        ],
        "DEFENSIVE_REBOUNDING": [
            "DREB_CHANCES_PER_100",
        ],
        }

    LOG_FEATURES = [
        "POST_TOUCHES_PER_100",
        "BLK_PER_100",
        "SCREEN_ASSISTS_PER_100",
        "OREB_CHANCES_PER_100",
        "PAINT_TOUCHES_PER_100",
        "CONTESTED_2PT_PER_100",
        "PULL_UP_FGA_PER_100",
        "DEFLECTIONS_PER_100",
        ]

    output, feature_scaler, dimension_scaler = (
        build_dimension_scores(
            engineered,
            STYLE_DIMENSIONS,
            LOG_FEATURES,
        )
    )

    clustering_columns = [
        f"{name}_SCORE"
        for name in STYLE_DIMENSIONS
    ]

    if not np.isfinite(output[clustering_columns].to_numpy()).all():
        raise ValueError("Invalid final dimension scores.")

    output.to_parquet(
        output_dir / "player_style_features.parquet",
        index=False,
    )

    joblib.dump(
        {
            "adjustment_models": adjustment_models,
            "feature_scaler": feature_scaler,
            "dimension_scaler": dimension_scaler,
            "log_features": LOG_FEATURES,
            "per_100_features": PER_100_FEATURES,
            "style_dimensions": STYLE_DIMENSIONS,
        },
        output_dir / "feature_preprocessing.joblib",
    )

    print(
        f"Saved {len(output)} player records to {output_dir}"
    )
    print(
        f"Clustering dimensions: {len(clustering_columns)}"
    )

if __name__ == "__main__":
    main()