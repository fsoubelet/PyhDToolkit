"""
Module cpymadtools.track
------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to manipulate MAD-X TRACK functionality through a cpymad.madx.Madx object.
"""
from typing import Dict, Sequence, Tuple

import pandas as pd

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def track_single_particle(
    madx: Madx,
    initial_coordinates: Tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: str = None,
    observation_points: Sequence[str] = None,
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """
    Tracks a single particle for nturns, based on its initial coordinates.

    Args:
        madx (Madx): an instantiated cpymad.madx.Madx object.
        initial_coordinates (Tuple[float, float, float, float, float, float]): a tuple with the X, PX, Y, PY,
            T, PT starting coordinates the particle to track. Defaults to all 0 if none given.
        nturns (int): the number of turns to track for.
        sequence (str): the sequence to use for tracking. If no value is provided, it is assumed that a
            sequence is already defined and in use, and this one will be picked up by MAD-X.
        observation_points (Sequence[str]): sequence of all element names at which to OBSERVE during the
            tracking.

    Keyword Args:
        Any keyword argument to be given to the `TRACK` command like it would be given directly into `MAD-X`,
        for instance `ONETABLE` etc. Refer to the `MAD-X` manual for options.

    Returns:
        A dictionary with a copy of the track table's dataframe for each defined observation point,
        with as columns the coordinates x, px, y, py, t, pt, s and e (energy). The keys of the dictionary
        are simply numbered 'observation_point_1', 'observation_point_2' etc. The first observation point
        always corresponds to the start of machine, the others correspond to the ones manually defined,
        in the order they are defined in.

        If the user has set `onetable` to `True`, only one entry is in the dictionary under the key
        'trackone' and it has the combined table as a pandas DataFrame for value.
    """
    onetable = kwargs.get("onetable", False) if "onetable" in kwargs else kwargs.get("ONETABLE", False)
    start = initial_coordinates if initial_coordinates else [0, 0, 0, 0, 0, 0]
    observation_points = observation_points if observation_points else []

    if isinstance(sequence, str):
        logger.debug(f"Using sequence '{sequence}' for tracking")
        madx.use(sequence=sequence)

    logger.debug(f"Tracking coordinates with initial X, PX, Y, PY, T, PT of '{initial_coordinates}'")
    madx.command.track(**kwargs)

    for element in observation_points:
        logger.trace(f"Setting observation point for tracking with OBSERVE at element '{element}'")
        madx.command.observe(place=element)

    madx.command.start(X=start[0], PX=start[1], Y=start[2], PY=start[3], T=start[4], PT=start[5])
    madx.command.run(turns=nturns)
    madx.command.endtrack()
    if onetable:  # user asked for ONETABLE, there will only be one table 'trackone' given back by MAD-X
        logger.debug("Because of option ONETABLE only one table 'TRACKONE' exists to be returned.")
        return {"trackone": madx.table.trackone.dframe().copy()}
    return {
        f"observation_point_{point:d}": madx.table[f"track.obs{point:04d}.p0001"].dframe().copy()
        for point in range(1, len(observation_points) + 2)  # len(observation_points) + 1 for start of
        # machine + 1 because MAD-X starts indexing these at 1
    }
