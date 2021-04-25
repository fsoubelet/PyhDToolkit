"""
Module cpymadtools.tune
-----------------------

Created on 2021.04.01
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to manipulate MAD-X functionality around the tune through a cpymad.madx.Madx
object.
"""
import math
import sys

from pathlib import Path

import pandas as pd

from cpymad.madx import Madx
from loguru import logger


def make_footprint_table(
    madx: Madx, sigma: float = 5, dense: bool = False, file: str = None, cleanup: bool = True, **kwargs,
) -> pd.DataFrame:
    """
    Instantiates an ensemble of particles up to the desired bunch sigma amplitude to be tracked for the
    DYNAP command, letting MAD-X infer their tunes. Particules are instantiated for different angle
    variables for each amplitude, creating an ensemble able to represent the tune footprint.

    Beware: since DYNAP makes use of tracking, your sequence needs to be sliced first.s

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        sigma (float): the maximum amplitude of the tracked particles, in bunch sigma. Defaults to 5.
        dense (bool): if set to True, an increased number of particles will be tracked. Defaults to False.
        file (str): If given, the `dynaptune` table will be exported as a TFS file with the provided name.
        cleanup (bool): If True, the `fort.69` and `lyapunov.data` files are cleared before returning the
            dynap table. Defaults to True.

	Keyword Args:
		Any keyword argument that will be transmitted to the DYNAP command in MAD-X.

    Returns:
		The resulting `dynaptune` table, as a pandas DataFrame.
    """
    logger.info(f"Initiating particules up to {sigma:d} bunch sigma to create a tune footprint table")
    small, big = 0.05, math.sqrt(1 - 0.05 ** 2)
    sigma_multiplier, angle_multiplier = 0.1, 0

    logger.debug("Initializing particles")
    madx.command.track()
    madx.command.start(fx=small, fy=small)
    while sigma_multiplier <= sigma + 1:
        angle = 15 * angle_multiplier * math.pi / 180
        if angle_multiplier == 0:
            madx.command.start(fx=sigma_multiplier * big, fy=sigma_multiplier * small)
        elif angle_multiplier == 6:
            madx.command.start(fx=sigma_multiplier * small, fy=sigma_multiplier * big)
        else:
            madx.command.start(fx=sigma_multiplier * math.cos(angle), fy=sigma_multiplier * math.sin(angle))
        angle_multiplier += 0.5
        if int(angle_multiplier) == 7:
            angle_multiplier = 0
            sigma_multiplier += 1 if not dense else 0.5

    logger.debug("Starting DYNAP tracking with initialized particles")
    try:
        madx.command.dynap(fastune=True, turns=1024, **kwargs)
        madx.command.endtrack()
    except RuntimeError as madx_crash:
        logger.error(
            "Remote MAD-X process crashed, most likely because you did not slice the sequence "
            "before running DYNAP. Restart and slice before calling this function."
        )
        raise RuntimeError("DYNAP command crashed the MAD-X process") from madx_crash

    if cleanup and sys.platform not in ("win32", "cygwin"):
        # fails on Windows due to its I/O system, since MAD-X still has "control" of the files
        logger.debug("Cleaning up DYNAP output file `fort.69` and `lyapunov.data`")
        Path("fort.69").unlink()
        Path("lyapunov.data").unlink()

    if file:
        madx.command.write(table="dynaptune", file=f"{file}")
    return madx.table.dynaptune.dframe().copy()
