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

from loguru import logger

try:
    from cpymad.madx import Madx
except ModuleNotFoundError:
    Madx = None


# ----- Utilities ----- #


def get_amplitude_detuning(
    cpymad_instance: Madx, order: int = 2, file: Union[Path, str] = None
) -> tfs.TfsDataFrame:
    """
    CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Calculate amplitude detuning via PTC_NORMAL.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        order (int): maximum derivative order (only 0, 1 or 2 implemented in PTC). Defaults to `2`.
        file (Union[Path, str]): path to output file. Default `None`

    Returns:
        A TfsDataframe with results.
    """
    if order >= 3:
        logger.error(f"Maximum amplitude detuning order in PTC is 2, but {order:d} was requested")
        raise NotImplementedError("PTC amplitude detuning is not implemented for order > 2")

    logger.info("Entering PTC to calculate amplitude detuning")
    cpymad_instance.ptc_create_universe()

    # layout I got with mask (jdilly)
    # model=3 (Sixtrack code model: Delta-Matrix-Kick-Matrix)
    # method=4 (integration order), nst=3 (integration steps), exact=True (exact Hamiltonian)
    logger.trace("Creating PTC layout")
    cpymad_instance.ptc_create_layout(model=3, method=4, nst=3, exact=True)

    # alternative layout: model=3, method=6, nst=3
    # resplit=True (adaptive splitting of magnets), thin=0.0005 (splitting of quads),
    # xbend=0.0005 (splitting of dipoles)
    # madx.ptc_create_layout(model=3, method=6, nst=3, resplit=True, thin=0.0005, xbend=0.0005)

    logger.trace("Incorporating MAD-X alignment errors")
    cpymad_instance.ptc_align()  # use madx alignment errors
    # madx.ptc_setswitch(fringe=True)  # include fringe effects

    logger.trace("Selecting tune orders")
    cpymad_instance.select_ptc_normal(q1="0", q2="0")
    for ii in range(1, order + 1):  # These are d^iQ/ddp^i
        cpymad_instance.select_ptc_normal(dq1=f"{ii:d}", dq2=f"{ii:d}")

    # ANH = anharmonicities (ex, ey, deltap), works only with parameters as full strings
    # could be done nicer with permutations ...
    logger.trace("Selecting anharmonicities")
    if order >= 1:
        # madx.select_ptc_normal('anhx=0, 0, 1')  # dQx/ddp
        # madx.select_ptc_normal('anhy=0, 0, 1')  # dQy/ddp
        cpymad_instance.select_ptc_normal("anhx=1, 0, 0")  # dQx/dex
        cpymad_instance.select_ptc_normal("anhx=0, 1, 0")  # dQx/dey
        cpymad_instance.select_ptc_normal("anhy=1, 0, 0")  # dQy/dex
        cpymad_instance.select_ptc_normal("anhy=0, 1, 0")  # dQy/dey

    if order >= 2:
        # madx.select_ptc_normal('anhx=0, 0, 2')  # d^2Qx/ddp^2
        # madx.select_ptc_normal('anhy=0, 0, 2')  # d^2Qy/ddp^2
        cpymad_instance.select_ptc_normal("anhx=2, 0, 0")  # d^2Qx/dex^2
        cpymad_instance.select_ptc_normal("anhx=1, 1, 0")  # d^2Qx/dexdey
        cpymad_instance.select_ptc_normal("anhx=0, 2, 0")  # d^2Qx/dey^2
        cpymad_instance.select_ptc_normal("anhy=2, 0, 0")  # d^2Qy/dex^2
        cpymad_instance.select_ptc_normal("anhy=1, 1, 0")  # d^2Qy/dexdey
        cpymad_instance.select_ptc_normal("anhy=0, 2, 0")  # d^2Qy/dey^2

    # icase = phase-space dimensionality, no = order of map
    logger.debug("Executing PTC Normal")
    cpymad_instance.ptc_normal(closed_orbit=True, normal=True, icase=5, no=5)
    cpymad_instance.ptc_end()

    logger.debug("Extracting results to TfsDataFrame")
    dframe = tfs.TfsDataFrame(cpymad_instance.table.normal_results.dframe())
    dframe.columns = dframe.columns.str.upper()
    dframe.NAME = dframe.NAME.str.upper()
    dframe.index = range(len(dframe.NAME))  # table has a weird index

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def get_rdts(cpymad_instance: Madx, order: int = 4, file: Union[Path, str] = None) -> tfs.TfsDataFrame:
    """
    CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Calculate the RDTs via PTC_TWISS.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        order (int): maximum derivative order (only 0, 1 or 2 implemented in PTC). Defaults to `2`.
        file (Union[Path, str]): path to output file. Default `None`

    Returns:
        TfsDataframe with results
    """
    logger.info("Entering PTC to calculate RDTs")
    cpymad_instance.ptc_create_universe()

    logger.trace("Creating PTC layout")
    cpymad_instance.ptc_create_layout(model=3, method=4, nst=3, exact=True)
    # madx.ptc_create_layout(model=3, method=6, nst=1)  # from Michi

    logger.trace("Incorporating MAD-X alignment errors")
    cpymad_instance.ptc_align()  # use madx alignment errors
    # madx.ptc_setswitch(fringe=True)  # include fringe effects

    logger.debug("Executing PTC Twiss")
    cpymad_instance.ptc_twiss(icase=6, no=order, normal=True, trackrdts=True)
    cpymad_instance.ptc_end()

    logger.debug("Extracting results to TfsDataFrame")
    dframe = tfs.TfsDataFrame(madx.table.twissrdt.dframe())
    dframe.columns = dframe.columns.str.upper()
    dframe.NAME = dframe.NAME.str.upper()

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe