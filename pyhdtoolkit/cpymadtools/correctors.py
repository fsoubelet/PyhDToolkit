"""
Module cpymadtools.correctors
-----------------------------

Created on 2021.10.16
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X correctors-related operations and manipulations with a
cpymad.madx.Madx object, mainly for LHC and HLLHC machines.
"""
from typing import Dict, List, Sequence

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.constants import (
    LHC_KCOSX_KNOBS,
    LHC_KCOX_KNOBS,
    LHC_KCSSX_KNOBS,
    LHC_KCSX_KNOBS,
    LHC_KCTX_KNOBS,
    LHC_KQSX_KNOBS,
)


def query_triplet_correctors_powering(madx: Madx) -> Dict[str, float]:
    """
    This is a port of one of the `corr_value.madx` file's macros. It queries for the corrector strengths
    and returns their values as a percentage of their max powering.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object with an active (HL)LHC sequence.

    Returns:
        A dict with the percentage for each corrector.
    """
    logger.info("Querying triplets correctors powering")
    result: Dict[str, float] = {}

    logger.debug("Querying triplet skew quadrupole correctors (MQSXs) powering")
    k_mqsx_max = 1.360 / 0.017 / madx.globals.brho  # 1.36 T @ 17mm
    result.update({knob: 100 * madx.globals[knob] / k_mqsx_max for knob in LHC_KQSX_KNOBS})

    logger.debug("Querying triplet sextupole correctors (MCSXs) powering")
    k_mcsx_max = 0.028 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.028 T @ 17 mm
    result.update({knob: 100 * madx.globals[knob] / k_mcsx_max for knob in LHC_KCSX_KNOBS})

    logger.debug("Querying triplet skew sextupole correctors (MCSSXs) powering")
    k_mcssx_max = 0.11 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.11 T @ 17 mm
    result.update({knob: 100 * madx.globals[knob] / k_mcssx_max for knob in LHC_KCSX_KNOBS})

    logger.debug("Querying triplet octupole correctors (MCOXs) powering")
    k_mcox_max = 0.045 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.045 T @ 17 mm
    result.update({knob: 100 * madx.globals[knob] / k_mcox_max for knob in LHC_KCOX_KNOBS})

    logger.debug("Querying triplet skew octupole correctors (MCOSXs) powering")
    k_mcosx_max = 0.048 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.048 T @ 17 mm
    result.update({knob: 100 * madx.globals[knob] / k_mcosx_max for knob in LHC_KCOSX_KNOBS})

    logger.debug("Querying triplet decapole correctors (MCTXs) powering")
    k_mctx_max = 0.01 * 120 / 0.017 ** 5 / madx.globals.brho  # 0.010 T @ 17 mm
    result.update({knob: 100 * madx.globals[knob] / k_mctx_max for knob in LHC_KCTX_KNOBS})
    return result
