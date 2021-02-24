from typing import Tuple, Union

import numpy as np
import pandas as pd

from loguru import logger

# ----- Miscellaneous Utilites ----- #


def get_magnitude(value: float) -> int:
    """Return the determined magnitude of the provided value."""
    return int(np.floor(np.log10(np.abs(value))))


def get_scaled_values_and_magnitude_string(
    values_array: Union[pd.DataFrame, np.ndarray], force_magnitude: float = None
) -> Tuple[Union[pd.DataFrame, np.ndarray], str]:
    """
    Conveniently scale provided values to the best determined magnitude. Returns scaled values
    and the magnitude string to use in plots labels.

    Args:
        values_array (Union[pd.DataFrame, np.ndarray]): vectorised structure containing the
            values to scale.
        force_magnitude (float0: a specific magnitude value to use for the scaling, if desired.

    Returns:
        A tuple of the scaled values (same type as the provided ones) and the string to use for
        the scale in plots labels and legends.

    Usage:
    """
    magnitude = get_magnitude(max(values_array)) if force_magnitude is None else force_magnitude
    applied_magnitude = -magnitude
    logger.trace(f"Scaling data by {applied_magnitude} orders of magnitude")
    scaled_values = values_array * (10 ** applied_magnitude)
    magnitude_string = "{" + f"{applied_magnitude}" + "}"
    return scaled_values, magnitude_string
