"""
Module cpymadtools.errors
-------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X errors setups and manipulatioins with a cpymad.madx.Madx object,
mainly for LHC and HLLHC machines.
"""
from typing import Sequence

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def switch_magnetic_errors(madx: Madx, **kwargs) -> None:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Applies magnetic field orders. This will only work for LHC and HLLHC machines.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.

    Keyword Args:
        default: sets global default to this value. Defaults to `False`.
        AB#:  sets the default for all of that order, the order being the # number.
        A# or B#: sets the default for systematic and random of this id.
        A#s, B#r etc.: sets the specific value.

    In all kwargs, the order # should be in the range (1...15), where 1 == dipolar field.
    """
    logger.debug("Setting magnetic errors")
    global_default = kwargs.get("default", False)

    for order in range(1, 16):
        logger.trace(f"Setting up for order {order}")
        order_default = kwargs.get(f"AB{order:d}", global_default)

        for ab in "AB":
            ab_default = kwargs.get(f"{ab}{order:d}", order_default)
            for sr in "sr":
                name = f"{ab}{order:d}{sr}"
                error_value = int(kwargs.get(name, ab_default))
                logger.trace(f"Setting global for 'ON_{name}' to {error_value}")
                madx.globals[f"ON_{name}"] = error_value


def misalign_lhc_triplets(
    madx: Madx, ip: int, sides: Sequence[str] = ("r", "l"), table: str = "triplet_errors", **kwargs
) -> None:
    """
    Apply misalignment errors to triplet quadrupoles on a given side of a given IP. In case of a sliced
    lattice, this will misalign all slices of the magnet together.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        ip (int): the interaction point around which to apply errors.
        sides (Sequence[str]): sides of the IP to apply error on the triplets, either L or R or both.
            Defaults to both.
        table (str): the name of the internal table that will save the assigned errors. Defaults to
            'triplet_errors'.

    Keyword Args:
        Any keyword argument to give to the EALIGN command, including the error to apply (DX, DY,
        DPSI etc) as a string, like it would be given directly into MAD-X.

    Examples:
        misalign_lhc_triplets(madx, ip=1, sides="RL", dx="1E-5 * TGAUSS(2.5)")
        misalign_lhc_triplets(madx, ip=5, sides="RL", dpsi="0.001 * TGAUSS(2.5)")
    """
    if ip not in (1, 2, 5, 8) or any(side.upper() not in ("R", "L") for side in sides):
        logger.error("Either the IP number of the side provided are invalid, not applying any error.")
        raise ValueError("Invalid 'ip' or 'sides' argument")

    logger.info(f"Applying alignment errors to triplets, with arguments {kwargs}")
    madx.command.select(flag="error", clear=True)
    for side in sides:
        logger.debug(f"Applying errors on {'right' if side.upper() == 'R' else 'left'} triplet of IP{ip:d}")
        madx.command.select(flag="error", pattern=f"^MQXA.1{side.upper()}{ip:d}")  # Q1 LHC
        madx.command.select(flag="error", pattern=f"^MQXFA.[AB]1{side.upper()}{ip:d}")  # Q1A & Q1B HL-LHC
        madx.command.select(flag="error", pattern=f"^MQXB.[AB]2{side.upper()}{ip:d}")  # Q2A & Q2B LHC
        madx.command.select(flag="error", pattern=f"^MQFXB.[AB]2{side.upper()}{ip:d}")  # Q2A & Q2B HL-LHC
        madx.command.select(flag="error", pattern=f"^MQXA.3{side.upper()}{ip:d}")  # Q3 LHC
        madx.command.select(flag="error", pattern=f"^MQXFA.[AB]3{side.upper()}{ip:d}")  # Q3A & Q3B HL-LHC
    madx.command.ealign(**kwargs)

    logger.debug(f"Saving assigned errors in internal table '{table if table else 'etable'}'")
    madx.command.etable(table=table)

    logger.trace("Clearing up error flag")
    madx.command.select(flag="error", clear=True)
