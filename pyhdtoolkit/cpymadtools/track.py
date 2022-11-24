"""
.. _cpymadtools-track:

Tracking Routines
-----------------

Module with functions to manipulate ``MAD-X`` ``TRACK`` functionality through a
`~cpymad.madx.Madx` object.
"""
from typing import Dict, Optional, Sequence, Tuple

import pandas as pd

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def track_single_particle(
    madx: Madx,
    initial_coordinates: Tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: Optional[str] = None,
    observation_points: Sequence[str] = None,
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """
    .. versionadded:: 0.8.0

    Tracks a single particle for *nturns*, based on its initial coordinates. For an example of the use of this
    function, have a look at the :ref:`phase space <demo-phase-space>` or :ref:`tracking <demo-free-tracking>`
    example galleries.

    Args:
        madx (cpymad.madx.Madx): an instantiated `~cpymad.madx.Madx` object.
        initial_coordinates (Tuple[float, float, float, float, float, float]): a tuple with the ``X, PX,
            Y, PY, T, PT`` starting coordinates of the particle to track. Defaults to all 0 if `None` given.
        nturns (int): the number of turns to track for.
        sequence (Optional[str]): the sequence to use for tracking. If no value is provided, it is assumed
            that a sequence is already defined and in use, and this one will be picked up by ``MAD-X``.
            Beware of the dangers of giving a sequence that will be used by ``MAD-X``, see the warning below
            for more information.
        observation_points (Sequence[str]): sequence of all element names at which to ``OBSERVE`` during the
            tracking.
        **kwargs: Any keyword argument will be given to the ``TRACK`` command like it would be given directly
            into ``MAD-X``, for instance ``ONETABLE`` etc. Refer to the ``MAD-X`` manual for options.

    .. warning::
        If the *sequence* argument is given a string value, the ``USE`` command will be ran on the provided
        sequence name. This means the caveats of ``USE`` apply, for instance the erasing of previously
        defined errors, orbits corrections etc. In this case a warning will be logged but the function will
        proceed. If `None` is given (by default) then the sequence already in use will be the one tracking
        is performed on.

    Returns:
        A `dict` with a copy of the track table's dataframe for each defined observation point,
        with as columns the coordinates ``x, px, y, py, t, pt, s and e`` (energy). The keys of the dictionary
        are simply named ``observation_point_1``, ``observation_point_2`` etc. The first observation point
        always corresponds to the start of machine, the others correspond to the ones manually defined,
        in the order they are defined in.

        If the user has set ``onetable`` to `True`, only one entry is in the dictionary under the key
        ``trackone`` and it has the combined table as a pandas DataFrame for value.

    Example:
        .. code-block:: python

            >>> tracks_dict = track_single_particle(
            ...     madx, nturns=1023, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0)
            ... )
    """
    logger.debug("Performing single particle MAD-X (thin) tracking")
    onetable = kwargs.get("onetable", False) if "onetable" in kwargs else kwargs.get("ONETABLE", False)
    start = initial_coordinates if initial_coordinates else [0, 0, 0, 0, 0, 0]
    observation_points = observation_points if observation_points else []

    if isinstance(sequence, str):
        logger.warning(f"Sequence '{sequence}' was provided and will be USEd, beware that this will erase errors etc.")
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
        return {"trackone": madx.table.trackone.dframe()}
    return {
        f"observation_point_{point:d}": madx.table[f"track.obs{point:04d}.p0001"].dframe()
        for point in range(1, len(observation_points) + 2)  # len(observation_points) + 1 for start of
        # machine + 1 because MAD-X starts indexing these at 1
    }
