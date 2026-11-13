
import numpy as np
import pandas as pd


OFFENSE_COLS = [
    "BALL_DOMINANCE_SCORE",
    "PLAYMAKING_SCORE",
    "BALL_MOVEMENT_SCORE",
    "RIM_PRESSURE_SCORE",
    "ON_BALL_CREATION_SCORE",
    "PERIMETER_SHOOTING_SCORE",
    "INTERIOR_OFFENSE_SCORE",
    "OFFENSIVE_REBOUNDING_SCORE",
]

def similar_players(players, player_id, top_n=10):
    """Find the nearest offensive-style neighbors."""
    X = players

    if not 1 <= top_n < len(players):
        raise ValueError("Invalid top_n.")

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

    if "OFFENSE_ARCHETYPE" in players.columns:
        columns.append("OFFENSE_ARCHETYPE")

    result = players.iloc[nearest][columns].copy()
    result["OFFENSIVE_DISTANCE"] = distances[nearest]

    return result.reset_index(drop=True)


def explain_similarity(players, player_id_a, player_id_b):
    """Explain the distance between two offensive profiles."""
    X = players

    ids = players["PLAYER_ID"].to_numpy()

    a_matches = np.flatnonzero(ids == player_id_a)
    b_matches = np.flatnonzero(ids == player_id_b)

    if len(a_matches) != 1 or len(b_matches) != 1:
        raise ValueError("Player ID not found.")

    a = X[a_matches[0]]
    b = X[b_matches[0]]

    differences = np.abs(a - b)
    contributions = differences ** 2 / len(OFFENSE_COLS)

    distance = np.sqrt(contributions.sum())

    result = pd.DataFrame({
        "DIMENSION": OFFENSE_COLS,
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
