"""
Module cpymadtools.errors
-------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X errors setups and manipulatioins with a cpymad.madx.Madx object,
mainly for LHC and HLLHC machines.
"""
from loguru import logger

try:
    from cpymad.madx import Madx
except ModuleNotFoundError:
    Madx = None


# ----- Utlites ----- #


def switch_magnetic_errors(cpymad_instance: Madx, **kwargs) -> None:
    """
    CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Applies magnetic field orders. This will only work for LHC and HLLHC machines.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.

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
                logger.trace(f"Setting global for '{name}'")
                cpymad_instance.globals[f"ON_{name}"] = int(kwargs.get(name, ab_default))