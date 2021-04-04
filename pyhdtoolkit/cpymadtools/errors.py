"""
Module cpymadtools.errors
-------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X errors setups and manipulatioins with a cpymad.madx.Madx object,
mainly for LHC and HLLHC machines.
"""
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


def misalign_lhc_triplet(madx: Madx, quad_number: int, ip: int, side: str, **kwargs,) -> None:
    """
    Apply misalignment errors to a triplet quadrupole on a given side of a given IP. In case of a sliced
    lattice, this will misalign all slices of the magnet together.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        quad_number (int): the numbering of the triplet to apply errors for. Should be on of 1, 2 or 3.
        side (str): side of the IP to apply error on the triplets, either L or R.
        ip (int): the interaction point around which to apply errors.

    Keyword Args:
        Any keyword argument to give to the EALIGN command, including the error to apply (DX, DY, DPSI etc).
    """

    if quad_number not in (1, 2, 3):
        logger.error(f"Quadrupole Q{quad_number} is not a triplet, this function will not have effect.")
        return

    logger.info(f"Applying alignment errors to Q{quad_number:d}")
    madx.command.select(flag="error", clear=True)

    if quad_number == 1:
        madx.command.select(flag="error", pattern=f"^MQXA.1{side.upper()}{ip:d}")  # Q1 LHC
        madx.command.select(flag="error", pattern=f"^MQXFA.[AB]1{side.upper()}{ip:d}")  # Q1A & Q1B HL-LHC

    elif quad_number == 2:
        madx.command.select(flag="error", pattern=f"^MQXB.[AB]2{side.upper()}{ip:d}")  # Q2A & Q2B LHC
        madx.command.select(flag="error", pattern=f"^MQFXB.[AB]2{side.upper()}{ip:d}")  # Q2A & Q2B HL-LHC

    elif quad_number == 3:
        madx.command.select(flag="error", pattern=f"^MQXA.3{side.upper()}{ip:d}")  # Q3 LHC
        madx.command.select(flag="error", pattern=f"^MQXFA.[AB]3{side.upper()}{ip:d}")  # Q3A & Q3B HL-LHC

    madx.command.ealign(**kwargs)
    logger.trace("Clearing up error flag")
    madx.command.select(flag="error", clear=True)
