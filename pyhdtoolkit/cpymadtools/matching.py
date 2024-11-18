"""
.. _cpymadtools-matching:

Matching Routines
-----------------

Module with functions to perform ``MAD-X`` matchings
through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from pyhdtoolkit.cpymadtools.lhc import get_lhc_tune_and_chroma_knobs

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cpymad.madx import Madx

# ----- Workhorse ----- #


def match_tunes_and_chromaticities(
    madx: Madx,
    /,
    accelerator: str | None = None,
    sequence: str | None = None,
    q1_target: float | None = None,
    q2_target: float | None = None,
    dq1_target: float | None = None,
    dq2_target: float | None = None,
    varied_knobs: Sequence[str] | None = None,
    telescopic_squeeze: bool = True,
    run3: bool = False,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
) -> None:
    """
    .. versionadded:: 0.8.0

    Provided with an active `~cpymad.madx.Madx` object, will run relevant commands to
    match tunes and/or chromaticities. As target values are given, the function expects
    knob names to be provided, which are then used and varied by ``MAD-X`` to match the
    targets. This is a convenient wrapper around the ``MATCH`` command in the ``MAD-X``
    process. For usage details, see the `MAD-X manual
    <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_.

    One can find examples of this function in the :ref:`lattice plotting
    <demo-accelerator-lattice>`, the :ref:`rigid waist shift <demo-rigid-waist-shift>`
    and the :ref:`phase space <demo-phase-space>` example galleries.

    Important
    ---------
        If only target tune values are provided, then tune matching is performed
        with the provided knobs. If only target chromaticity values are provided,
        then chromaticity matching is performed with the provided knobs. Otherwise
        if targets are provided for both, then both are matched in a single call
        with the provided knobs.

    Note
    ----
        If one wishes to perform different matching calls for each, then it is
        recommended to call this function as many times as necessary, with the
        appropriate targets, or simply the wrappers provided in this module.

        For instance, in some cases and machines some prefer to do a tune matching
        followed by a chromaticity matching, then followed by a combined matching.
        In this case one could call this function three times, or use each wrapper
        once (first tunes, then chromaticities, then this function). Refer to the
        :func:`match_tunes` and :func:`match_chromaticities` functions.

    Hint
    ----
        When acting on either the ``LHC`` or ``HLLHC`` machines, the accelerator name
        can be provided and the vary knobs will be automatically set accordingly to the
        provided targets, based on the machine's default knobs. Note that in this case
        only the relevant knobs are set, so if tune targets only are provided, then tune
        knobs only will be used, and vice versa. If explicit knobs are provided, these
        will always take precedence. On any other machine the knobs should be provided
        explicitly, always.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object.
    accelerator : str, optional
        Name of the accelerator, used to determmine knobs if *variables* is not given.
        Automatic determination will only work for the ``LHC`` and ``HLLHC`` (accepted
        case insensitively). Defaults to `None`, in which case the knobs must be provided
        explicitly through ``varied_knobs``.
    sequence : str, optional
        Name of the sequence to perform the matching for. Defaults to `None`, in which
        case the currently active sequence will be used for the matching.
    q1_target : float, optional
        Horizontal tune to match to. Defaults to `None`, in which case it will not be a
        target and will be excluded from the matching.
    q2_target : float, optional
        Vertical tune to match to. Defaults to `None`, in which case it will not be a
        target and will be excluded from the matching.
    dq1_target : float, optional
        Horizontal chromaticity to match to. Defaults to `None`, in which case it will
        not be a target and will be excluded from the matching.
    dq2_target : float, optional
        Vertical chromaticity to match to. Defaults to `None`, in which case it will not
        be a target and will be excluded from the matching.
    varied_knobs : Sequence[str], optional
        The variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine. An example
        input could be ``["kqf", "ksd", "kqf", "kqd"]`` as they are common names used
        for quadrupole and sextupole strengths (focusing / defocusing) in most examples.
        This parameter is optional if the accelerator is provided as ``LHC`` or ``HLLHC``,
        but must be provided otherwise. Defaults to `None`.
    telescopic_squeeze : bool
        ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
        Squeeze configuration. Defaults to `True` since `v0.9.0`.
    run3 : bool
        ``LHC`` specific. If set to `True`, uses the ``LHC`` Run 3 `*_op` knobs. Defaults
        to `False`.
    step : float
        Step size to use when varying knobs. Defaults to :math:`10^{-7}`.
    calls : int
        Max number of varying calls to perform. Defaults to 100.
    tolerance : float
        Tolerance for successfull matching. Defaults to :math:`10^{-21}`.

    Examples
    --------
        Matching a dummy lattice (not ``LHC`` or ``HLLHC``):

        .. code-block:: python

            matching.match_tunes_and_chromaticities(
                madx,
                None,  # this is not LHC or HLLHC
                sequence="CAS3",
                q1_target=6.335,
                q2_target=6.29,
                dq1_target=100,
                dq2_target=100,
                varied_knobs=["kqf", "kqd", "ksf", "ksd"],
            )

        Note that since the `accelerator` and `sequence` parameters default to `None`,
        they can be omitted. In this case the sequence currently in use will be used for
        the matching, and `varied_knobs` must be provided:

        .. code-block:: python

            matching.match_tunes_and_chromaticities(
                madx,
                q1_target=6.335,
                q2_target=6.29,
                dq1_target=100,
                dq2_target=100,
                varied_knobs=["kqf", "kqd", "ksf", "ksd"],
            )

        Matching the ``lhcb1`` sequence of the ``LHC`` lattice and letting
        the function determine the knobs automatically:

        .. code-block:: python

            matching.match_tunes_and_chromaticities(
                madx,
                "lhc",  # will find the knobs automatically
                sequence="lhcb1",
                q1_target=62.31,
                q2_target=60.32,
                dq1_target=2.0,
                dq2_target=2.0,
                run3=True,  # influences the knobs definition
            )
    """
    if accelerator and not varied_knobs:
        # Assume valid accelerator, which checked in function below
        logger.trace(f"Getting knobs from default {accelerator.upper()} values")
        lhc_knobs = get_lhc_tune_and_chroma_knobs(
            accelerator=accelerator, beam=int(sequence[-1]), telescopic_squeeze=telescopic_squeeze, run3=run3
        )
        tune_knobs, chroma_knobs = lhc_knobs[:2], lhc_knobs[2:]  # first two, last two

    def match(*args, **kwargs):
        """Create matching commands for kwarg targets, varying the given args."""
        logger.debug(f"Executing matching commands, using sequence '{sequence}'")
        madx.command.match()
        logger.trace(f"Targets are given as {kwargs}")
        madx.command.global_(sequence=sequence, **kwargs)
        for variable_name in args:
            logger.trace(f"Creating vary command for knob '{variable_name}'")
            madx.command.vary(name=variable_name, step=step)
        madx.command.lmdif(calls=calls, tolerance=tolerance)
        madx.command.endmatch()
        logger.trace("Performing routine TWISS")
        madx.command.twiss()  # prevents errors if the user forgets to TWISS before querying tables

    # Case of a combined matching: both tune and chroma targets have been provided
    if q1_target is not None and q2_target is not None and dq1_target is not None and dq2_target is not None:
        logger.debug(
            f"Doing combined matching to Qx={q1_target}, Qy={q2_target}, "
            f"dqx={dq1_target}, dqy={dq2_target} for sequence '{sequence}'"
        )
        varied_knobs = varied_knobs or lhc_knobs  # if accelerator was given we've extracted this already
        logger.trace(f"Vary knobs sent are {varied_knobs}")
        match(*varied_knobs, q1=q1_target, q2=q2_target, dq1=dq1_target, dq2=dq2_target)

    # Case of a tune matching: ony tune targets have been provided (see also 'match_tunes' wrapper)
    elif q1_target is not None and q2_target is not None:
        logger.debug(f"Matching tunes to Qx={q1_target}, Qy={q2_target} for sequence '{sequence}'")
        tune_knobs = varied_knobs or tune_knobs  # if accelerator was given we've extracted this already
        logger.trace(f"Vary knobs sent are {tune_knobs}")
        match(*tune_knobs, q1=q1_target, q2=q2_target)  # sent varied_knobs should be tune knobs

    # Case of a chrom matching: ony chroma targets have been provided (see also 'match_chromaticities' wrapper)
    elif dq1_target is not None and dq2_target is not None:
        logger.debug(f"Matching chromaticities to dq1={dq1_target}, dq2={dq2_target} for sequence {sequence}")
        chroma_knobs = varied_knobs or chroma_knobs  # if accelerator was given we've extracted this already
        logger.trace(f"Vary knobs sent are {chroma_knobs}")
        match(*chroma_knobs, dq1=dq1_target, dq2=dq2_target)  # sent varied_knobs should be chromaticity knobs


# ----- Convenient Wrappers ----- #


def match_tunes(
    madx: Madx,
    /,
    accelerator: str | None = None,
    sequence: str | None = None,
    q1_target: float | None = None,
    q2_target: float | None = None,
    varied_knobs: Sequence[str] | None = None,
    telescopic_squeeze: bool = True,
    run3: bool = False,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
):
    """
    .. versionadded:: 0.17.0

    Provided with an active `~cpymad.madx.Madx` object, will run relevant commands
    to match tunes to the desired target values.

    Note
    ----
        This is a wrapper around the `~.match_tunes_and_chromaticities` function.
        Refer to its documentation for usage details.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object.
    accelerator : str, optional
        Name of the accelerator, used to determmine knobs if *variables* is not given.
        Automatic determination will only work for the ``LHC`` and ``HLLHC`` (accepted
        case insensitively). Defaults to `None`, in which case the knobs must be provided
        explicitly through ``varied_knobs``.
    sequence : str, optional
        Name of the sequence to perform the matching for. Defaults to `None`, in which
        case the currently active sequence will be used for the matching.
    q1_target : float, optional
        Horizontal tune to match to. Defaults to `None`, in which case it will not be a
        target and will be excluded from the matching.
    q2_target : float, optional
        Vertical tune to match to. Defaults to `None`, in which case it will not be a
        target and will be excluded from the matching.
    varied_knobs : Sequence[str], optional
        The variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine. An example
        input could be ``["kqf", "ksd", "kqf", "kqd"]`` as they are common names used
        for quadrupole and sextupole strengths (focusing / defocusing) in most examples.
        This parameter is optional if the accelerator is provided as ``LHC`` or ``HLLHC``,
        but must be provided otherwise. Defaults to `None`.
    telescopic_squeeze : bool
        ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
        Squeeze configuration. Defaults to `True` since `v0.9.0`.
    run3 : bool
        ``LHC`` specific. If set to `True`, uses the ``LHC`` Run 3 `*_op` knobs. Defaults
        to `False`.
    step : float
        Step size to use when varying knobs. Defaults to :math:`10^{-7}`.
    calls : int
        Max number of varying calls to perform. Defaults to 100.
    tolerance : float
        Tolerance for successfull matching. Defaults to :math:`10^{-21}`.

    Examples
    --------
        Matching a dummy lattice (not ``LHC`` or ``HLLHC``):

        .. code-block:: python

            matching.match_tunes(
                madx,
                None,  # this is not LHC or HLLHC
                sequence="CAS3",
                q1_target=6.335,
                q2_target=6.29,
                varied_knobs=["kqf", "kqd"],  # only tune knobs
            )

        Note that since the `accelerator` and `sequence` parameters default to `None`,
        they can be omitted. In this case the sequence currently in use will be used for
        the matching, and `varied_knobs` must be provided:

        .. code-block:: python

            matching.match_tunes_and_chromaticities(
                madx,
                q1_target=6.335,
                q2_target=6.29,
                varied_knobs=["kqf", "kqd"],  # only tune knobs
            )

        Matching the ``lhcb1`` sequence of the ``LHC`` lattice and letting
        the function determine the knobs automatically:

        .. code-block:: python

            matching.match_tunes(
                madx,
                "lhc",  # will find the knobs automatically
                sequence="lhcb1",
                q1_target=62.31,
                q2_target=60.32,
            )
    """
    match_tunes_and_chromaticities(
        madx,
        accelerator=accelerator,
        sequence=sequence,
        q1_target=q1_target,
        q2_target=q2_target,
        dq1_target=None,
        dq2_target=None,
        varied_knobs=varied_knobs,
        telescopic_squeeze=telescopic_squeeze,
        run3=run3,
        step=step,
        calls=calls,
        tolerance=tolerance,
    )


def match_chromaticities(
    madx: Madx,
    /,
    accelerator: str | None = None,
    sequence: str | None = None,
    dq1_target: float | None = None,
    dq2_target: float | None = None,
    varied_knobs: Sequence[str] | None = None,
    telescopic_squeeze: bool = True,
    run3: bool = False,
    step: float = 1e-7,
    calls: int = 100,
    tolerance: float = 1e-21,
):
    """
    .. versionadded:: 0.17.0

    Provided with an active `~cpymad.madx.Madx` object, will run relevant commands
    to match chromaticities to the desired target values.

    Note
    ----
        This is a wrapper around the `~.match_tunes_and_chromaticities` function.
        Refer to its documentation for usage details.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object.
    accelerator : str, optional
        Name of the accelerator, used to determmine knobs if *variables* is not given.
        Automatic determination will only work for the ``LHC`` and ``HLLHC`` (accepted
        case insensitively). Defaults to `None`, in which case the knobs must be provided
        explicitly through ``varied_knobs``.
    sequence : str, optional
        Name of the sequence to perform the matching for. Defaults to `None`, in which
        case the currently active sequence will be used for the matching.
    dq1_target : float, optional
        Horizontal chromaticity to match to. Defaults to `None`, in which case it will
        not be a target and will be excluded from the matching.
    dq2_target : float, optional
        Vertical chromaticity to match to. Defaults to `None`, in which case it will not
        be a target and will be excluded from the matching.
    varied_knobs : Sequence[str], optional
        The variables names to ``VARY`` in the ``MAD-X`` ``MATCH`` routine. An example
        input could be ``["kqf", "ksd", "kqf", "kqd"]`` as they are common names used
        for quadrupole and sextupole strengths (focusing / defocusing) in most examples.
        This parameter is optional if the accelerator is provided as ``LHC`` or ``HLLHC``,
        but must be provided otherwise. Defaults to `None`.
    telescopic_squeeze : bool
        ``LHC`` specific. If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
        Squeeze configuration. Defaults to `True` since `v0.9.0`.
    run3 : bool
        ``LHC`` specific. If set to `True`, uses the ``LHC`` Run 3 `*_op` knobs. Defaults
        to `False`.
    step : float
        Step size to use when varying knobs. Defaults to :math:`10^{-7}`.
    calls : int
        Max number of varying calls to perform. Defaults to 100.
    tolerance : float
        Tolerance for successfull matching. Defaults to :math:`10^{-21}`.

    Examples
    --------
        Matching a dummy lattice (not ``LHC`` or ``HLLHC``):

        .. code-block:: python

            matching.match_chromaticities(
                madx,
                None,  # this is not LHC or HLLHC
                sequence="CAS3",
                dq1_target=100,
                dq2_target=100,
                varied_knobs=["ksf", "ksd"],  # only chroma knobs
            )

        Note that since the `accelerator` and `sequence` parameters default to `None`,
        they can be omitted. In this case the sequence currently in use will be used for
        the matching, and `varied_knobs` must be provided:

        .. code-block:: python

            matching.match_tunes_and_chromaticities(
                madx,
                dq1_target=100,
                dq2_target=100,
                varied_knobs=["ksf", "ksd"],  # only chroma knobs
            )

        Matching the ``lhcb1`` sequence of the ``LHC`` lattice and letting
        the function determine the knobs automatically:

        .. code-block:: python

            matching.match_chromaticities(
                madx,
                "lhc",  # will find the knobs automatically
                sequence="lhcb1",
                dq1_target=2.0,
                dq2_target=2.0,
            )
    """
    match_tunes_and_chromaticities(
        madx,
        accelerator=accelerator,
        sequence=sequence,
        q1_target=None,
        q2_target=None,
        dq1_target=dq1_target,
        dq2_target=dq2_target,
        varied_knobs=varied_knobs,
        telescopic_squeeze=telescopic_squeeze,
        run3=run3,
        step=step,
        calls=calls,
        tolerance=tolerance,
    )
