"""
Module optics.twiss
-------------------

Created on 2020.09.07
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 module implementing various functionality for optics calculations from / to
twiss parameters.
"""
import numba
import numpy as np


@numba.njit()
def courant_snyder_transform(u_vector: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """
    Perform the Courant-Snyder transform on rergular (nonchaotic) phase-space coordinatess.
    Specifically, if considering the horizontal plane and noting U = (x, px) the phase-space
    vector, it returns U_bar = (x_bar, px_bar) according to the transform:
    U_bar = P * U,  where  P = [1/sqrt(beta_x)              0      ]
                               [alpha_x/sqrt(beta_x)   sqrt(beta_x)]

    Args:
        u_vector (np.ndarray): two-dimentional array of phase-space (spatial and momenta)
            coordinates, either horizontal or vertical.
        alpha (float): alpha twiss parameter in the appropriate plane.
        beta (float): beta twiss parameter in the appropriate plane.

    Returns:
        The normal phase-space coordinates from the Courant-Snyder transform.
    """
    p_matrix = np.array([[1 / np.sqrt(beta), 0], [alpha / np.sqrt(beta), np.sqrt(beta)]])
    return p_matrix @ u_vector
