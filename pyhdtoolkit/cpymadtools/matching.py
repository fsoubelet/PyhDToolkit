"""
Module cpymadtools.matching
---------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X matchings with a cpymad.madx.Madx object.
"""
from typing import Dict, Sequence, Tuple

from loguru import logger

try:
    from cpymad.madx import Madx
except ModuleNotFoundError:
    Madx = None


# ----- Utlites ----- #


def get_tune_and_chroma_knobs(accelerator: str, beam: int = 1) -> Tuple[str, str, str, str]:
    """
    CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Get names of knobs needed to match tunes and chromaticities as a tuple of strings.

    Args:
        accelerator (str): Accelerator either 'LHC' (dQ[xy], dQp[xy] knobs) or 'HLLHC'
            (kqt[fd], ks[fd] knobs).
        beam (int): Beam to use, for the knob names.

    Returns:
        Tuple of strings with knobs for `(qx, qy, dqx, dqy)`.
    """
    beam = 2 if beam == 4 else beam

    if accelerator.upper() not in ("LHC", "HLLHC"):
        logger.error("Invalid accelerator name, only 'LHC' and 'HLLHC' implemented")
        raise NotImplementedError(f"Accelerator '{accelerator}' not implemented.")

    return {
        "LHC": (f"dQx.b{beam}", f"dQy.b{beam}", f"dQpx.b{beam}", f"dQpy.b{beam}"),
        "HLLHC": (f"kqtf.b{beam}", f"kqtd.b{beam}", f"ksf.b{beam}", f"ksd.b{beam}"),
    }[accelerator.upper()]


def match_tunes_and_chromaticities(
    cpymad_instance: Madx,
    accelerator: str = None,
    sequence: str = None,
    q1_target: float = None,
    q2_target: float = None,
    dq1_target: float = None,
    dq2_target: float = None,
    varied_knobs: Sequence[str] = None,
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
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
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
        step (float): step size to use when varying knobs.
        calls (int): max number of varying calls to perform.
        tolerance (float): tolerance for successfull matching.
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        varied_knobs = get_tune_and_chroma_knobs(accelerator=accelerator, beam=int(sequence[-1]))

    def match(*args, **kwargs):
        logger.debug(f"Executing matching commands, using sequence '{sequence}'")
        cpymad_instance.command.match(chrom=True)
        logger.trace(f"Targets are given as {kwargs}")
        cpymad_instance.command.global_(sequence=sequence, **kwargs)
        for variable_name in args:
            logger.trace(f"Creating vary command for knob '{variable_name}'")
            cpymad_instance.command.vary(name=variable_name, step=step)
        cpymad_instance.command.lmdif(calls=calls, tolerance=tolerance)
        cpymad_instance.command.endmatch()
        logger.trace("Performing routine TWISS")
        cpymad_instance.twiss()  # prevents errors if the user forget to do so before querying tables

    if q1_target and q2_target and dq1_target and dq2_target:
        logger.info(
            f"Doing combined matching to Qx = {q1_target}, Qy = {q2_target}, "
            f"dqx = {dq1_target}, dqy = {dq2_target} for sequence '{sequence}'"
        )
        logger.trace(f"Vary knobs sent are {varied_knobs}")
        match(*varied_knobs, q1=q1_target, q2=q2_target, dq1=dq1_target, dq2=dq2_target)

    elif q1_target and q2_target:
        logger.info(f"Matching tunes to Qx = {q1_target}, Qy = {q2_target} for sequence '{sequence}'")
        logger.trace(f"Vary knobs sent are {varied_knobs[:2]}")
        match(*varied_knobs[:2], q1=q1_target, q2=q2_target)  # first two in varied_knobs are tune knobs


def get_closest_tune_approach(
    cpymad_instance: Madx,
    accelerator: str = None,
    sequence: str = None,
    varied_knobs: Sequence[str] = None,
    step: float = 1e-7,
    calls: float = 100,
    tolerance: float = 1e-21,
) -> float:
    """
    Provided with an active `cpymad` class after having ran a script, tries to match the tunes to
    their mid-fractional tunes. The difference between this mid-tune and the actual matched tune is the
    closest tune approach.

    NOTA BENE: This assumes your lattice has previously been matched to desired tunes and
    chromaticities, as it will determine the appropriate targets from the Madx instance's internal tables.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        accelerator (str): name of the accelerator, used to determmine knobs if 'variables' not given.
            Automatic determination will only work for LHC and HLLHC.
        sequence (str): name of the sequence you want to activate for the tune matching.
        varied_knobs (Sequence[str]): the variables names to 'vary' in the MADX routine. An input
            could be ["kqf", "ksd", "kqf", "kqd"] as they are common names used for quadrupole and
            sextupole strengths (foc / defoc) in most examples.
        step (float): step size to use when varying knobs.
        calls (int): max number of varying calls to perform.
        tolerance (float): tolerance for successfull matching.

    Returns:
        The closest tune approach, in absolute value.
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        varied_knobs = get_tune_and_chroma_knobs(accelerator=accelerator, beam=int(sequence[-1]))

    logger.debug("Saving knob values to restore after closest tune approach")
    saved_knobs: Dict[str, float] = {knob: cpymad_instance.globals[knob] for knob in varied_knobs}
    logger.trace(f"Saved knobs are {saved_knobs}")

    logger.debug("Retrieving tunes and chromaticities from internal tables")
    q1, q2 = cpymad_instance.table.summ.q1[0], cpymad_instance.table.summ.q2[0]
    dq1, dq2 = cpymad_instance.table.summ.dq1[0], cpymad_instance.table.summ.dq2[0]
    logger.trace(f"Retrieved values are q1 = {q1}, q2 = {q2}, dq1 = {dq1}, dq2 = {dq2}")

    logger.debug("Determining target tunes for closest approach")
    middle_of_fractional_tunes = (_fractional_tune(q1) + _fractional_tune(q2)) / 2
    qx_target = int(q1) + middle_of_fractional_tunes
    qy_target = int(q2) + middle_of_fractional_tunes
    logger.trace(f"Targeting tunes Qx = {qx_target}  |  Qy = {qy_target}")

    logger.info("Performing closest tune approach routine, matching should fail at DeltaQ = dqmin")
    match_tunes_and_chromaticities(
        cpymad_instance,
        accelerator,
        sequence,
        qx_target,
        qy_target,
        dq1,
        dq2,
        varied_knobs,
        step,
        calls,
        tolerance,
    )

    logger.debug("Retrieving tune separation from internal tables")
    dqmin = cpymad_instance.table.summ.q1[0] - cpymad_instance.table.summ.q2[0] - (int(q1) - int(q2))

    logger.info("Restoring saved knobs")
    for knob, knob_value in saved_knobs.items():
        cpymad_instance.globals[knob] = knob_value
    cpymad_instance.twiss()

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