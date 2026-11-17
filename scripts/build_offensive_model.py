from pathlib import Path
import joblib
import pandas as pd

from nba_archetypes.config import(PROCESSED_DATA_DIR)
from nba_archetypes.clustering_similarity import (
    OFFENSE_FEATURES,
    OFFENSIVE_ARCHETYPE_NAMES,
    fit_offensive_clusters,
    add_archetype_names,
)

features_filename = "player_style_features.parquet"

def main():
    features_path = PROCESSED_DATA_DIR / features_filename

    # 1. Load previously engineered player features.
    players = pd.read_parquet(features_path)

    # Input must contain the eligible, standardized
    # offensive player dataset used in our experiment.

    # 2. Fit our selected model.
    model, assignments = fit_offensive_clusters(
        players
    )

    assignments = add_archetype_names(assignments)

    # 3. Calculate cluster profiles.
    combined = players[
        ["PLAYER_ID", *OFFENSE_FEATURES]
    ].merge(
        assignments[
            [
                "PLAYER_ID",
                "OFFENSIVE_CLUSTER",
                "OFFENSIVE_ARCHETYPE",
            ]
        ],
        on="PLAYER_ID",
        validate="one_to_one",
    )

    profiles = (
        combined.groupby(
            ["OFFENSIVE_CLUSTER", "OFFENSIVE_ARCHETYPE"]
        )
        .agg(
            PLAYER_COUNT=("PLAYER_ID", "size"),
            **{
                feature: (feature, "mean")
                for feature in OFFENSE_FEATURES
            },
        )
        .reset_index()
    )

    # 4. Save outputs.
    assignments.to_parquet(
        PROCESSED_DATA_DIR / "offensive_clustering_assignments.parquet",
        index=False,
    )

    profiles.to_parquet(
        PROCESSED_DATA_DIR / "offensive_profiles.parquet",
        index=False,
    )

    joblib.dump(
        {
            "model": model,
            "features": OFFENSE_FEATURES,
            "archetype_names": OFFENSIVE_ARCHETYPE_NAMES,
        },
        PROCESSED_DATA_DIR / "offensive_kmeans.joblib",
    )

    print("Offensive model saved successfully.")

    print("\nCluster sizes:")
    print(
        assignments.groupby(
            ["OFFENSIVE_CLUSTER", "OFFENSIVE_ARCHETYPE"]
        ).size()
    )


if __name__ == "__main__":
    main()
