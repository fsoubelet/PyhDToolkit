"""
.. _lhc-routines:

**Routine Utilities**

The functions below are routines mimicking manipulations that
would be done in the ``LHC``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import tfs

from loguru import logger

from pyhdtoolkit.cpymadtools.lhc._twiss import get_ir_twiss

if TYPE_CHECKING:
    from cpymad.madx import Madx


def do_kmodulation(
    madx: Madx, /, ir: int = 1, side: str = "right", steps: int = 100, stepsize: float = 3e-8, **kwargs
) -> tfs.TfsDataFrame:
    r"""
    .. versionadded:: 0.20.0

    Simulates a K-Modulation measurement by varying the powering of Q1 left or
    right of the IP, and returning the tune variations resulting from this
    modulation.

    Note
    ----
        At the end of the simulation, the powering of the quadrupole is reset
        to the value it had at the time of function call.

    Hint
    ----
        From these, one can then calculate the :math:`\beta`-functions at the
        Q1 and then at the IP, plus the possible waist shift, according to
        :cite:t:`Carlier:AccuracyFeasibilityMeasurement2017`.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    ir : int
        The IR in which to perform the modulation. Defaults to 1.
    side : str
        Side of the IP on which to use the Q1 to perform the modulation.
        Should be either ``right`` or ``left``, case insensitive. Defaults
        to ``right``.
    steps : int
        The number of steps to perform in the modulation, aka the number of
        "measurements". Defaults to 100.
    stepsize : float
        The increment in powering for Q1, in direct values of the powering
        variable used in ``MAD-X``. Defaults to 3e-8.
    **kwargs
        Any additional keyword arguments to pass to down to the ``MAD-X``
        ``TWISS`` command, such as `chrom`, `ripken` or `centre`.

    Returns
    -------
    tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` containing the tune values at each powering step.

    Example
    -------

        .. code-block:: python

            tune_results = do_kmodulation(
                madx, ir=1, side="right", steps=100, stepsize=3e-8
            )
    """
    element = f"MQXA.1R{ir:d}" if side.lower() == "right" else f"MQXA.1L{ir:d}"
    powering_variable = f"KTQX1.R{ir:d}" if side.lower() == "right" else f"KTQX1.L{ir:d}"

    logger.debug(f"Saving current magnet powering for '{element}'")
    old_powering = madx.globals[powering_variable]
    minval = old_powering - steps / 2 * stepsize
    maxval = old_powering + steps / 2 * stepsize
    k_powerings = np.linspace(minval, maxval, steps + 1)
    results = tfs.TfsDataFrame(
        index=k_powerings,
        columns=["K", "TUNEX", "ERRTUNEX", "TUNEY", "ERRTUNEY"],
        headers={
            "TITLE": "K-Modulation",
            "ELEMENT": element,
            "VARIABLE": powering_variable,
            "STEPS": steps,
            "STEP_SIZE": stepsize,
        },
        dtype=float,
    )

    logger.debug(f"Modulating quadrupole '{element}'")
    for powering in k_powerings:
        logger.trace(f"Modulation of '{element}' - Setting '{powering_variable}' to {powering}")
        madx.globals[powering_variable] = powering
        df = get_ir_twiss(madx, ir=ir, centre=True, columns=["k1l", "l"], **kwargs)
        results.loc[powering].K = df.loc[element.lower()].k1l / df.loc[element.lower()].l  # Store K
        results.loc[powering].TUNEX = madx.table.summ.q1[0]  # Store Qx
        results.loc[powering].TUNEY = madx.table.summ.q2[0]  # Store Qy

    logger.debug(f"Resetting '{element}' powering")
    madx.globals[powering_variable] = old_powering

    results.index.name = powering_variable
    results.ERRTUNEX = 0  # No measurement error from MAD-X
    results.ERRTUNEY = 0  # No measurement error from MAD-X
    return results


def correct_lhc_global_coupling(
    madx: Madx, /, beam: int = 1, telescopic_squeeze: bool = True, calls: int = 100, tolerance: float = 1.0e-21
) -> None:
    """
    .. versionadded:: 0.20.0

    A littly tricky matching routine to perform a decent global coupling
    correction using the ``LHC`` coupling knobs.

    Important
    ---------
        This routine makes use of some matching tricks and uses the ``SUMM``
        table's ``dqmin`` variable for the matching. It should be considered
        a helpful little trick, but it is not a perfect solution.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    beam : int
        The beam to perform the matching for. Should be either 1 or 2.
        Defaults to 1.
    telescopic_squeeze : bool
        If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
        Squeeze configuration. Defaults to `True`.
    calls : int
        Max number of varying calls to perform. Defaults to 100.
    tolerance : float
        Tolerance for successfull matching. Defaults to :math:`10^{-21}`.

    Example
    -------
        .. code-block:: python

            correct_lhc_global_coupling(madx, sequence="lhcb1", telescopic_squeeze=True)
    """
    suffix = "_sq" if telescopic_squeeze else ""
    sequence = f"lhcb{beam:d}"
    logger.debug(f"Attempting to correct global coupling through matching, on sequence '{sequence}'")

    real_knob, imag_knob = f"CMRS.b{beam:d}{suffix}", f"CMIS.b{beam:d}{suffix}"
    logger.debug(f"Matching using the coupling knobs '{real_knob}' and '{imag_knob}'")
    madx.command.match(sequence=sequence)
    madx.command.gweight(dqmin=1, Q1=0)
    madx.command.global_(dqmin=0, Q1=62.28)
    madx.command.vary(name=real_knob, step=1.0e-8)
    madx.command.vary(name=imag_knob, step=1.0e-8)
    madx.command.lmdif(calls=calls, tolerance=tolerance)
    madx.command.endmatch()


def correct_lhc_orbit(
    madx: Madx,
    /,
    sequence: str,
    orbit_tolerance: float = 1e-14,
    iterations: int = 3,
    mode: str = "micado",
    **kwargs,
) -> None:
    """
    .. versionadded:: 0.9.0

    Routine for orbit correction using ``MCB.*`` elements in the LHC. This uses
    the ``CORRECT`` command in ``MAD-X`` behind the scenes, refer to the `MAD-X
    manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_ for
    usage information.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    sequence : str
        Which sequence to use the routine on.
    orbit_tolerance : float
        The tolerance for the correction. Defaults to 1e-14.
    iterations : int
        The number of iterations of the correction to perform. Defaults to 3.
    mode : str
        The method to use for the correction. Defaults to ``micado`` as in
        the ``CORRECT`` command.
    **kwargs
        Any keyword argument that can be given to the ``MAD-X`` ``CORRECT``
        command, such as ``mode``, ``ncorr``, etc.

    Example
    -------
        .. code-block:: python

            correct_lhc_orbit(madx, sequence="lhcb1", plane="y")
    """
    logger.debug("Starting orbit correction")
    for default_kicker in ("kicker", "hkicker", "vkicker", "virtualcorrector"):
        logger.trace(f"Disabling default corrector class '{default_kicker}'")
        madx.command.usekick(sequence=sequence, status="off", class_=default_kicker)

    logger.debug("Selecting '^MCB.*' correctors")
    madx.command.usekick(sequence=sequence, status="on", pattern="^MCB.*")
    madx.command.usemonitor(sequence=sequence, status="on", class_="monitor")

    for _ in range(iterations):
        logger.trace("Doing orbit correction for Y then X plane")
        madx.command.twiss()
        madx.command.correct(sequence=sequence, plane="y", flag="ring", error=orbit_tolerance, mode=mode, **kwargs)
        madx.command.correct(sequence=sequence, plane="x", flag="ring", error=orbit_tolerance, mode=mode, **kwargs)
