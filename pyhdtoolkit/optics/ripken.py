"""
.. _optics-ripken:

Ripken Parameters
-----------------

Module implementing various calculations based on the :cite:t:`Ripken:optics:1989` optics parameters.
"""
from typing import Union

import numpy as np
import tfs

from loguru import logger

# ----- Setup Utilites ----- #


def lebedev_beam_size(
    beta1_: Union[float, np.ndarray], beta2_: Union[float, np.ndarray], geom_emit_x: float, geom_emit_y: float
) -> Union[float, np.ndarray]:
    """
    .. versionadded:: 0.8.2

    Calculate beam size according to the Lebedev-Bogacz formula, based on the Ripken-Mais Twiss
    parameters. The implementation is that of Eq. (A.3.1) in :cite:t:`Lebedev:coupling:2010`.

    .. tip::
        For the calculations, use :math:`\\beta_{11}` and :math:`\\beta_{21}` for the **vertical**
        beam size, but use :math:`\\beta_{12}` and :math:`\\beta_{22}` for the **horizontal** one.
        See the example below.

    Args:
        beta1_ (Union[float, np.ndarray]): value(s) for the beta1x or beta1y Ripken parameter.
        beta2_ (Union[float, np.ndarray]): value(s) for the beta2x or beta2y Ripken parameter.
        geom_emit_x (float): geometric emittance of the horizontal plane, in [m].
        geom_emit_y (float): geometric emittante of the vertical plane, in [m].

    Returns:
        The beam size (horizontal or vertical) according to Lebedev & Bogacz, as
        :math:`\\sqrt{\\epsilon_x * \\beta_{1,\\_}^2 + \\epsilon_y * \\beta_{2,\\_}^2}`.

    Example:
        .. code-block:: python

            >>> geom_emit_x = madx.globals["geometric_emit_x"]
            >>> geom_emit_y = madx.globals["geometric_emit_y"]
            >>> twiss_tfs = madx.twiss(ripken=True).dframe().copy()
            >>> horizontal_size = lebedev_beam_size(
                    twiss_tfs.beta11, twiss_tfs.beta21, geom_emit_x, geom_emit_y
                )
            >>> vertical_size = lebedev_beam_size(
                    twiss_tfs.beta12, twiss_tfs.beta22, geom_emit_x, geom_emit_y
                )
    """
    logger.trace("Computing beam size according to Lebedev formula: sqrt(epsx * b1_^2 + epsy * b2_^2)")
    return np.sqrt(geom_emit_x * beta1_ + geom_emit_y * beta2_)


# ----- Helpers ----- #


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


def _add_beam_size_to_df(df: tfs.TfsDataFrame, geom_emit_x: float, geom_emit_y: float) -> tfs.TfsDataFrame:
    """
    Adds columns with the horizontal and vertical Lebedev beam sizes to a dataframe
    that already contains Ripken Twiss parameters. Assumes that the geometrical emittance
    is identical for the horizontal and vertical plane, which is something I usually have.
    """
    res = df.copy(deep=True)
    res["SIZE_X"] = lebedev_beam_size(res.BETA11, res.BETA21, geom_emit_x, geom_emit_y)  # horizontal
    res["SIZE_Y"] = lebedev_beam_size(res.BETA12, res.BETA22, geom_emit_x, geom_emit_y)  # vertical
    return res
