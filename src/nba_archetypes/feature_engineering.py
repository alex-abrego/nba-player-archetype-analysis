import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """ 
    Safely divide two pandas Series, handling division by zero. 
    
    Args:
        numerator (pd.Series): The numerator Series to be divided.
        denominator (pd.Series): The denominator Series to divide by.

    Returns:
        A pandas Series containing the result of the division.
    """
    denominator = denominator.replace(0, np.nan)
    result = numerator / denominator
    
    return result.replace([np.inf, -np.inf], np.nan).fillna(0)


def per_100_calc(stat: pd.Series, possessions: pd.Series) -> pd.Series:
    """
    Converts a given statistic to a per-100 possessions basis.
    
    Args:
        stat (pd.Series): A pandas Series representing the statistic to be converted.
        possessions (pd.Series): A pandas Series representing the total number of possessions.

    Returns:
        A pandas Series containing the statistic converted to a per-100 possessions basis.
    """
    return safe_divide(stat, possessions) * 100


def engineer_style_features(raw_features: pd.DataFrame, per_100_features: dict, adjustment_features: list) -> pd.DataFrame:
    df = raw_features.copy()

    df.loc[df["CATCH_SHOOT_FG3A"].isna(), "CATCH_SHOOT_FG3A"] = 0

    for column, new_feature in per_100_features.items():
        df[new_feature] = per_100_calc(df[column], df["POSS"])

    adjustment_models = {}
    for predictor, response, output in adjustment_features:
        lm = LinearRegression()
        lm.fit(df[[predictor]], df[response])
        df[output] = df[response] - lm.predict(df[[predictor]])
        adjustment_models[output] = lm
    
    df["3PA_SHARE"] = safe_divide(df["FG3A"], df["FGA"])
    df["CONTESTED_3PT_SHARE"] = safe_divide(df["CONTESTED_SHOTS_3PT"], df["CONTESTED_SHOTS"])
    return df, adjustment_models


def build_dimension_scores(player_features: pd.DataFrame, feature_dimensions: dict, log_features: list):
    df = player_features.copy()

    feature_columns = list(dict.fromkeys(
        feature
        for columns in feature_dimensions.values()
        for feature in columns
    ))

    df[log_features] = np.log1p(df[log_features])

    feature_scaler = StandardScaler().set_output(transform="pandas")

    scaled_features = feature_scaler.fit_transform(df[feature_columns])

    composites = pd.DataFrame({
        f"{dimension}_SCORE":
            scaled_features[features].mean(axis=1)
        for dimension, features in feature_dimensions.items()
    })

    dimension_scaler = StandardScaler().set_output(transform="pandas")

    scaled_dimensions = dimension_scaler.fit_transform(composites)

    df[scaled_dimensions.columns] = scaled_dimensions

    return df, feature_scaler, dimension_scaler


POSITIONS = ["G", "F", "C"]

def calculate_matchup_diversity(
    rollup,
    min_possessions=200,
):
    """Measure diversity of recorded G/F/C matchups."""

    required = {
        "DEF_PLAYER_ID",
        "POSITION",
        "PARTIAL_POSS",
    }

    if not required.issubset(rollup.columns):
        raise ValueError("Missing matchup columns.")

    data = rollup.copy()

    data["POSITION"] = (
        data["POSITION"].astype(str).str.strip().str.upper()
    )

    data["PARTIAL_POSS"] = pd.to_numeric(
        data["PARTIAL_POSS"],
        errors="raise",
    )

    valid_positions = set(POSITIONS + ["TOTAL"])

    if not data["POSITION"].isin(valid_positions).all():
        raise ValueError("Unexpected position category.")

    if (
        data["PARTIAL_POSS"].isna().any()
        or (data["PARTIAL_POSS"] < 0).any()
    ):
        raise ValueError("Invalid matchup possessions.")

    if data.duplicated(
        ["DEF_PLAYER_ID", "POSITION"]
    ).any():
        raise ValueError("Duplicate defender-position rows.")

    # Keep the three offensive position categories.
    position_rows = data[
        data["POSITION"].isin(POSITIONS)
    ]

    counts = position_rows.pivot(
        index="DEF_PLAYER_ID",
        columns="POSITION",
        values="PARTIAL_POSS",
    )

    counts = counts.reindex(
        columns=POSITIONS
    ).fillna(0)

    # Total recorded matchup possessions.
    volume = counts.sum(axis=1)

    # Share of matchups against each position.
    shares = counts.div(
        volume.replace(0, np.nan),
        axis=0,
    ).fillna(0)

    p = shares.to_numpy()

    # Handle zero shares without taking log(0).
    safe_p = np.where(p > 0, p, 1.0)

    entropy = -(p * np.log(safe_p)).sum(axis=1)
    diversity = 100 * entropy / np.log(3)

    result = shares.rename(
        columns={
            "G": "MATCHUP_SHARE_G",
            "F": "MATCHUP_SHARE_F",
            "C": "MATCHUP_SHARE_C",
        }
    ).copy()

    result["MATCHUP_POSSESSIONS"] = volume
    result["MATCHUP_DIVERSITY_RAW"] = diversity

    # Compare G/F/C totals against the endpoint's
    # supplied TOTAL row as a data-quality check.
    total_rows = data[
        data["POSITION"] == "TOTAL"
    ].set_index("DEF_PLAYER_ID")["PARTIAL_POSS"]

    result["ROLLUP_TOTAL_POSS"] = total_rows

    result["ROLLUP_COVERAGE"] = (
        result["MATCHUP_POSSESSIONS"]
        / result["ROLLUP_TOTAL_POSS"].replace(0, np.nan)
    )

    # Provisional quality thresholds.
    result["VALID_FOR_MODEL"] = (
        (result["MATCHUP_POSSESSIONS"] >= min_possessions)
        & result["ROLLUP_COVERAGE"].between(0.95, 1.05)
    )

    # Missing means insufficient or unverified evidence,
    # NOT zero defensive versatility.
    result["POSITIONAL_MATCHUP_DIVERSITY"] = (
        result["MATCHUP_DIVERSITY_RAW"].where(
            result["VALID_FOR_MODEL"]
        )
    )

    return result.reset_index()