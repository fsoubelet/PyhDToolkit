"""
.. _optics-ripken:

Ripken Parameters
-----------------

Module implementing various calculations based
on the :cite:t:`Ripken:optics:1989` optics parameters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from tfs import TfsDataFrame


# ----- Setup Utilites ----- #


def lebedev_beam_size(
    beta1_: float | np.ndarray, beta2_: float | np.ndarray, gemitt_x: float, gemitt_y: float
) -> float | np.ndarray:
    """
    .. versionadded:: 0.8.2

    Calculate beam size according to the Lebedev-Bogacz formula, based
    on the Ripken-Mais Twiss parameters. The implementation is that of
    Eq. (A.3.1) in :cite:t:`Lebedev:coupling:2010`.

    Hint
    ----
        For the calculations, use :math:`\\beta_{11}` and :math:`\\beta_{21}`
        for the **vertical** beam size, but use :math:`\\beta_{12}` and
        :math:`\\beta_{22}` for the **horizontal** one. See the example below.

    Parameters
    ----------
    beta1_ : float | numpy.ndarray
        Value(s) for the beta1x or beta1y Ripken parameters.
    beta2_ : float | numpy.ndarray
        Value(s) for the beta2x or beta2y Ripken parameters.
    gemitt_x : float
        Geometric horizontal emittance, in [m].
    gemitt_y : float
        Geometric vertical emittance, in [m].

    Returns
    -------
    float | numpy.ndarray
        The beam size (horizontal or vertical) according to Lebedev& Bogacz, as
        :math:`\\sqrt{\\epsilon_x * \\beta_{1,\\_}^2 + \\epsilon_y * \\beta_{2,\\_}^2}`.

    Example
    -------
        .. code-block:: python

            gemitt_x = madx.globals["geometric_emit_x"]
            gemitt_y = madx.globals["geometric_emit_y"]
            twiss_tfs = madx.twiss(ripken=True).dframe()
            horizontal_size = lebedev_beam_size(
                twiss_tfs.beta11, twiss_tfs.beta21, gemitt_x, gemitt_y
            )
            vertical_size = lebedev_beam_size(
                twiss_tfs.beta12, twiss_tfs.beta22, gemitt_x, gemitt_y
            )
    """
    return np.sqrt(gemitt_x * beta1_ + gemitt_y * beta2_)


# ----- Helpers ----- #


def _beam_size(coordinates_distribution: np.ndarray, method: str = "std") -> float:
    """
    Computes the beam size from particle coordinates, either as the
    standard deviation or as the root mean square of the distribution.

    Parameters
    ----------
    coordinates_distribution : numpy.ndarray
        Ensemble of coordinates of the particle distribution.
    method : str
        The method of calculation to use, either 'std' (using the standard
        deviation as the beam size) or 'rms' (root mean square). Case
        insensitive.

    Returns
    -------
    float
        The computed beam size.

    Raises
    ------
    NotImplementedError
        If the required *method* is neither std nor rms.
    """
    if method.lower() not in ("std", "rms"):
        msg = "Invalid method provided"
        raise NotImplementedError(msg)
    if method == "std":
        return coordinates_distribution.std()
    return np.sqrt(np.mean(np.square(coordinates_distribution)))  # rms


def _add_beam_size_to_df(df: TfsDataFrame, geom_emit_x: float, geom_emit_y: float) -> TfsDataFrame:
    """
    Adds columns with the horizontal and vertical Lebedev beam sizes
    to a dataframe that already contains Ripken Twiss parameters.
    Assumes that the geometrical emittance is identical for the horizontal
    and vertical plane, which is something I usually have. Beware.
    """
    res = df.copy(deep=True)
    res["SIZE_X"] = lebedev_beam_size(res.BETA11, res.BETA21, geom_emit_x, geom_emit_y)  # horizontal
    res["SIZE_Y"] = lebedev_beam_size(res.BETA12, res.BETA22, geom_emit_x, geom_emit_y)  # vertical
    return res
