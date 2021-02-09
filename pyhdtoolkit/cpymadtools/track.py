"""
Module cpymadtools.track
------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to manipulate MAD-X TRACK functionality through a cpymad.madx.Madx object.
"""
from typing import Dict, Tuple

import pandas as pd

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def track_single_particle(
    madx: Madx,
    initial_coordinates: Tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: str = None,
) -> pd.DataFrame:
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
        A copy of the track table's dataframe, with as columns the coordinates x, px, y, py, t, pt,
        s and e (energy).
    """
    start = initial_coordinates

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
    return madx.table["track.obs0001.p0001"].dframe().copy()
