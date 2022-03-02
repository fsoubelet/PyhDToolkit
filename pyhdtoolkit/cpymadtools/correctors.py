"""
.. _cpymadtools-correctors:


Correctors
----------

Module with functions to perform ``MAD-X`` correctors-related operations and manipulations
through a `~cpymad.madx.Madx` object, mainly for LHC and HLLHC machines.
"""
from typing import Dict, List, Sequence

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.constants import (
    LHC_KCD_KNOBS,
    LHC_KCO_KNOBS,
    LHC_KCOSX_KNOBS,
    LHC_KCOX_KNOBS,
    LHC_KCS_KNOBS,
    LHC_KCSSX_KNOBS,
    LHC_KCSX_KNOBS,
    LHC_KCTX_KNOBS,
    LHC_KO_KNOBS,
    LHC_KQS_KNOBS,
    LHC_KQSX_KNOBS,
    LHC_KQTF_KNOBS,
    LHC_KSF_KNOBS,
    LHC_KSS_KNOBS,
)

__all__ = [
    "query_arc_correctors_powering",
    "query_triplet_correctors_powering",
]


def query_triplet_correctors_powering(madx: Madx) -> Dict[str, float]:
    """
    Queries for the triplet corrector strengths and returns their values as a percentage of
    their max powering. This is a port of one of the **corr_value.madx** file's macros.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object with an
            active (HL)LHC sequence.

    Returns:
        A `dict` with the percentage for each corrector.

    Example:
        .. code-block:: python

            >>> triplet_knobs = query_triplet_correctors_powering(madx)
    """
    logger.debug("Querying triplets correctors powering")
    result: Dict[str, float] = {}

    logger.debug("Querying triplet skew quadrupole correctors (MQSXs) powering")
    k_mqsx_max = 1.360 / 0.017 / madx.globals.brho  # 1.36 T @ 17mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqsx_max for knob in LHC_KQSX_KNOBS})

    logger.debug("Querying triplet sextupole correctors (MCSXs) powering")
    k_mcsx_max = 0.028 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.028 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcsx_max for knob in LHC_KCSX_KNOBS})

    logger.debug("Querying triplet skew sextupole correctors (MCSSXs) powering")
    k_mcssx_max = 0.11 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.11 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcssx_max for knob in LHC_KCSSX_KNOBS})

    logger.debug("Querying triplet octupole correctors (MCOXs) powering")
    k_mcox_max = 0.045 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.045 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcox_max for knob in LHC_KCOX_KNOBS})

    logger.debug("Querying triplet skew octupole correctors (MCOSXs) powering")
    k_mcosx_max = 0.048 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.048 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcosx_max for knob in LHC_KCOSX_KNOBS})

    logger.debug("Querying triplet decapole correctors (MCTXs) powering")
    k_mctx_max = 0.01 * 120 / 0.017 ** 5 / madx.globals.brho  # 0.010 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mctx_max for knob in LHC_KCTX_KNOBS})
    return result


def query_arc_correctors_powering(madx: Madx) -> Dict[str, float]:
    """
    Queries for the arc corrector strengths and returns their values as a percentage of
    their max powering. This is a port of one of the **corr_value.madx** file's macros

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object with an
            active (HL)LHC sequence.

    Returns:
        A `dict` with the percentage for each corrector.

    Example:
        .. code-block:: python

            >>> arc_knobs = query_arc_correctors_powering(madx)
    """
    logger.debug("Querying triplets correctors powering")
    result: Dict[str, float] = {}

    logger.debug("Querying arc tune trim quadrupole correctors (MQTs) powering")
    k_mqt_max = 120 / madx.globals.brho  # 120 T/m
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqt_max for knob in LHC_KQTF_KNOBS})

    logger.debug("Querying arc short straight sections skew quadrupole correctors (MQSs) powering")
    k_mqs_max = 120 / madx.globals.brho  # 120 T/m
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqs_max for knob in LHC_KQS_KNOBS})

    logger.debug("Querying arc sextupole correctors (MSs) powering")
    k_ms_max = 1.280 * 2 / 0.017 ** 2 / madx.globals.brho  # 1.28 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_ms_max for knob in LHC_KSF_KNOBS})

    logger.debug("Querying arc skew sextupole correctors (MSSs) powering")
    k_mss_max = 1.280 * 2 / 0.017 ** 2 / madx.globals.brho  # 1.28 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mss_max for knob in LHC_KSS_KNOBS})

    logger.debug("Querying arc spool piece (skew) sextupole correctors (MCSs) powering")
    k_mcs_max = 0.471 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.471 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcs_max for knob in LHC_KCS_KNOBS})

    logger.debug("Querying arc spool piece (skew) octupole correctors (MCOs) powering")
    k_mco_max = 0.040 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.04 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mco_max for knob in LHC_KCO_KNOBS})

    logger.debug("Querying arc spool piece (skew) decapole correctors (MCDs) powering")
    k_mcd_max = 0.100 * 24 / 0.017 ** 4 / madx.globals.brho  # 0.1 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcd_max for knob in LHC_KCD_KNOBS})

    logger.debug("Querying arc short straight sections octupole correctors (MOs) powering")
    k_mo_max = 0.29 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.29 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mo_max for knob in LHC_KO_KNOBS})
    return result


# ----- Helpers ----- #


def _knob_value(madx: Madx, knob: str) -> float:
    """
    Queryies the current value of a given *knob* name in the ``MAD-X`` process, and defaults
    to 0 (as ``MAD-X`` does) in case that knob has not been defined in the current process.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        knob (str): the name the knob.

    Returns:
        The knob value if it was defined, otherwise 0.

    Example:
        .. code-block:: python

            >>> _knob_value(madx, knob="underfined_for_sure")
            0
    """
    try:
        return madx.globals[knob]
    except KeyError:  # cpymad gives a 'Variable not defined: var_name'
        return 0
