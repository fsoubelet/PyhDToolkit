"""
Module cpymadtools.matching
---------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X matchings with a cpymad.madx.Madx object.
"""
from typing import Dict, Sequence, Tuple

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def get_lhc_tune_and_chroma_knobs(
    accelerator: str, beam: int = 1, telescopic_squeeze: bool = False
) -> Tuple[str, str, str, str]:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Get names of knobs needed to match tunes and chromaticities as a tuple of strings.

    Args:
        accelerator (str): Accelerator either 'LHC' (dQ[xy], dQp[xy] knobs) or 'HLLHC'
            (kqt[fd], ks[fd] knobs).
        beam (int): Beam to use, for the knob names.
        telescopic_squeeze (bool): if set to True, returns the knobs for Telescopic Squeeze configuration.
            Defaults to False.

    Returns:
        Tuple of strings with knobs for `(qx, qy, dqx, dqy)`.
    """
    beam = 2 if beam == 4 else beam
    suffix = "_sq" if telescopic_squeeze else ""

    if accelerator.upper() not in ("LHC", "HLLHC"):
        logger.error("Invalid accelerator name, only 'LHC' and 'HLLHC' implemented")
        raise NotImplementedError(f"Accelerator '{accelerator}' not implemented.")

    return {
        "LHC": (
            f"dQx.b{beam}{suffix}",
            f"dQy.b{beam}{suffix}",
            f"dQpx.b{beam}{suffix}",
            f"dQpy.b{beam}{suffix}",
        ),
        "HLLHC": (
            f"kqtf.b{beam}{suffix}",
            f"kqtd.b{beam}{suffix}",
            f"ksf.b{beam}{suffix}",
            f"ksd.b{beam}{suffix}",
        ),
    }[accelerator.upper()]


def match_tunes_and_chromaticities(
    madx: Madx,
    accelerator: str = None,
    sequence: str = None,
    q1_target: float = None,
    q2_target: float = None,
    dq1_target: float = None,
    dq2_target: float = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = False,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
) -> None:
    """
    Provided with an active `cpymad` class after having ran a script, will run an additional
    matching command to reach the provided values for tunes and chromaticities.

    Tune matching is always performed. If chromaticity target values are given, then a matching is done
    for them, followed by an additionnal matching for both tunes and chromaticities.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        accelerator (str): name of the accelerator, used to determmine knobs if 'variables' not given.
            Automatic determination will only work for LHC and HLLHC.
        sequence (str): name of the sequence you want to activate for the tune matching.
        q1_target (float): horizontal tune to match to.
        q2_target (float): vertical tune to match to.
        dq1_target (float): horizontal chromaticity to match to.
        dq2_target (float): vertical chromaticity to match to.
        varied_knobs (Sequence[str]): the variables names to 'vary' in the MADX routine. An input
            could be ["kqf", "ksd", "kqf", "kqd"] as they are common names used for quadrupole and
            sextupole strengths (foc / defoc) in most examples.
        telescopic_squeeze (bool): LHC specific. If set to True, uses the (HL)LHC knobs for Telescopic
            Squeeze configuration. Defaults to False, but will default to True in a later release.
        step (float): step size to use when varying knobs.
        calls (int): max number of varying calls to perform.
        tolerance (float): tolerance for successfull matching.
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        varied_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze
        )

    def match(*args, **kwargs):
        """Create matching commands for kwarg targets, varying the given args."""
        logger.debug(f"Executing matching commands, using sequence '{sequence}'")
        madx.command.match(chrom=True)
        logger.trace(f"Targets are given as {kwargs}")
        madx.command.global_(sequence=sequence, **kwargs)
        for variable_name in args:
            logger.trace(f"Creating vary command for knob '{variable_name}'")
            madx.command.vary(name=variable_name, step=step)
        madx.command.lmdif(calls=calls, tolerance=tolerance)
        madx.command.endmatch()
        logger.trace("Performing routine TWISS")
        madx.twiss()  # prevents errors if the user forget to do so before querying tables

    if q1_target and q2_target and dq1_target and dq2_target:
        logger.info(
            f"Doing combined matching to Qx={q1_target}, Qy={q2_target}, "
            f"dqx={dq1_target}, dqy={dq2_target} for sequence '{sequence}'"
        )
        logger.trace(f"Vary knobs sent are {varied_knobs}")
        match(*varied_knobs, q1=q1_target, q2=q2_target, dq1=dq1_target, dq2=dq2_target)

    elif q1_target and q2_target:
        logger.info(f"Matching tunes to Qx={q1_target}, Qy={q2_target} for sequence '{sequence}'")
        logger.trace(f"Vary knobs sent are {varied_knobs[:2]}")
        match(*varied_knobs[:2], q1=q1_target, q2=q2_target)  # first two in varied_knobs are tune knobs


