"""
Module cpymadtools.twiss
------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to manipulate MAD-X TRACK functionality through a cpymad.madx.Madx object.
"""
from typing import Dict, Tuple

import numpy as np

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def track_single_particle(
    madx: Madx,
    initial_coordinates: Tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: str = None,
) -> Dict[str, np.ndarray]:
    """
    Tracks a single particle for nturns, based on its initial coordinates.

    Args:
        madx (Madx): an instantiated cpymad.madx.Madx object.
        initial_coordinates (Tuple[float, float, float, float, float, float]): a tuple with the X, PX, Y, PY,
            T, PT starting coordinates the particle to track.
        nturns (int): the number of turns to track for.
        sequence (str): the sequence to use for tracking. If no value is provided, it is assumed that a
            sequence is already defined and in use, and this one will be picked up by MAD-X.

    Returns:
        A dictionnary with the X, PX, Y, PY keys, each holding these specific coordinates of the
        particle along the tracking, as a numpy ndarray.
    """
    start = initial_coordinates
    x_coordinates, px_coordinates, y_coordinates, py_coordinates = [], [], [], []

    if isinstance(sequence, str):
        logger.debug(f"Using sequence '{sequence}' for tracking")
        madx.use(sequence=sequence)

    logger.debug(f"Tracking coordinates with initial X, PX, Y, PY, T, PT of '{initial_coordinates}'")
    madx.command.track()
    madx.command.start(
        X=start[0], PX=start[1], Y=start[2], PY=start[3], T=start[4], PT=start[5],
    )
    madx.command.run(turns=nturns)
    madx.command.endtrack()

    return {
        "x": madx.table["track.obs0001.p0001"].dframe()["x"].to_numpy(dtype=float),
        "px": madx.table["track.obs0001.p0001"].dframe()["px"].to_numpy(dtype=float),
        "y": madx.table["track.obs0001.p0001"].dframe()["y"].to_numpy(dtype=float),
        "py": madx.table["track.obs0001.p0001"].dframe()["py"].to_numpy(dtype=float),
    }
