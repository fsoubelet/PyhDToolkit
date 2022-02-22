"""
.. _optics-twiss:

Twiss Optics
------------

Module implementing various calculations based on the ``TWISS`` optics parameters.
"""
import numpy as np


def courant_snyder_transform(u_vector: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """
    Perform the Courant-Snyder transform on regular (nonchaotic) phase-space coordinates.
    Specifically, if considering the horizontal plane and noting :math:`U = (x, px)` the
    phase-space vector, it returns :math:`\\bar{U} = (\\bar{x}, \\bar{px})` according to
    the transform :math:`\\bar{U} = P \\cdot U`, where::

        P = [1/sqrt(beta_x)              0      ]
            [alpha_x/sqrt(beta_x)   sqrt(beta_x)]

    Args:
        u_vector (np.ndarray): two-dimentional array of phase-space (spatial and momenta)
            coordinates, either horizontal or vertical.
        alpha (float): alpha twiss parameter in the appropriate plane.
        beta (float): beta twiss parameter in the appropriate plane.

    Returns:
        The normalized phase-space coordinates from the Courant-Snyder transform.
    """
    p_matrix = np.array([[1 / np.sqrt(beta), 0], [alpha / np.sqrt(beta), np.sqrt(beta)]])
    return p_matrix @ u_vector