def get_closest_tune_approach(
    madx: Madx,
    accelerator: str = None,
    sequence: str = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = False,
    explicit_targets: Tuple[float, float] = None,
    step: float = 1e-7,
    calls: float = 100,
    tolerance: float = 1e-21,
) -> float:
    """
    Provided with an active `cpymad` class after having ran a script, tries to match the tunes to
    their mid-fractional tunes. The difference between this mid-tune and the actual matched tune is the
    closest tune approach.

    NOTA BENE: This assumes your lattice has previously been matched to desired tunes and chromaticities,
    as it will determine the appropriate targets from the Madx instance's internal tables.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        accelerator (str): name of the accelerator, used to determmine knobs if 'variables' not given.
            Automatic determination will only work for LHC and HLLHC.
        sequence (str): name of the sequence you want to activate for the tune matching.
        varied_knobs (Sequence[str]): the variables names to 'vary' in the MADX routine. An input
            could be ["kqf", "ksd", "kqf", "kqd"] as they are common names used for quadrupole and
            sextupole strengths (foc / defoc) in most examples.
        telescopic_squeeze (bool): LHC specific. If set to True, uses the (HL)LHC knobs for Telescopic
            Squeeze configuration. Defaults to False.
        explicit_targets (Tuple[float, float]): if given, will be used as matching targets for Qx, Qy.
            Otherwise, the target is determined as the middle of the current fractional tunes. Defaults to
            None.
        step (float): step size to use when varying knobs.
        calls (int): max number of varying calls to perform.
        tolerance (float): tolerance for successfull matching.

    Returns:
        The closest tune approach, in absolute value.
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        varied_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze
        )

    logger.debug("Saving knob values to restore after closest tune approach")
    saved_knobs: Dict[str, float] = {knob: madx.globals[knob] for knob in varied_knobs}
    logger.trace(f"Saved knobs are {saved_knobs}")

    if explicit_targets:
        qx_target, qy_target = explicit_targets
        q1, q2 = qx_target, qy_target  # the integer part is used later on
    else:
        logger.trace("Retrieving tunes and chromaticities from internal tables")
        q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
        dq1, dq2 = madx.table.summ.dq1[0], madx.table.summ.dq2[0]
        logger.trace(f"Retrieved values are q1 = {q1}, q2 = {q2}, dq1 = {dq1}, dq2 = {dq2}")

        logger.trace("Determining target tunes for closest approach")
        middle_of_fractional_tunes = (_fractional_tune(q1) + _fractional_tune(q2)) / 2
        qx_target = int(q1) + middle_of_fractional_tunes
        qy_target = int(q2) + middle_of_fractional_tunes
    logger.debug(f"Targeting tunes Qx = {qx_target}  |  Qy = {qy_target}")

    logger.info("Performing closest tune approach routine, matching should fail at DeltaQ = dqmin")
    match_tunes_and_chromaticities(
        madx,
        accelerator,
        sequence,
        qx_target,
        qy_target,
        # dq1,  # remove?
        # dq2,  # remove?
        varied_knobs=varied_knobs,
        step=step,
        calls=calls,
        tolerance=tolerance,
    )

    logger.debug("Retrieving tune separation from internal tables")
    dqmin = madx.table.summ.q1[0] - madx.table.summ.q2[0] - (int(q1) - int(q2))

    logger.info("Restoring saved knobs")
    for knob, knob_value in saved_knobs.items():
        madx.globals[knob] = knob_value
    madx.twiss()

    return abs(dqmin)


# ----- Helpers ----- #


def _fractional_tune(tune: float) -> float:
    """
    Return only the fractional part of a tune value.

    Args:
        tune (float): tune value.

    Returns:
        The fractional part.
    """
    return tune - int(tune)  # ok since int truncates to lower integer
