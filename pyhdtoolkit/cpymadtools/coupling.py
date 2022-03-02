"""
.. _cpymadtools-coupling:


Betatron Coupling Utilities
---------------------------

Module with functions to perform ``MAD-X`` actions through a `~cpymad.madx.Madx` object, that
retate to betatron coupling in the machine.
"""
from typing import Dict, Sequence, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.lhc import get_lhc_tune_and_chroma_knobs
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities

__all__ = [
    "get_closest_tune_approach",
    "match_no_coupling_through_ripkens",
]

# ----- General Use ----- #


def get_closest_tune_approach(
    madx: Madx,
    accelerator: str = None,
    sequence: str = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = True,
    explicit_targets: Tuple[float, float] = None,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
) -> float:
    """
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
            Squeeze configuration. Defaults to `True` as of run III.
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

            >>> # Say we have set the coupling knobs to 1e-3
            >>> dqmin = get_closest_tune_approach(
            ...     madx,
            ...     "lhc",                    # will find the knobs automatically
            ...     sequence="lhcb1",
            ...     telescopic_squeeze=True,  # influences the knobs definition
            ... )
            0.001
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        lhc_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze
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


def match_no_coupling_through_ripkens(
    madx: Madx, sequence: str = None, location: str = None, vary_knobs: Sequence[str] = None
) -> None:
    """
    Matching routine to get cross-term Ripken parameters :math:`\\beta_{12}` and :math:`\\beta_{21}`
    to be 0 at a given location.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): name of the sequence to activate for the matching.
        location (str): the name of the element at which one wants the cross-term Ripkens to be 0.
        vary_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` routine.
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
