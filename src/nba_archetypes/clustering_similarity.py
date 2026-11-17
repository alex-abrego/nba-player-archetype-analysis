
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


OFFENSE_FEATURES = [
    "BALL_DOMINANCE_SCORE",
    "PLAYMAKING_SCORE",
    "BALL_MOVEMENT_SCORE",
    "RIM_PRESSURE_SCORE",
    "ON_BALL_CREATION_SCORE",
    "PERIMETER_SHOOTING_SCORE",
    "INTERIOR_OFFENSE_SCORE",
    "OFFENSIVE_REBOUNDING_SCORE",
]


def fit_offensive_clusters(players: pd.DataFrame):
    """Fit the selected seven-cluster offensive style model."""

    required = [
        "PLAYER_ID",
        "PLAYER_NAME",
        *OFFENSE_FEATURES,
    ]

    missing = [
        col for col in required
        if col not in players.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if players["PLAYER_ID"].duplicated().any():
        raise ValueError("Duplicate player IDs found.")

    X = players[OFFENSE_FEATURES].to_numpy(
        dtype=float
    )

    if not np.isfinite(X).all():
        raise ValueError(
            "Offensive features contain missing or infinite values."
        )

    model = KMeans(
        n_clusters=7,
        random_state=28,
        n_init=20,
    )

    labels = model.fit_predict(X)

    assignments = players[
        ["PLAYER_ID", "PLAYER_NAME"]
    ].copy()

    assignments["OFFENSIVE_CLUSTER"] = labels
    return model, assignments


OFFENSIVE_ARCHETYPE_NAMES = {
    0: "Interior Finishers & Rebounders",
    1: "Secondary Shot Creators",
    2: "Complementary Support Players",
    3: "Perimeter Spacers",
    4: "Primary Offensive Engines",
    5: "Interior-Oriented Creators",
    6: "Ball-Movement Facilitators",
}


def add_archetype_names(assignments: pd.DataFrame):
    """Attach descriptive labels to offensive clusters."""

    result = assignments.copy()

    result["OFFENSIVE_ARCHETYPE"] = (
        result["OFFENSIVE_CLUSTER"].map(
            OFFENSIVE_ARCHETYPE_NAMES
        )
    )

    if result["OFFENSIVE_ARCHETYPE"].isna().any():
        raise ValueError("Unrecognized offensive cluster.")
    return result


def similar_players(players, player_id, top_n=10):
    """Find the nearest offensive-style neighbors."""
    required = ["PLAYER_ID", "PLAYER_NAME", *OFFENSE_FEATURES]
    missing = [col for col in required if col not in players]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if not players["PLAYER_ID"].is_unique:
        raise ValueError("Duplicate player IDs found.")

    if not isinstance(top_n, (int, np.integer)) or not 1 <= top_n < len(players):
        raise ValueError("Invalid top_n.")
    
    X = players[OFFENSE_FEATURES].to_numpy(dtype=float)

    if not np.isfinite(X).all():
        raise ValueError("Non-finite offensive features.")

    matches = np.flatnonzero(
        players["PLAYER_ID"].to_numpy() == player_id
    )

    if len(matches) != 1:
        raise ValueError("Player ID not found.")

    idx = matches[0]

    distances = np.sqrt(
        np.mean((X - X[idx]) ** 2, axis=1)
    )

    # Exclude the player being compared.
    distances[idx] = np.inf

    nearest = np.argsort(distances)[:top_n]

    columns = ["PLAYER_ID", "PLAYER_NAME"]

    if "OFFENSIVE_ARCHETYPE" in players.columns:
        columns.append("OFFENSIVE_ARCHETYPE")

    result = players.iloc[nearest][columns].copy()
    result["OFFENSIVE_DISTANCE"] = distances[nearest]

    return result.reset_index(drop=True)


def explain_similarity(players, player_id_a, player_id_b):
    """Explain the distance between two offensive profiles."""
    required = ["PLAYER_ID", *OFFENSE_FEATURES]
    missing = [col for col in required if col not in players]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if not players["PLAYER_ID"].is_unique:
        raise ValueError("Duplicate player IDs found.")
    
    X = players[OFFENSE_FEATURES].to_numpy(dtype=float)

    if not np.isfinite(X).all():
        raise ValueError("Non-finite offensive features.")
    
    ids = players["PLAYER_ID"].to_numpy()

    a_matches = np.flatnonzero(ids == player_id_a)
    b_matches = np.flatnonzero(ids == player_id_b)

    if len(a_matches) != 1 or len(b_matches) != 1:
        raise ValueError("Player ID not found.")

    a = X[a_matches[0]]
    b = X[b_matches[0]]

    differences = np.abs(a - b)
    contributions = differences ** 2 / len(OFFENSE_FEATURES)

    distance = np.sqrt(contributions.sum())

    result = pd.DataFrame({
        "DIMENSION": OFFENSE_FEATURES,
        "PLAYER_A": a,
        "PLAYER_B": b,
        "ABSOLUTE_DIFFERENCE": differences,
        "DISTANCE_CONTRIBUTION": contributions,
    })

    result["DISTANCE_SHARE"] = (
        contributions / distance**2
        if distance > 0
        else 0.0
    )

    result = result.sort_values(
        "DISTANCE_CONTRIBUTION",
        ascending=False,
    )

    return distance, result.reset_index(drop=True)
