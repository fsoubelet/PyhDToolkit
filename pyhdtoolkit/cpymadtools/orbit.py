"""
Module cpymadtools.orbit
------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X orbit setup with a cpymad.madx.Madx object, mainly for LHC and
HLLHC machines.
"""
from typing import Dict, List, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.constants import LHC_CROSSING_SCHEMES

# ----- Utilities ----- #


def lhc_orbit_variables() -> Tuple[List[str], Dict[str, str]]:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Get the variable names used for orbit setup in the (HL)LHC.

    Returns:
        A tuple with a list of all orbit variables, and a dict of additional variables, that in the
        default configurations have the same value as another variable.
    """
    logger.trace("Returning (HL)LHC orbit variables")
    on_variables = (
        "crab1",
        "crab5",  # exists only in HL-LHC
        "x1",
        "sep1",
        "o1",
        "oh1",
        "ov1",
        "x2",
        "sep2",
        "o2",
        "oe2",
        "a2",
        "oh2",
        "ov2",
        "x5",
        "sep5",
        "o5",
        "oh5",
        "ov5",
        "phi_IR5",
        "x8",
        "sep8",
        "o8",
        "a8",
        "sep8h",
        "x8v",
        "oh8",
        "ov8",
        "alice",
        "sol_alice",
        "lhcb",
        "sol_atlas",
        "sol_cms",
    )
    variables = [f"on_{var}" for var in on_variables] + [f"phi_IR{ir:d}" for ir in (1, 2, 5, 8)]
    special = {
        "on_ssep1": "on_sep1",
        "on_xx1": "on_x1",
        "on_ssep5": "on_sep5",
        "on_xx5": "on_x5",
    }
    return variables, special


def setup_lhc_orbit(madx: Madx, scheme: str = "flat", **kwargs) -> Dict[str, float]:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Automated orbit setup for (hl)lhc runs, for some default schemes.
    Assumed that at least sequence and optics files have been called.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        scheme (str): the default scheme to apply, as defined in `LHC_CROSSING_SCHEMES`. Accepted values
            are keys of `LHC_CROSSING_SCHEMES`. Defaults to 'flat' (every orbit variable to 0).

    Keyword Args:
        All standard crossing scheme variables (on_x1, phi_IR1, etc). Values given here override the
        values in the default scheme configurations.

    Returns:
        A dictionary of all orbit variables set, and their values as set in the MAD-X globals.
    """
    if scheme not in LHC_CROSSING_SCHEMES.keys():
        logger.error(f"Invalid scheme parameter, should be one of {LHC_CROSSING_SCHEMES.keys()}")
        raise ValueError("Invalid scheme parameter given")

    logger.debug("Getting orbit variables")
    variables, special = lhc_orbit_variables()

    scheme_dict = LHC_CROSSING_SCHEMES[scheme]
    final_scheme = {}

    for orbit_variable in variables:
        variable_value = kwargs.get(orbit_variable, scheme_dict.get(orbit_variable, 0))
        logger.trace(f"Setting orbit variable '{orbit_variable}' to {variable_value}")
        # Sets value in MAD-X globals & returned dict, taken from scheme dict or kwargs if provided
        madx.globals[orbit_variable] = final_scheme[orbit_variable] = variable_value

    for special_variable, copy_from in special.items():
        special_variable_value = kwargs.get(special_variable, madx.globals[copy_from])
        logger.trace(f"Setting special orbit variable '{special_variable}' to {special_variable_value}")
        # Sets value in MAD-X globals & returned dict, taken from a given global or kwargs if provided
        madx.globals[special_variable] = final_scheme[special_variable] = special_variable_value

    return final_scheme


def get_current_orbit_setup(madx: Madx) -> Dict[str, float]:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Get the current values for the (HL)LHC orbit variales.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.

    Returns:
        A dictionary of all orbit variables set, and their values as set in the MAD-X globals.
    """
    logger.debug("Extracting orbit variables from global table")
    variables, specials = lhc_orbit_variables()
    return {
        orbit_variable: madx.globals[orbit_variable] for orbit_variable in variables + list(specials.keys())
    }
