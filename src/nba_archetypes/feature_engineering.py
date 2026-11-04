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