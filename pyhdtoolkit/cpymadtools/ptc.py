"""
Module cpymadtools.ptc
----------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to harness MAD-X PTC functionality with a cpymad.madx.Madx object.
"""
from pathlib import Path
from typing import Union

import tfs

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.utils import get_table_tfs

# ----- Utilities ----- #


def get_amplitude_detuning(
    madx: Madx, order: int = 2, file: Union[Path, str] = None, fringe: bool = False, **kwargs
) -> tfs.TfsDataFrame:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD), but this has been heavily refactored.
    Calculate amplitude detuning via `PTC_NORMAL`, with sensible defaults set for other relevant `PTC`
    commands. The result table is returned as a `TfsDataFrame`, the headers of which are the contents of the
    internal `SUMM` table.

    The `PTC_CREATE_LAYOUT` command is issued with `model=3` (`SixTrack` model), `method=4` (integration
    order), `nst=3` (number of integratioin steps, aka body slices for elements) and `exact=True` (use
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

    logger.info("Entering PTC to calculate amplitude detuning")
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
    order), `nst=3` (number of integratioin steps, aka body slices for elements) and `exact=True` (use
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
    logger.info(f"Entering PTC to calculate RDTs up to order {order}")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=3, method=4, nst=3, exact=True)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug("Executing PTC Twiss")
    madx.ptc_twiss(icase=6, no=order, normal=True, trackrdts=True, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name="twissrdt")

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe
