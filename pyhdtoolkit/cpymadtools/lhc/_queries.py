"""
.. _lhc-queries:

**Querying Utilities**

The functions below are settings query utilities for the ``LHC``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from pyhdtoolkit.cpymadtools import twiss
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
from pyhdtoolkit.cpymadtools.lhc._setup import lhc_orbit_variables
from pyhdtoolkit.cpymadtools.utils import _get_k_strings

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cpymad.madx import Madx
    from tfs import TfsDataFrame


def get_magnets_powering(
    madx: Madx, /, patterns: Sequence[str] = [r"^mb\.", r"^mq\.", r"^ms\."], brho: str | float | None = None, **kwargs
) -> TfsDataFrame:
    r"""
    .. versionadded:: 0.17.0

    Gets the TWISS table with additional defined columns for the given *patterns*.

    Hint
    ----
        Here are below certain useful patterns for the ``LHC`` and their meaning:

        * ``^mb\.`` :math:`\rightarrow` main bends.
        * ``^mq\.`` :math:`\rightarrow` main quadrupoles.
        * ``^ms\.`` :math:`\rightarrow` main sextupoles.
        * ``^mb[rswx]`` :math:`\rightarrow` separation dipoles.
        * ``^mq[mwxy]`` :math:`\rightarrow` insertion quads.
        * ``^mqt.1[23]`` :math:`\rightarrow` short tuning quads (12 & 13).
        * ``^mqtl`` :math:`\rightarrow` long  tuning quads.
        * ``^mcbx`` :math:`\rightarrow` crossing scheme magnets.
        * ``^mcb[cy]`` :math:`\rightarrow` crossing scheme magnets.

        To make no selection, one can give ``patterns=("")`` and this will give back
        the results for *all* elements. One can also give a specific magnet's exact
        name to include it in the results.

    Note
    ----
        The ``TWISS`` flag will be fully cleared after running this function.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    patterns : Sequence[str]
        A list of regex patterns to define which elements should be selected
        and included in the returned table. Defaults to selecting the main
        bends, quads and sextupoles. See the hint admonition above for useful
        patterns to select specific ``LHC`` magnet families.
    brho : Union[str, float], optional
        An explicit definition for the magnetic rigidity in :math:`Tm^{-1}`.
        If not given, it will be assumed that a ``brho`` quantity is defined
        in the ``MAD-X`` globals and this one will be used.
    **kwargs
        Any keyword argument will be passed to `~.twiss.get_pattern_twiss` and
        later on to the ``TWISS`` command executed in ``MAD-X``.

    Returns
    -------
    TfsDataFrame
        A `~tfs.TfsDataFrame` of the ``TWISS`` table, with the relevant newly
        defined columns and including the elements matching the regex *patterns*
        that were provided.

    Example
    -------
        .. code-block:: python

            sextupoles_powering = get_magnets_powering(madx, patterns=[r"^ms\."])
    """
    logger.debug("Computing magnets field and powering limits proportions")
    new_colnames = ["name", "keyword", "ampere", "imax", "percent", "kn", "kmax", "integrated_field", "L"]
    new_colnames = list(set(new_colnames + kwargs.pop("columns", [])))  # in case user gives explicit columns
    _list_field_currents(madx, brho=brho)
    return twiss.get_pattern_twiss(madx, columns=new_colnames, patterns=patterns, **kwargs)


def query_arc_correctors_powering(madx: Madx, /) -> dict[str, float]:
    """
    .. versionadded:: 0.15.0

    Queries for the arc corrector strengths and returns their values as a
    percentage of their max powering. This is a port of one of the macros
    from the **corr_value.madx** file in the old toolkit.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.

    Returns
    -------
    dict[str, float]
        A `dict` with the percentage for each corrector.

    Example
    -------
        .. code-block:: python

            arc_knobs = query_arc_correctors_powering(madx)
    """
    logger.debug("Querying triplets correctors powering")
    result: dict[str, float] = {}

    logger.debug("Querying arc tune trim quadrupole correctors (MQTs) powering")
    k_mqt_max = 120 / madx.globals.brho  # 120 T/m
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqt_max for knob in LHC_KQTF_KNOBS})

    logger.debug("Querying arc short straight sections skew quadrupole correctors (MQSs) powering")
    k_mqs_max = 120 / madx.globals.brho  # 120 T/m
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqs_max for knob in LHC_KQS_KNOBS})

    logger.debug("Querying arc sextupole correctors (MSs) powering")
    k_ms_max = 1.280 * 2 / 0.017**2 / madx.globals.brho  # 1.28 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_ms_max for knob in LHC_KSF_KNOBS})

    logger.debug("Querying arc skew sextupole correctors (MSSs) powering")
    k_mss_max = 1.280 * 2 / 0.017**2 / madx.globals.brho  # 1.28 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mss_max for knob in LHC_KSS_KNOBS})

    logger.debug("Querying arc spool piece (skew) sextupole correctors (MCSs) powering")
    k_mcs_max = 0.471 * 2 / 0.017**2 / madx.globals.brho  # 0.471 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcs_max for knob in LHC_KCS_KNOBS})

    logger.debug("Querying arc spool piece (skew) octupole correctors (MCOs) powering")
    k_mco_max = 0.040 * 6 / 0.017**3 / madx.globals.brho  # 0.04 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mco_max for knob in LHC_KCO_KNOBS})

    logger.debug("Querying arc spool piece (skew) decapole correctors (MCDs) powering")
    k_mcd_max = 0.100 * 24 / 0.017**4 / madx.globals.brho  # 0.1 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcd_max for knob in LHC_KCD_KNOBS})

    logger.debug("Querying arc short straight sections octupole correctors (MOs) powering")
    k_mo_max = 0.29 * 6 / 0.017**3 / madx.globals.brho  # 0.29 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mo_max for knob in LHC_KO_KNOBS})
    return result


def query_triplet_correctors_powering(madx: Madx, /) -> dict[str, float]:
    """
    .. versionadded:: 0.15.0

    Queries for the triplet corrector strengths and returns their values
    as a percentage of their max powering. This is a port of one of the
    macros from the **corr_value.madx** file in the old toolkit.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.

    Returns
    -------
    dict[str, float]
        A `dict` with the percentage for each corrector.

    Example
    -------
        .. code-block:: python

            triplet_knobs = query_triplet_correctors_powering(madx)
    """
    logger.debug("Querying triplets correctors powering")
    result: dict[str, float] = {}

    logger.debug("Querying triplet skew quadrupole correctors (MQSXs) powering")
    k_mqsx_max = 1.360 / 0.017 / madx.globals.brho  # 1.36 T @ 17mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqsx_max for knob in LHC_KQSX_KNOBS})

    logger.debug("Querying triplet sextupole correctors (MCSXs) powering")
    k_mcsx_max = 0.028 * 2 / 0.017**2 / madx.globals.brho  # 0.028 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcsx_max for knob in LHC_KCSX_KNOBS})

    logger.debug("Querying triplet skew sextupole correctors (MCSSXs) powering")
    k_mcssx_max = 0.11 * 2 / 0.017**2 / madx.globals.brho  # 0.11 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcssx_max for knob in LHC_KCSSX_KNOBS})

    logger.debug("Querying triplet octupole correctors (MCOXs) powering")
    k_mcox_max = 0.045 * 6 / 0.017**3 / madx.globals.brho  # 0.045 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcox_max for knob in LHC_KCOX_KNOBS})

    logger.debug("Querying triplet skew octupole correctors (MCOSXs) powering")
    k_mcosx_max = 0.048 * 6 / 0.017**3 / madx.globals.brho  # 0.048 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcosx_max for knob in LHC_KCOSX_KNOBS})

    logger.debug("Querying triplet decapole correctors (MCTXs) powering")
    k_mctx_max = 0.01 * 120 / 0.017**5 / madx.globals.brho  # 0.010 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mctx_max for knob in LHC_KCTX_KNOBS})
    return result


def get_current_orbit_setup(madx: Madx, /) -> dict[str, float]:
    """
    .. versionadded:: 0.8.0

    Get the current values for the (HL)LHC orbit variables. Initial
    implementation credits go to :user:`Joschua Dilly <joschd>`.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.

    Returns
    -------
    dict[str, float]
        A `dict` of all orbit variables set, and their values as set
        in the ``MAD-X`` globals.

    Example
    -------
        .. code-block:: python

            orbit_setup = get_current_orbit_setup(madx)
    """
    logger.debug("Extracting orbit variables from global table")
    variables, specials = lhc_orbit_variables()
    return {orbit_variable: madx.globals[orbit_variable] for orbit_variable in variables + list(specials.keys())}


# ----- Helpers ----- #


def _list_field_currents(madx: Madx, /, brho: str | float | None = None) -> None:
    """
    Creates additional columns for the ``TWISS`` table with the magnets' total
    fields and currents, to help later on determine which proportion of their
    maximum powering the current setting is using. This is an implementation of
    the old utility script located in the toolkit on AFS at
    **/afs/cern.ch/eng/lhc/optics/V6.503/toolkit/list_fields_currents.madx**.

    Important
    ---------
        Certain quantities are assumed to be defined in the ``MAD-X`` globals,
        such as ``brho``, or available in the magnets definition, such as ``calib``.
        For this reason, this script most likely only works for the ``(HL)LHC``
        sequences where those are defined.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    brho : Union[str, float], optional
        An explicit definition for the magnetic rigidity in :math:`Tm^{-1}`.
        If not given, it will be assumed that a ``brho`` quantity is defined
        in the ``MAD-X`` globals and this one will be used.
    """
    logger.debug("Creating additional TWISS table columns for magnets' fields and currents")

    if brho is not None:
        logger.trace(f"Setting 'brho' to explicitely defined '{brho}'")
        madx.globals["brho"] = brho

    # Define strength := table(twiss, k0l) + ... + table(twiss, k5sl) +  table(twiss, hkick)  +  table(twiss, vkick);
    madx.globals["strength"] = (
        " + ".join(f"table(twiss, {a.lower()})" for a in _get_k_strings(stop=6))
        + " +  table(twiss, hkick)  +  table(twiss, vkick)"
    )

    # All here are given as strings to make it deferred expressions in MAD-X
    madx.globals["epsilon"] = 1e-20  # to avoid divisions by zero
    madx.globals["length"] = "table(twiss, l) + table(twiss, lrad) + epsilon"
    madx.globals["kmaxx"] = "table(twiss, kmax) + epsilon"
    madx.globals["calibration"] = "table(twiss, calib) + epsilon"
    madx.globals["kn"] = "abs(strength) / length"
    # madx.globals["rho"] = "kn / (kn + epsilon) / (kn + epsilon)"

    madx.globals["field"] = "kn * brho"
    madx.globals["percent"] = "field * 100 / (kmaxx + epsilon)"
    madx.globals["ampere"] = "field / calibration"
    madx.globals["imax"] = "kmaxx / calibration"
    madx.globals["integrated_field"] = "field * length"


def _knob_value(madx: Madx, /, knob: str) -> float:
    """
    Queryies the current value of a given *knob* name in the ``MAD-X`` process,
    and defaults to 0 (as ``MAD-X`` does) in case that knob has not been defined
    in the current process.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    knob : str
        The name the knob to get the value for.

    Returns
    -------
    float
        The knob value if it was defined, otherwise 0.

    Example
    -------
        .. code-block:: python

            _knob_value(madx, knob="underfined_for_sure")  # returns 0
    """
    try:
        return madx.globals[knob]
    except KeyError:  # cpymad gives a 'Variable not defined: var_name'
        return 0
