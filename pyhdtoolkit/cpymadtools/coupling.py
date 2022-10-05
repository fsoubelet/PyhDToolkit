"""
.. _cpymadtools-coupling:


Betatron Coupling Utilities
---------------------------

Module with functions to perform ``MAD-X`` actions through a `~cpymad.madx.Madx` object, that
retate to betatron coupling in the machine.
"""
from typing import Dict, Sequence, Tuple

import numpy as np
import tfs

from cpymad.madx import Madx
from loguru import logger
from optics_functions.coupling import check_resonance_relation, closest_tune_approach, coupling_via_cmatrix
from scipy import stats

from pyhdtoolkit.cpymadtools.constants import MONITOR_TWISS_COLUMNS
from pyhdtoolkit.cpymadtools.lhc import get_lhc_tune_and_chroma_knobs
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.twiss import get_pattern_twiss, get_twiss_tfs

# ----- General Use ----- #


def get_closest_tune_approach(
    madx: Madx,
    accelerator: str = None,
    sequence: str = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = True,
    run3: bool = False,
    explicit_targets: Tuple[float, float] = None,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
) -> float:
    """
    .. versionadded:: 0.16.0

    Provided with an active `~cpymad.madx.Madx` object, tries to match the tunes to their mid-fractional tunes,
    a.k.a tries to get them together. The difference between the final reached fractional tunes is the closest
    tune approach. This should not have any effect on the user's simulation, as the varied knobs are
    restored to their previous values after performing the CTA. This uses `~.tune.match_tunes_and_chromaticities`
    under the hood.

    .. note::
        This assumes the sequence has previously been matched to the user's desired working point, as if not
        explicitely given, the appropriate targets will be determined from the ``MAD-X`` internal tables.

    .. important::
        This is hard-coded to use the ``CHROM`` flag when performing matching, since we expect to be in
        the presence of betatron coupling. In this case, attempting to match chromaticities at the same time as the
        tunes might cause ``LMDIF`` to fail, as the knobs become dependent. For this reason, only tune matching is
        performed here, and chromaticities are voluntarily ignored.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        accelerator (Optional[str]): name of the accelerator, used to determmine knobs if *variables* is not given.
            Automatic determination will only work for `LHC` and `HLLHC`.
        sequence (str): name of the sequence you want to activate for the tune matching.
        varied_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine. An input
            could be ``["kqf", "ksd", "kqf", "kqd"]`` as they are common names used for quadrupole and sextupole
            strengths (focusing / defocusing) in most examples.
        telescopic_squeeze (bool): ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
            Squeeze configuration. Defaults to `True` since `v0.9.0`.
        run3 (bool): if set to `True`, uses the `LHC` Run 3 `*_op` knobs. Defaults to `False`.
        explicit_targets (Tuple[float, float]): if given, will be used as matching targets for `(Qx, Qy)`.
            Otherwise, the target is determined as the middle of the current fractional tunes. Defaults to
            `None`.
        step (float): step size to use when varying knobs.
        calls (int): max number of varying calls to perform.
        tolerance (float): tolerance for successfull matching.

    Returns:
        The closest tune approach, in absolute value.

    Example:
        .. code-block:: python

            >>> # Say we have set the LHC coupling knobs to 1e-3
            >>> dqmin = get_closest_tune_approach(
            ...     madx,
            ...     "lhc",                    # will find the knobs automatically
            ...     sequence="lhcb1",
            ...     telescopic_squeeze=True,  # influences the knobs definition
            ...     run3=True,                # influences the knobs definition (LHC Run 3)
            ... )
            0.001
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        lhc_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze, run3=run3
        )
        tune_knobs, _ = lhc_knobs[:2], lhc_knobs[2:]  # first two for tune & last two for chroma, not used

    logger.debug("Running TWISS to update SUMM and TWISS tables")
    madx.command.twiss(chrom=True)

    logger.debug("Saving knob values to restore after closest tune approach")
    varied_knobs = varied_knobs or tune_knobs  # if accelerator was given we've extracted this already
    saved_knobs: Dict[str, float] = {knob: madx.globals[knob] for knob in varied_knobs}
    logger.trace(f"Saved knobs are {saved_knobs}")

    if explicit_targets:
        q1, q2 = explicit_targets  # the integer part is used later on
    else:
        logger.trace("Retrieving tunes and chromaticities from internal tables")
        q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
        logger.trace(f"Retrieved values are q1 = {q1}, q2 = {q2}")

    logger.trace("Determining target tunes for closest approach")
    middle_of_fractional_tunes = (_fractional_tune(q1) + _fractional_tune(q2)) / 2
    qx_target = int(q1) + middle_of_fractional_tunes
    qy_target = int(q2) + middle_of_fractional_tunes
    logger.debug(f"Targeting tunes Qx = {qx_target}  |  Qy = {qy_target}")

    logger.debug("Performing closest tune approach routine, matching should fail at DeltaQ = dqmin")
    match_tunes_and_chromaticities(
        madx,
        accelerator,
        sequence,
        q1_target=qx_target,
        q2_target=qy_target,
        varied_knobs=varied_knobs,
        telescopic_squeeze=telescopic_squeeze,
        run3=run3,
        step=step,
        calls=calls,
        tolerance=tolerance,
    )

    logger.debug("Retrieving tune separation from internal tables")
    dqmin = madx.table.summ.q1[0] - madx.table.summ.q2[0] - (int(q1) - int(q2))
    cminus = abs(dqmin)
    logger.debug(f"Matching got to a Closest Tune Approach of {cminus:.5f}")

    logger.debug("Restoring saved knobs")
    with madx.batch():
        madx.globals.update(saved_knobs)
    madx.command.twiss(chrom=True)  # make sure TWISS and SUMM tables are returned to their original state

    return cminus


def get_cminus_from_coupling_rdts(
    madx: Madx,
    patterns: Sequence[str] = [""],
    method: str = "teapot",
    qx: float = None,
    qy: float = None,
    filtering: float = 0,
) -> float:
    """
    .. versionadded:: 0.20.0

    Computes and returns the :math:`|C^{-}|` from the machine's coupling RDTs. The
    closest tune approach is computed thanks to functionality from `optics_functions.coupling`.

    .. hint::
        A quick estimate of the :math:`|C^{-}|` is available in ``MAD-X`` as the ``dqmin``
        variable in the ``SUMM`` table. However this estimate is not accurate in all situations,
        and is the norm of a complex vector which is not approriate for comparisons or for
        normalizations, which is the use-case of this functions.

    .. note::
        If using the “calaga”, “teapot”, “teapot_franchi” or “franchi” method, then the returned
        value will be a real number.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        patterns (Sequence[str]): the different patterns (such as ``MQX`` or ``BPM``) of elements
            to use when computing the coupling RDTs. Defaults to `[""]` which will select and use
            all elements in the ``TWISS`` outputs.
        method (str): the method to use for the calculation of the :math:`C^{-}`. Defaults to
            `teapot`, which is the default of `~optics_functions.coupling.closest_tune_approach`.
        qx (float): the horizontal tune. Defaults to `None`, in which case the value will be taken
            from the ``SUMM`` table.
        qy (float): the vertical tune. Defaults to `None`, in which case the value will be taken
            from the ``SUMM`` table.
        filtering (float): If non-zero value is given, applies outlier filtering of BPMs based on
            the abs. value of the coupling RTDs before computing the :math:`C^{-}`. The given value
            corresponds to the std. dev. :math:`\\sigma` outside of which to filter out a BPM.
            Defaults to 0, which means no filtering.

    Returns:
        The calculated :math:`|C^{-}|` value.

    Examples:

        To compute the :math:`|C^{-}|` taking in consideration all elements in the sequence:

        .. code-block:: python

            >>> complex_cminus = get_cminus_from_coupling_rdts(madx)


        To simulate the calculation from a measurement, with RDTs computed at BPMs only:

        .. code-block:: python

            >>> complex_cminus = get_cminus_from_coupling_rdts(madx, patterns=["^BPM.*B[12]$"])
    """
    logger.debug(f"Getting coupling RDTs at selected elements thoughout the machine")
    twiss_with_rdts = get_pattern_twiss(madx, patterns=patterns, columns=MONITOR_TWISS_COLUMNS, chrom=True)
    twiss_with_rdts.columns = twiss_with_rdts.columns.str.upper()  # optics_functions needs capitalized names
    twiss_with_rdts[["F1001", "F1010"]] = coupling_via_cmatrix(twiss_with_rdts, output=["rdts"])

    # Get tunes values from SUMM table if not provided
    qx = qx or madx.table.summ.q1[0]
    qy = qy or madx.table.summ.q2[0]

    # Do this following line here as if done above, merging model erases headers
    logger.debug("Filtering out BPMs that do not respect the resonance relation")
    twiss_with_rdts.headers["LENGTH"] = 26659  # LHC length, will be needed later
    twiss_with_rdts = check_resonance_relation(twiss_with_rdts, to_nan=True).dropna()

    if filtering:
        logger.debug(f"Filtering out BPMs with RDTs outside of {filtering:f} std. dev.")
        twiss_with_rdts = _filter_outlier_bpms_from_coupling_rdts(twiss_with_rdts, filtering)

    # Now we do the closest tune approach calculation -> adds DELTAQMIN column to df
    logger.debug(f"Calculating CTA via optics_functions, with method '{method}'")
    dqmin_df = closest_tune_approach(twiss_with_rdts, qx=qx, qy=qy, method=method)

    # If we use a method that returns complex values, we have to average on the abs of these values!!
    if method not in ["calaga", "teapot", "teapot_franchi", "franchi"]:
        logger.debug(f"Taking module of values, as method '{method}' returns complex values")
        dqmin_df = dqmin_df.abs()

    # Now we can take the mean of the DELTAQMIN column
    return dqmin_df.DELTAQMIN.mean()


def match_no_coupling_through_ripkens(
    madx: Madx, sequence: str = None, location: str = None, vary_knobs: Sequence[str] = None
) -> None:
    """
    .. versionadded:: 0.16.0

    Matching routine to get cross-term Ripken parameters :math:`\\beta_{12}` and :math:`\\beta_{21}`
    to be 0 at a given location.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): name of the sequence to activate for the matching.
        location (str): the name of the element at which one wants the cross-term Ripkens to be 0.
        vary_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` routine.

    Example:
        .. code-block:: python

            >>> match_no_coupling_through_ripkens(
            ...     madx, sequence="lhcb1", location="IP5", vary_knobs=["kqsx.3l5", "kqsx.3r5"]
            ... )
    """
    logger.debug(f"Matching Ripken parameters for no coupling at location {location}")
    logger.debug("Creating macro to update Ripkens")
    madx.input("do_ripken: macro = {twiss, ripken=True;}")  # cpymad needs .input for macros

    logger.debug("Matching Parameters")
    madx.command.match(sequence=sequence, use_macro=True, chrom=True)
    for knob in vary_knobs:
        madx.command.vary(name=knob)
    madx.command.use_macro(name="do_ripken")
    madx.input(f"constraint, expr=table(twiss, {location}, beta12)=0")  # need input else includes " and fails
    madx.input(f"constraint, expr=table(twiss, {location}, beta21)=0")  # need input else includes " and fails
    madx.command.lmdif(calls=500, tolerance=1e-21)
    madx.command.endmatch()


def get_coupling_rdts(madx: Madx, **kwargs) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.20.0

    Computed the coupling Resonance Driving Tensors (RDTs) :math:`f_{1001}` and :math:`f_{1010}`
    at all elements in the currently active sequence from a ``TWISS`` call.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        **kwargs: any keyword argument will be transmitted to the ``TWISS`` command in ``MAD-X``.
            Note that ``CHROM`` is already provided as it is needed for the RDTs' calculation.

    Returns:
        A `~tfs.TfsDataFrame` with columns of the ``TWISS`` table, and two complex columns for the
        ``F1001`` and ``f1010`` RDTs.

    Example:
        .. code-block:: python

            >>> twiss_rdts = get_coupling_rdts(madx)
    """
    twiss_tfs = get_twiss_tfs(madx, chrom=True, **kwargs)
    twiss_tfs[["F1001", "F1010"]] = coupling_via_cmatrix(twiss_tfs, output=["rdts"])
    return twiss_tfs


# ----- Helpers ----- #


def _fractional_tune(tune: float) -> float:
    """
    Returns only the fractional part *tune*.

    Args:
        tune (float): tune value.

    Returns:
        The fractional part.

    Example:
        .. code-block:: python

            >>> _fractional_tune(62.31)
            0.31
    """
    return tune - int(tune)  # ok since int truncates to lower integer


def _filter_outlier_bpms_from_coupling_rdts(twiss_df: tfs.TfsDataFrame, stdev: float = 3) -> tfs.TfsDataFrame:
    """Only keep BPMs for which the abs. value of coupling RDTs is no further than `stdev` sigma from its mean.Example:

    .. note::
        This expects the `twiss_df` to have ``F1001`` and ``F1010`` complex columns.
    """
    logger.debug("Filtering out outlier BPMs based on coupling RDTs")
    df = twiss_df.copy(deep=True)
    df = df[np.abs(stats.zscore(df.F1001.abs())) < stdev]
    df = df[np.abs(stats.zscore(df.F1010.abs())) < stdev]
    removed = len(twiss_df) - len(df)
    if removed > 0:
        logger.debug(f"{removed} BPMs removed due to outlier coupling RDTs")
    return df
