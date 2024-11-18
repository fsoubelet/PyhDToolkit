"""
.. _cpymadtools-track:

Tracking Routines
-----------------

Module with functions to manipulate ``MAD-X`` ``TRACK`` functionality
through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pandas as pd

    from cpymad.madx import Madx

# ----- Utlites ----- #


def track_single_particle(
    madx: Madx,
    /,
    initial_coordinates: tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: str | None = None,
    observation_points: Sequence[str] | None = None,
    **kwargs,
) -> dict[str, pd.DataFrame]:
    """
    .. versionadded:: 0.8.0

    Tracks a single particle for *nturns* through the ``TRACK`` command, based
    on its initial coordinates. For an example of the use of this function, have
    a look at either the :ref:`phase space <demo-phase-space>` or the
    :ref:`tracking <demo-free-tracking>` example galleries.

    Warning
    -------
        If the *sequence* parameter is given a string value, the ``USE`` command will
        be ran on the provided sequence name. This means the caveats of ``USE`` apply,
        for instance the erasing of previously defined errors, orbits corrections etc.
        In this case a warning will be logged but the function will proceed. If `None`
        is given (by default) then the sequence already in use will be the one tracking
        is performed with.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instantiated `~cpymad.madx.Madx` object. Positional only.
    initial_coordinates : tuple[float, float, float, float, float, float]
        A tuple with the ``X, PX, Y, PY, T, PT`` starting coordinates of the
        particle to track. Defaults to all 0 if `None` given.
    nturns : int
        The number of turns to track for.
    sequence : str, optional
        The sequence to use for tracking. If no value is provided, it is assumed
        that a sequence is already defined and in use, and this one will be picked
        up by ``MAD-X``. Beware of the dangers of giving a sequence that will be
        ``use``-d by ``MAD-X``, see the warning above for more information.
    observation_points : Sequence[str], optional
        A sequence of element names at which to ``OBSERVE`` during the tracking.
    **kwargs
        Any keyword argument will be given to the ``TRACK`` command, for instance
        `ONETABLE` etc. Refer to the `MAD-X manual
        <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_
        for options.

    Returns
    -------
    dict[str, pd.DataFrame]
        A `dict` with a copy of the track table's dataframe for each defined
        observation point, with as columns the coordinates ``x, px, y, py, t,
        pt, s and e`` (energy). The keys of the dictionary are simply named
        `observation_point_1`, `observation_point_2` etc. The first observation
        point always corresponds to the start of machine, the others correspond
        to the ones manually defined at function call, in the order they are given.

        If the user has set `onetable=True`, only one entry is in the dictionary
        under the key ``trackone`` and it has the combined table as a
        `~pandas.DataFrame` for value.

    Example
    -------
        .. code-block:: python

            tracks_dict = track_single_particle(
                madx, nturns=1023, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0)
            )
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
