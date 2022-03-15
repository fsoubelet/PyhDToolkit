"""
.. _cpymadtools-matching:

Matching Routines
-----------------

Module with functions to perform ``MAD-X`` matchings through a `~cpymad.madx.Madx` object.
"""
from typing import Dict, Optional, Sequence, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.lhc import get_lhc_tune_and_chroma_knobs

__all__ = ["match_tunes_and_chromaticities", "match_tunes", "match_chromaticities"]


# ----- Workhorse ----- #


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


# ----- Convenient Wrappers ----- #


def match_tunes(
    madx: Madx,
    accelerator: str = None,
    sequence: Optional[str] = None,
    q1_target: float = None,
    q2_target: float = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = True,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
):
    """
    Provided with an active `~cpymad.madx.Madx` object, will run relevant commands to match tunes to
    the desired target values.

    .. note::
        This is a wrapper around the `~.match_tunes_and_chromaticities` function. Refer to its documentation
        for usage details.

    .. important::
        The matching is always performed with the ``CHROM`` option on.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        accelerator (Optional[str]): name of the accelerator, used to determmine knobs if *variables* is not given.
            Automatic determination will only work for `LHC` and `HLLHC`.
        sequence (str): name of the sequence you want to perform the matching for.
        q1_target (float): horizontal tune to match to.
        q2_target (float): vertical tune to match to.
        varied_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine.
        telescopic_squeeze (bool): ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
            Squeeze configuration. Defaults to `True` as of run III.
        step (float): step size to use when varying knobs. Defaults to `1E-7`.
        calls (int): max number of varying calls to perform. Defaults to `100`.
        tolerance (float): tolerance for successfull matching. Defaults to `1E-21`.

    Examples:
        Matching a dummy lattice (not LHC or HLLHC):

        .. code-block:: python

            >>> matching.match_tunes(
            ...     madx,
            ...     None,              # this is not LHC or HLLHC
            ...     sequence="CAS3",
            ...     q1_target=6.335,
            ...     q2_target=6.29,
            ...     varied_knobs=["kqf", "kqd"],  # only tune knobs
            ... )

        Matching the LHC lattice:

        .. code-block:: python

            >>> matching.match_tunes(
            ...     madx,
            ...     "lhc",                    # will find the knobs automatically
            ...     sequence="lhcb1",
            ...     q1_target=62.31,
            ...     q2_target=60.32,
            ... )
    """
    match_tunes_and_chromaticities(
        madx=madx,
        accelerator=accelerator,
        sequence=sequence,
        q1_target=q1_target,
        q2_target=q2_target,
        dq1_target=None,
        dq2_target=None,
        varied_knobs=varied_knobs,
        telescopic_squeeze=telescopic_squeeze,
        step=step,
        calls=calls,
        tolerance=tolerance,
    )


def match_chromaticities(
    madx: Madx,
    accelerator: str = None,
    sequence: Optional[str] = None,
    dq1_target: float = None,
    dq2_target: float = None,
    varied_knobs: Sequence[str] = None,
    telescopic_squeeze: bool = True,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
):
    """
    Provided with an active `~cpymad.madx.Madx` object, will run relevant commands to match chromaticities
    to the desired target values.

    .. note::
        This is a wrapper around the `~.match_tunes_and_chromaticities` function. Refer to its documentation
        for usage details.

    .. important::
        The matching is always performed with the ``CHROM`` option on.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        accelerator (Optional[str]): name of the accelerator, used to determmine knobs if *variables* is not given.
            Automatic determination will only work for `LHC` and `HLLHC`.
        sequence (str): name of the sequence you want to perform the matching for.
        q1_target (float): horizontal tune to match to.
        q2_target (float): vertical tune to match to.
        varied_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine.
        telescopic_squeeze (bool): ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
            Squeeze configuration. Defaults to `True` as of run III.
        step (float): step size to use when varying knobs. Defaults to `1E-7`.
        calls (int): max number of varying calls to perform. Defaults to `100`.
        tolerance (float): tolerance for successfull matching. Defaults to `1E-21`.

    Examples:
        Matching a dummy lattice (not LHC or HLLHC):

        .. code-block:: python

            >>> matching.match_chromaticities(
            ...     madx,
            ...     None,              # this is not LHC or HLLHC
            ...     sequence="CAS3",
            ...     dq1_target=100,
            ...     dq2_target=100,
            ...     varied_knobs=["ksf", "ksd"],  # only chroma knobs
            ... )

        Matching the LHC lattice:

        .. code-block:: python

            >>> matching.match_chromaticities(
            ...     madx,
            ...     "lhc",                    # will find the knobs automatically
            ...     sequence="lhcb1",
            ...     dq1_target=2.0,
            ...     dq2_target=2.0,
            ... )
    """
    match_tunes_and_chromaticities(
        madx=madx,
        accelerator=accelerator,
        sequence=sequence,
        q1_target=None,
        q2_target=None,
        dq1_target=dq1_target,
        dq2_target=dq2_target,
        varied_knobs=varied_knobs,
        telescopic_squeeze=telescopic_squeeze,
        step=step,
        calls=calls,
        tolerance=tolerance,
    )
