import numpy as np

def safe_divide(numerator, denominator):
    """ Safely divide two pandas Series, handling division by zero. """

    denominator = denominator.replace(0, np.nan)
    result = numerator / denominator
    
    return result.replace([np.inf, -np.inf], np.nan)