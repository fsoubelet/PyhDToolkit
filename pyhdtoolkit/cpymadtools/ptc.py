"""
Module cpymadtools.ptc
----------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to harness MAD-X PTC functionality with a cpymad.madx.Madx object.
"""
from pathlib import Path
from typing import Dict, Sequence, Tuple, Union

import pandas as pd
import tfs

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.utils import get_table_tfs


def get_amplitude_detuning(
    madx: Madx, order: int = 2, file: Union[Path, str] = None, fringe: bool = False, **kwargs
) -> tfs.TfsDataFrame:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD), but this has been heavily refactored.
    Calculate amplitude detuning via `PTC_NORMAL`, with sensible defaults set for other relevant `PTC`
    commands. The result table is returned as a `TfsDataFrame`, the headers of which are the contents of the
    internal `SUMM` table.

    The `PTC_CREATE_LAYOUT` command is issued with `model=3` (`SixTrack` model), `method=4` (integration
    order), `nst=3` (number of integration steps, aka body slices for elements) and `exact=True` (use
    exact Hamiltonian, not an approximated one).

    The `PTC_NORMAL` command is explicitely given `icase=6` to enforce 6D calculations (see the `MAD-X`
    manual for details), `no=5` (map order for derivative evaluation of Twiss parameters) and
    `closedorbit=True` (triggers closed orbit calculation) and `normal=True` (activate calculation of the
    Normal Form).

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        order (int): maximum derivative order coefficient (only 0, 1 or 2 implemented in `PTC`).
            Defaults to `2`.
        file (Union[Path, str]): path to output file. Default `None`
        fringe (bool): boolean flag to include fringe field effects in the calculation. Defaults to `False`.

    Keyword Args:
        Any keyword argument is transmitted to the `PTC_NORMAL` command. See above which arguments are
        already set for `PTC_NORMAL` to avoid trying to override them.

    Returns:
        A `TfsDataframe` with results.
    """
    if order >= 3:
        logger.error(f"Maximum amplitude detuning order in PTC is 2, but {order:d} was requested")
        raise NotImplementedError("PTC amplitude detuning is not implemented for order > 2")

    logger.info("Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=3, method=4, nst=3, exact=True)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.trace("Selecting tune orders")
    madx.select_ptc_normal(q1="0", q2="0")
    for ii in range(1, order + 1):  # These are d^iQ/ddp^i
        madx.select_ptc_normal(dq1=f"{ii:d}", dq2=f"{ii:d}")

    # ANH = anharmonicities (ex, ey, deltap), works only with parameters as full strings
    # could be done nicer with permutations ...
    logger.trace("Selecting anharmonicities")
    if order >= 1:
        # madx.select_ptc_normal('anhx=0, 0, 1')  # dQx/ddp
        # madx.select_ptc_normal('anhy=0, 0, 1')  # dQy/ddp
        madx.select_ptc_normal("anhx=1, 0, 0")  # dQx/dex
        madx.select_ptc_normal("anhx=0, 1, 0")  # dQx/dey
        madx.select_ptc_normal("anhy=1, 0, 0")  # dQy/dex
        madx.select_ptc_normal("anhy=0, 1, 0")  # dQy/dey

    if order >= 2:
        # madx.select_ptc_normal('anhx=0, 0, 2')  # d^2Qx/ddp^2
        # madx.select_ptc_normal('anhy=0, 0, 2')  # d^2Qy/ddp^2
        madx.select_ptc_normal("anhx=2, 0, 0")  # d^2Qx/dex^2
        madx.select_ptc_normal("anhx=1, 1, 0")  # d^2Qx/dexdey
        madx.select_ptc_normal("anhx=0, 2, 0")  # d^2Qx/dey^2
        madx.select_ptc_normal("anhy=2, 0, 0")  # d^2Qy/dex^2
        madx.select_ptc_normal("anhy=1, 1, 0")  # d^2Qy/dexdey
        madx.select_ptc_normal("anhy=0, 2, 0")  # d^2Qy/dey^2

    logger.debug("Executing PTC Normal")
    madx.ptc_normal(icase=6, no=5, closed_orbit=True, normal=True, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name="normal_results")
    dframe.index = range(len(dframe.NAME))  # table has a weird index

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def get_rdts(
    madx: Madx, order: int = 4, file: Union[Path, str] = None, fringe: bool = False, **kwargs
) -> tfs.TfsDataFrame:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD), but this has been heavily refactored.
    Calculate the `RDTs` via `PTC_TWISS`, with sensible defaults set for other relevant `PTC` commands.
    The result table is returned as a `TfsDataFrame`, the headers of which are the contents of the
    internal `SUMM` table.

    The `PTC_CREATE_LAYOUT` command is issued with `model=3` (`SixTrack` model), `method=4` (integration
    order), `nst=3` (number of integration steps, aka body slices for elements) and `exact=True` (use
    exact Hamiltonian, not an approximated one).

    The `PTC_TWISS` command is explicitely given `icase=6` to enforce 6D calculations (see the `MAD-X`
    manual for details), `trackrdts=True` (for this function to fullfill its purpose) and `normal=True` to
    trigger saving the normal form analysis results in a table called `NONLIN` which will then be available
    through the provided `Madx` instance.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        order (int): map order for derivative evaluation of Twiss parameters. Defaults to `4`.
        file (Union[Path, str]): path to output file. Default `None`
        fringe (bool): boolean flag to include fringe field effects in the calculation. Defaults to `False`.

    Keyword Args:
        Any keyword argument is transmitted to the `PTC_TWISS` command. See above which arguments are
        already set for `PTC_TWISS` to avoid trying to override them.

    Returns:
        A `TfsDataframe` with results.
    """
    logger.info("Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=3, method=4, nst=3, exact=True)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug("Executing PTC Twiss")
    madx.ptc_twiss(icase=6, no=order, normal=True, trackrdts=True, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name="twissrdt", headers_table="ptc_twiss_summary")

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def ptc_twiss(
    madx: Madx,
    order: int = 4,
    file: Union[Path, str] = None,
    fringe: bool = False,
    table: str = "ptc_twiss",
    **kwargs,
) -> tfs.TfsDataFrame:
    """
    Calculate the TWISS parameters according to G. Ripken's formalism via `PTC_TWISS`, with sensible defaults
    set for other relevant `PTC` commands. The result table is returned as a `TfsDataFrame`, the headers of
    which are the contents of the internal `SUMM` table.

    This is very similar to the `get_rdts` function as both use `ptc_twiss` internally, however this function
    does not track RDTs which makes the calculations significantly faster.

    The `PTC_CREATE_LAYOUT` command is issued with `model=3` (`SixTrack` model), `method=4` (integration
    order), `nst=3` (number of integration steps, aka body slices for elements) and `exact=True` (use
    exact Hamiltonian, not an approximated one).

    The `PTC_TWISS` command is explicitely given `icase=6` to enforce 6D calculations (see the `MAD-X`
    manual for details) `normal=True` to trigger saving the normal form analysis results in a table called
    `NONLIN` which will then be available through the provided `Madx` instance.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        order (int): map order for derivative evaluation of Twiss parameters. Defaults to `4`.
        file (Union[Path, str]): path to output file. Default `None`
        fringe (bool): boolean flag to include fringe field effects in the calculation. Defaults to `False`.
        table (str): the name of the internal table in which to save the results. Defaults to 'ptc_twiss'.

    Keyword Args:
        Any keyword argument is transmitted to the `PTC_TWISS` command. See above which arguments are
        already set for `PTC_TWISS` to avoid trying to override them.

    Returns:
        A `TfsDataframe` with results.
    """
    logger.info(f"Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=3, method=4, nst=3, exact=True)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug("Executing PTC Twiss")
    madx.ptc_twiss(icase=6, no=order, normal=True, table=table, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name=table, headers_table="ptc_twiss_summary")

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def ptc_track_particle(
    madx: Madx,
    initial_coordinates: Tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: str = None,
    observation_points: Sequence[str] = None,
    onetable: bool = False,
    fringe: bool = False,
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """
    Tracks a single particle for nturns through PTC_TRACK, based on its initial coordinates.

    The `PTC_CREATE_LAYOUT` command is issued with `model=3` (`SixTrack` model), `method=4` (integration
    order), `nst=3` (number of integration steps, aka body slices for elements) and `exact=True` (use
    exact Hamiltonian, not an approximated one).

    The `PTC_TRACK` command is explicitely given `ELEMENT_BY_ELEMENT=True` to force element by element
    tracking mode.

    Args:
        madx (Madx): an instantiated cpymad.madx.Madx object.
        initial_coordinates (Tuple[float, float, float, float, float, float]): a tuple with the X, PX, Y, PY,
            T, PT starting coordinates the particle to track. Defaults to all 0 if none given.
        nturns (int): the number of turns to track for.
        sequence (str): the sequence to use for tracking. If no value is provided, it is assumed that a
            sequence is already defined and in use, and this one will be picked up by MAD-X.
        observation_points (Sequence[str]): sequence of all element names at which to OBSERVE during the
            tracking.
        onetable (bool): flag to combine all observation points data into a single table. Defaults to `False`.
        fringe (bool): boolean flag to include fringe field effects in the calculation. Defaults to `False`.

    Keyword Args:
        Any keyword argument to be given to the `PTC_TRACK` command, such as the `CLOSED_ORBIT` flag to
        activate closed orbit calculation before tracking. Refer to the `MAD-X` manual for options.

    Returns:
        A dictionary with a copy of the track table's dataframe for each defined observation point,
        with as columns the coordinates x, px, y, py, t, pt, s and e (energy). The keys of the dictionary
        are simply numbered 'observation_point_1', 'observation_point_2' etc. The first observation point
        always corresponds to the start of machine, the others correspond to the ones manually defined,
        in the order they are defined in.

        If the user has set `onetable` to `True`, only one entry is in the dictionary under the key
        'trackone' and it has the combined table as a pandas DataFrame for value.
    """
    start = initial_coordinates if initial_coordinates else [0, 0, 0, 0, 0, 0]
    observation_points = observation_points if observation_points else []

    if isinstance(sequence, str):
        logger.debug(f"Using sequence '{sequence}' for tracking")
        madx.use(sequence=sequence)

    logger.info(f"Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=3, method=4, nst=3, exact=True)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug(f"Tracking coordinates with initial X, PX, Y, PY, T, PT of '{initial_coordinates}'")
    madx.command.ptc_start(
        X=start[0], PX=start[1], Y=start[2], PY=start[3], T=start[4], PT=start[5],
    )

    for element in observation_points:
        logger.trace(f"Setting observation point for tracking with OBSERVE at element '{element}'")
        madx.command.ptc_observe(place=element)

    madx.command.ptc_track(turns=nturns, element_by_element=True, onetable=onetable, **kwargs)
    madx.ptc_end()

    if onetable:  # user asked for ONETABLE, there will only be one table 'trackone' given back by MAD-X
        logger.debug("Because of option ONETABLE only one table 'TRACKONE' exists to be returned.")
        return {"trackone": madx.table.trackone.dframe().copy()}
    return {
        f"observation_point_{point:d}": madx.table[f"track.obs{point:04d}.p0001"].dframe().copy()
        for point in range(1, len(observation_points) + 2)  # len(observation_points) + 1 for start of
        # machine + 1 because MAD-X starts indexing these at 1
    }
