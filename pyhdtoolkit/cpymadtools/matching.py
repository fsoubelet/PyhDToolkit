"""
.. _cpymadtools-matching:

Matching Routines
-----------------

Module with functions to perform ``MAD-X`` matchings through a `~cpymad.madx.Madx` object.
"""
from typing import Dict, Optional, Sequence, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.utils import deprecated

__all__ = ["match_tunes_and_chromaticities"]

# ----- Utlites ----- #


@deprecated(message="Please use its equivalent from the 'cpymadtools.lhc' module.")
def get_lhc_tune_and_chroma_knobs(
    accelerator: str, beam: int = 1, telescopic_squeeze: bool = True
) -> Tuple[str, str, str, str]:
    """
    Gets names of knobs needed to match tunes and chromaticities as a tuple of strings,
    for the LHC or HLLHC machines. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    .. danger::
        This function is deprecated and will be removed in a future version. Please use
        its equivalent from the `~.cpymadtools.lhc` module.

    Args:
        accelerator (str): Accelerator either 'LHC' (dQ[xy], dQp[xy] knobs) or 'HLLHC'
            (kqt[fd], ks[fd] knobs).
        beam (int): Beam to use, for the knob names. Defaults to 1.
        telescopic_squeeze (bool): if set to `True`, returns the knobs for Telescopic
            Squeeze configuration. Defaults to `True` to reflect run III scenarios.

    Returns:
        A `tuple` of strings with knobs for ``(qx, qy, dqx, dqy)``.
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
    sequence: Optional[str] = None,
    q1_target: float = None,
    q2_target: float = None,
    dq1_target: float = None,
    dq2_target: float = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = True,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
) -> None:
    """
    Provided with an active `~cpymad.madx.Madx` object, will run relevant commands to match tunes
    and/or chromaticities. As target values are given, the function expects knob names to be provided,
    which are then used and varied by `MAD-X` to match the targets. This is a convenient wrapper around
    the ``MATCH`` command. For usage details, see the
    `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_.

    One can find example use of this function in the :ref:`lattice plotting <demo-accelerator-lattice>`,
    :ref:`rigid waist shift <demo-rigid-waist-shift>` or :ref:`phase space <demo-phase-space>` example
    galleries.

    .. important::
        If target tune values only are provided, then tune matching is performed with the provided knobs.
        If target chromaticity values only are provided, then chromaticity matching is performed with the
        provided knobs. If targets for both types are provided, then both are matched in a single call with
        the provided knobs.

    .. note::
        If the user wishes to perform different matching calls for each, then it is recommended to call this
        function as many times as necessary, with the appropriate targets.

        For instance, in some cases and machines some prefer to do a tune matching followed by a chromaticity matching,
        then followed by a combined matching. In this case the function should be called three times, once with tune
        targets and knobs, another time with chromaticity targets and knobs, then a final time with all of the above.

    .. note::
        When acting of either the ``LHC`` or ``HLLHC`` machines, the accelerator name can be provided and the vary
        knobs will be automatically set accordingly to the provided targets. Note that only the relevant knobs are
        set, so if tune targets only are provided, then tune knobs only will be used, and not chromaticity knobs.
        If explicit knobs are provided, these will always be used. On other machines the knobs should be provided
        explicitly, always.

    .. important::
        The matching is always performed with the ``CHROM`` option on.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        accelerator (Optional[str]): name of the accelerator, used to determmine knobs if *variables* is not given.
            Automatic determination will only work for `LHC` and `HLLHC`.
        sequence (str): name of the sequence you want to perform the matching for.
        q1_target (float): horizontal tune to match to.
        q2_target (float): vertical tune to match to.
        dq1_target (float): horizontal chromaticity to match to.
        dq2_target (float): vertical chromaticity to match to.
        varied_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine. An input
            could be ``["kqf", "ksd", "kqf", "kqd"]`` as they are common names used for quadrupole and sextupole
            strengths (focusing / defocusing) in most examples.
        telescopic_squeeze (bool): ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
            Squeeze configuration. Defaults to `True` as of run III.
        step (float): step size to use when varying knobs.
        calls (int): max number of varying calls to perform.
        tolerance (float): tolerance for successfull matching.

    Examples:
        Matching a dummy lattice (not LHC or HLLHC):

        .. code-block:: python

            >>> matching.match_tunes_and_chromaticities(
            ...     madx,
            ...     None,              # this is not LHC or HLLHC
            ...     sequence="CAS3",
            ...     q1_target=6.335,
            ...     q2_target=6.29,
            ...     dq1_target=100,
            ...     dq2_target=100,
            ...     varied_knobs=["kqf", "kqd", "ksf", "ksd"],
            ... )

        Matching the LHC lattice:

        .. code-block:: python

            >>> matching.match_tunes_and_chromaticities(
            ...     madx,
            ...     "lhc",                    # will find the knobs automatically
            ...     sequence="lhcb1",
            ...     q1_target=62.31,
            ...     q2_target=60.32,
            ...     dq1_target=2.0,
            ...     dq2_target=2.0,
            ...     telescopic_squeeze=True,  # influences the knobs definition
            ... )
    """
    if accelerator and not varied_knobs:
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        lhc_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze
        )
        tune_knobs, chroma_knobs = lhc_knobs[:2], lhc_knobs[2:]  # first two, last two

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
        madx.twiss(chrom=True)  # prevents errors if the user forgets to TWISS before querying tables

    if q1_target is not None and q2_target is not None and dq1_target is not None and dq2_target is not None:
        logger.debug(
            f"Doing combined matching to Qx={q1_target}, Qy={q2_target}, "
            f"dqx={dq1_target}, dqy={dq2_target} for sequence '{sequence}'"
        )
        varied_knobs = varied_knobs or lhc_knobs  # if accelerator was given we've extracted this already
        logger.trace(f"Vary knobs sent are {varied_knobs}")
        match(*varied_knobs, q1=q1_target, q2=q2_target, dq1=dq1_target, dq2=dq2_target)

    elif q1_target is not None and q2_target is not None:
        logger.debug(f"Matching tunes to Qx={q1_target}, Qy={q2_target} for sequence '{sequence}'")
        tune_knobs = varied_knobs or tune_knobs  # if accelerator was given we've extracted this already
        logger.trace(f"Vary knobs sent are {tune_knobs}")
        match(*tune_knobs, q1=q1_target, q2=q2_target)  # sent varied_knobs should be tune knobs

    elif dq1_target is not None and dq2_target is not None:
        logger.debug(f"Matching chromaticities to dq1={dq1_target}, dq2={dq2_target} for sequence {sequence}")
        chroma_knobs = varied_knobs or chroma_knobs  # if accelerator was given we've extracted this already
        logger.trace(f"Vary knobs sent are {chroma_knobs}")
        match(*chroma_knobs, dq1=dq1_target, dq2=dq2_target)  # sent varied_knobs should be chromaticity knobs


@deprecated(message="Please use its equivalent from the 'cpymadtools.coupling' module.")
def get_closest_tune_approach(
    madx: Madx,
    accelerator: Optional[str] = None,
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

    .. danger::
        This function is deprecated and will be removed in a future version. Please use
        its equivalent from the `~.cpymadtools.coupling` module.

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
        varied_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze
        )

    logger.debug("Running TWISS to update SUMM and TWISS tables")
    madx.command.twiss(chrom=True)

    logger.debug("Saving knob values to restore after closest tune approach")
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


# ----- Helpers ----- #

# TODO: remove this once deprecated 'get_closest_tune_approach' is removed as its the only thing using it
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
