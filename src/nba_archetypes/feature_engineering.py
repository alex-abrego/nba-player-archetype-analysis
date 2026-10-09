import numpy as np
import pandas as pd

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