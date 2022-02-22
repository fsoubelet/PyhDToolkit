"""
.. _optics-ripken:

Ripken Parameters
-----------------

Module implementing various calculations based on the :cite:t:`Ripken:optics:1989` optics parameters.
"""
from typing import Union

import numpy as np

from loguru import logger

# ----- Setup Utilites ----- #


def lebedev_beam_size(
    beta1_: Union[float, np.ndarray], beta2_: Union[float, np.ndarray], geom_emit_x: float, geom_emit_y: float
) -> Union[float, np.ndarray]:
    """
    Calculate beam size according to the Lebedev-Bogacz formula, based on the Ripken-Mais Twiss
    parameters. The implementation is that of Eq. (A.3.1) in :cite:t:`Lebedev:coupling:2010`.

    Args:
        beta1_ (Union[float, np.ndarray]): value(s) for the beta1x or beta1y Ripken parameter.
        beta2_ (Union[float, np.ndarray]): value(s) for the beta2x or beta2y Ripken parameter.
        geom_emit_x (float): geometric emittance of the horizontal plane, in [m].
        geom_emit_y (float): geometric emittante of the vertical plane, in [m].

    Returns:
        The beam size (horizontal or vertical) according to Lebedev & Bogacz, as
        :math:`\\sqrt{\\epsilon_x * \\beta_{1,\\_}^2 + \\epsilon_y * \\beta_{2,\\_}^2}`.
    """
    logger.trace("Computing beam size according to Lebedev formula: sqrt(epsx * b1_^2 + epsy * b2_^2)")
    return np.sqrt(geom_emit_x * beta1_ + geom_emit_y * beta2_)


def _beam_size(coordinates_distribution: np.ndarray, method: str = "std") -> float:
    """
    Computes the beam size from particle coordinates, either as the standard deviation
    or as the root mean square of the distribution.

    Args:
        coordinates_distribution (np.ndarray): ensemble of coordinates of the particle distributon.
        method (str): the method of calculation to use, either 'std' (using the standard deviation as the
            beam size) or 'rms' (root mean square).

    Returns:
        The computed beam size.

    Raises:
        NotImplementedError: If the required *method* is neither std nor rms.
    """
    if method == "std":
        return coordinates_distribution.std()
    elif method == "rms":
        return np.sqrt(np.mean(np.square(coordinates_distribution)))
    raise NotImplementedError(f"Invalid method provided")
