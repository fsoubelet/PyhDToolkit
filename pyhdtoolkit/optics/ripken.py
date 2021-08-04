from typing import Union

import numpy as np

from loguru import logger

# ----- Setup Utilites ----- #


def lebedev_beam_size(
    beta1_: Union[float, np.ndarray], beta2_: Union[float, np.ndarray], geom_emit_x: float, geom_emit_y: float
) -> Union[float, np.ndarray]:
    """
    Calculate beam size according to the Lebedev-bogacz formula, based on the Ripken-Mais
    Twiss parameters. The implementation is that of Eq. (A.3.1) in FERMILAB-PUB-10-383-AD, avaliable at the
    following link: https://arxiv.org/ftp/arxiv/papers/1207/1207.5526.pdf

    Args:
        beta1_ (Union[float, np.ndarray]): value(s) for the beta1x or beta1y Ripken parameter.
        beta2_ (Union[float, np.ndarray]): value(s) for the beta2x or beta2y Ripken parameter.
        geom_emit_x (float): geometric emittance of the horizontal plane.
        geom_emit_y (float): geometric emittante of the vertical plane.

    Returns:
        The beam size (horizontal or vertical) according to Lebedev & Bogacz, as sqrt(epsx *
        beta1_^2 + epsy * beta2_^2).
    """
    logger.trace("Computing beam size according to Lebedev formula: sqrt(epsx * b1_^2 + epsy * b2_^2)")
    return np.sqrt(geom_emit_x * beta1_ + geom_emit_y * beta2_)


def _beam_size(coordinates_distribution: np.ndarray, method: str = "std") -> float:
    """
    Compute beam size from particle coordinates.

    Args:
        coordinates_distribution (np.ndarray): ensemble of coordinates of the particle distributon.
        method (str): the method of calculation to use, either 'std' (using the standard deviation as the
            beam size) or 'rms' (root mean square).

    Returns:
        The computed beam size.
    """
    if method == "std":
        return coordinates_distribution.std()
    elif method == "rms":
        return np.sqrt(np.mean(np.square(coordinates_distribution)))
    raise NotImplementedError(f"Invalid method provided")
