"""
.. _maths-utils:

Utilities
---------

Module with utility functions used throughout the `~.maths.nonconvex_phase_sync`
and `~.maths.stats_fitting` modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from loguru import logger

if TYPE_CHECKING:
    import pandas as pd

# ----- Miscellaneous Utilites ----- #


def get_magnitude(value: float) -> int:
    """
    .. versionadded:: 0.8.2

    Returns the determined magnitude of the provided *value*. This
    corresponds to the power of 10 that would be necessary to reduce
    *value* to a :math:`X \\cdot 10^{n}` form. In this case, *n* is
    the result.

    Parameters
    ----------
    value : float
        Value to determine the magnitude of.

    Returns
    -------
    int
        The magnitude of the provided *value*, as an `int`.

    Examples
    --------

        .. code-block:: python

            get_magnitude(10)
            # returns 1

        .. code-block:: python

            get_magnitude(0.0311)
            # returns -2

        .. code-block:: python

            get_magnitude(1e-7)
            # returns -7
    """
    return int(np.floor(np.log10(np.abs(value))))


def get_scaled_values_and_magnitude_string(
    values_array: pd.DataFrame | np.ndarray, force_magnitude: float | None = None
) -> tuple[pd.DataFrame | np.ndarray, str]:
    """
    .. versionadded:: 0.8.2

    Conveniently scales the provided values to the best determined
    magnitude, and returns the scaled values and the magnitude string
    to use in plots labels.

    Parameters
    ----------
    values_array : Union[pd.DataFrame, np.ndarray]
        Vectorised structure containing the values to scale.
    force_magnitude : float, optional
        A specific magnitude value to use for the scaling, if desired.

    Returns
    -------
    tuple[pandas.DataFrame | numpy.ndarray, str]
        A `tuple` of the scaled values (same type as the provided ones)
        and the string to use for the scale in plots labels and legends.

    Example
    -------
        .. code-block:: python

            import numpy as np

            q = np.array([-330, 230, 430, -720, 750, -110, 410, -340, -950, -630])
            get_scaled_values_and_magnitude_string(q)
            # returns (array([-3.3,  2.3,  4.3, -7.2,  7.5, -1.1,  4.1, -3.4, -9.5, -6.3]), '{-2}')
    """
    magnitude = get_magnitude(max(values_array)) if force_magnitude is None else force_magnitude
    applied_magnitude = -magnitude
    logger.trace(f"Scaling data by {applied_magnitude} orders of magnitude")
    scaled_values = values_array * (10**applied_magnitude)
    magnitude_string = "{" + f"{applied_magnitude}" + "}"
    return scaled_values, magnitude_string
