"""
.. _optics-twiss:

Twiss Optics
------------

Module implementing various calculations based on the ``TWISS`` optics parameters.
"""

import numpy as np


def courant_snyder_transform(u_vector: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    r"""
    .. versionadded:: 0.5.0

    Perform the Courant-Snyder transform on regular (nonchaotic) phase
    space coordinates. Specifically, if considering the horizontal plane
    and noting :math:`U = (x, px)` the phase-space vector, it returns
    :math:`\bar{U} = (\bar{x}, \bar{px})` according to the transform
    :math:`\bar{U} = P \cdot U`, where

    .. math::

        P = \begin{pmatrix}
                \frac{1}{\sqrt{\beta_x}}          &   0              \\
                \frac{\alpha_x}{\sqrt{\beta_x}}   &  \sqrt{\beta_x}  \\
            \end{pmatrix}

    Parameters
    ----------
    u_vector : numpy.ndarray
        Two-dimentional array of the phase-space (spatial and momentum)
        coordinates, either horizontal or vertical.
    alpha : float
        Alpha twiss parameter in the appropriate plane.
    beta : float
        Beta twiss parameter in the appropriate plane.

    Returns
    -------
    numpy.ndarray
        The normalized phase-space coordinates from the Courant-Snyder
        transform.

    Example
    -------
        .. code-block:: python

            alfx = madx.table.twiss.alfx[0]
            betx = madx.table.twiss.betx[0]
            u = np.array([x_coords, px_coord])
            u_bar = courant_snyder_transform(u, alfx, betx)
    """
    p_matrix = np.array([[1 / np.sqrt(beta), 0], [alpha / np.sqrt(beta), np.sqrt(beta)]])
    return p_matrix @ u_vector
