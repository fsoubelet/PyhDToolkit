"""
.. _cpymadtools-lhc:

LHC-Specific Utilities
----------------------

Module with functions to perform ``MAD-X`` actions through a `~cpymad.madx.Madx` object,
that are specific to LHC and HLLHC machines.
"""
from typing import Dict, List, Sequence, Tuple

import numpy as np

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools import twiss
from pyhdtoolkit.cpymadtools.constants import (
    LHC_ANGLE_FLAGS,
    LHC_CROSSING_ANGLE_FLAGS,
    LHC_EXPERIMENT_STATE_FLAGS,
    LHC_IP2_SPECIAL_FLAG,
    LHC_IP_OFFSET_FLAGS,
    LHC_PARALLEL_SEPARATION_FLAGS,
)
from pyhdtoolkit.utils import deprecated

__all__ = [
    "apply_lhc_colinearity_knob",
    "apply_lhc_coupling_knob",
    "apply_lhc_rigidity_waist_shift_knob",
    "deactivate_lhc_arc_sextupoles",
    "get_lhc_bpms_list",
    "get_lhc_tune_and_chroma_knobs",
    "install_ac_dipole_as_kicker",
    "install_ac_dipole_as_matrix",
    "make_lhc_beams",
    "make_lhc_thin",
    "make_sixtrack_output",
    "power_landau_octupoles",
    "reset_lhc_bump_flags",
    "re_cycle_sequence",
    "vary_independent_ir_quadrupoles",
]


# ----- Setup Utlites ----- #


def make_lhc_beams(madx: Madx, energy: float = 7000, emittance: float = 3.75e-6, **kwargs) -> None:
    """
    Defines beams with default configuratons for ``LHCB1`` and ``LHCB2`` sequences.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        energy (float): beam energy, in [GeV]. Defaults to 6500.
        emittance (float): emittance in [m]. Will be used to calculate geometric
            emittance which is then fed to the ``BEAM`` command.
        **kwargs: Any keyword argument that can be given to the ``MAD-X`` ``BEAM`` command.

    Example:
        .. code-block:: python

            >>> make_lhc_beams(madx, energy=6800, emittance=2.5e-6)
    """
    logger.info("Making default beams for 'lhcb1' and 'lhbc2' sequences")
    madx.globals["NRJ"] = energy
    madx.globals["brho"] = energy * 1e9 / madx.globals.clight
    geometric_emit = madx.globals["geometric_emit"] = emittance / (energy / 0.938)

    for beam in (1, 2):
        logger.trace(f"Defining beam for sequence 'lhcb{beam:d}'")
        madx.command.beam(
            sequence=f"lhcb{beam:d}",
            particle="proton",
            bv=1 if beam == 1 else -1,
            energy=energy,
            npart=1.15e11,
            ex=geometric_emit,
            ey=geometric_emit,
            sige=4.5e-4,
            **kwargs,
        )


def power_landau_octupoles(madx: Madx, beam: int, mo_current: float, defective_arc: bool = False) -> None:
    """
    Powers the Landau octupoles in the (HL)LHC.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam (int): beam to use.
        mo_current (float): `MO` powering, in [A].
        defective_arc: If set to `True`, the ``KOD`` in Arc 56 are powered for less ``Imax``.

    Example:
        .. code-block:: python

            >>> power_landau_octupoles(madx, beam=1, mo_current=350, defect_arc=True)
    """
    try:
        brho = madx.globals.nrj * 1e9 / madx.globals.clight  # clight is MAD-X constant
    except AttributeError as madx_error:
        logger.exception("The global MAD-X variable 'NRJ' should have been set in the optics files but is not defined.")
        raise EnvironmentError("No 'NRJ' variable found in scripts") from madx_error

    logger.info(f"Powering Landau Octupoles, beam {beam} @ {madx.globals.nrj} GeV with {mo_current} A.")
    strength = mo_current / madx.globals.Imax_MO * madx.globals.Kmax_MO / brho
    beam = 2 if beam == 4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            octupole = f"KO{fd}.{arc}"
            logger.trace(f"Powering element '{octupole}' at {strength} Amps")
            madx.globals[octupole] = strength

    if defective_arc and (beam == 1):
        madx.globals["KOD.A56B1"] = strength * 4.65 / 6  # defective MO group


def deactivate_lhc_arc_sextupoles(madx: Madx, beam: int) -> None:
    """
    Deactivates all arc sextupoles in the (HL)LHC.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam (int): beam to use.

    Example:
        .. code-block:: python

            >>> deactivate_lhc_arc_sextupoles(madx, beam=1)
    """
    # KSF1 and KSD2 - Strong sextupoles of sectors 81/12/45/56
    # KSF2 and KSD1 - Weak sextupoles of sectors 81/12/45/56
    # Rest: Weak sextupoles in sectors 78/23/34/67
    logger.info(f"Deactivating all arc sextupoles for beam {beam}.")
    beam = 2 if beam == 4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            for i in (1, 2):
                sextupole = f"KS{fd}{i:d}.{arc}"
                logger.trace(f"De-powering element '{sextupole}'")
                madx.globals[sextupole] = 0.0


def apply_lhc_colinearity_knob(madx: Madx, colinearity_knob_value: float = 0, ir: int = None) -> None:
    """
    Applies the LHC colinearity knob.

    .. note::
        If you don't know what this is, you really should not be using this function.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        colinearity_knob_value (float): Units of the colinearity knob to apply. Defaults to 0 so users
            don't mess up local IR coupling by mistake. This should be a positive integer, normally between 1
            and 10.
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.

    Example:
        .. code-block:: python

            >>> apply_lhc_colinearity_knob(madx, colinearity_knob_value=5, ir=1)
    """
    logger.info(f"Applying Colinearity knob with a unit setting of {colinearity_knob_value}")
    logger.warning("You should re-match tunes & chromaticities after this")
    knob_variables = (f"KQSX3.R{ir:d}", f"KQSX3.L{ir:d}")  # MQSX IP coupling correctors
    right_knob, left_knob = knob_variables

    madx.globals[right_knob] = colinearity_knob_value * 1e-4
    logger.trace(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    madx.globals[left_knob] = -1 * colinearity_knob_value * 1e-4
    logger.trace(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_rigidity_waist_shift_knob(
    madx: Madx, rigidty_waist_shift_value: float = 0, ir: int = None, side: str = "left"
) -> None:
    """
    Applies the LHC rigidity waist shift knob, moving the waist left or right of IP.

    .. note::
        If you don't know what this is, you really should not be using this function. The waist shift
        is achieved by moving all four betatron waists simltaneously: unbalancing the triplet powering
        knobs of the left and right-hand sides of the IP,

    .. warning::
        Applying the shift will modify your tunes and is likely to flip them, making a subsequent matching
        impossible if your lattice has coupling. To avoid this, one should match to tunes split further apart
        before applying the waist shift knob, and then match to the desired working point. For instance for
        the LHC, matching to (62.27, 60.36) before applying and afterwards rematching to (62.31, 60.32) usually
        works well.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        rigidty_waist_shift_value (float): Units of the rigidity waist shift knob (positive values only).
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.
        side (str): Which side of the IP to move the waist to, determines a sign in the calculation.
            Defaults to `left`, which means :math:`s_{\\mathrm{waist}} \\lt s_{\\mathrm{ip}}` (and
            setting it to `right` would move the waist such that
            :math:`s_{\\mathrm{waist}} \\gt s_{\\mathrm{ip}}`).

    Example:
        .. code-block:: python

            >>> matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.27, 60.36)
            >>> apply_lhc_rigidity_waist_shift_knob(madx, rigidty_waist_shift_value=1.5, ir=5)
            >>> matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32)
    """
    logger.info(f"Applying Rigidity Waist Shift knob with a unit setting of {rigidty_waist_shift_value}")
    logger.warning("You should re-match tunes & chromaticities after this")
    right_knob, left_knob = f"kqx.r{ir:d}", f"kqx.l{ir:d}"  # IP triplet default knob (no trims)

    current_right_knob = madx.globals[right_knob]
    current_left_knob = madx.globals[left_knob]

    if side.lower() == "left":
        madx.globals[right_knob] = (1 - rigidty_waist_shift_value * 0.005) * current_right_knob
        madx.globals[left_knob] = (1 + rigidty_waist_shift_value * 0.005) * current_left_knob
    elif side.lower() == "right":
        madx.globals[right_knob] = (1 + rigidty_waist_shift_value * 0.005) * current_right_knob
        madx.globals[left_knob] = (1 - rigidty_waist_shift_value * 0.005) * current_left_knob
    else:
        logger.error(f"Given side '{side}' invalid, only 'left' and 'right' are accepted values.")
        raise ValueError("Invalid value for parameter 'side'.")

    logger.trace(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    logger.trace(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_coupling_knob(
    madx: Madx, coupling_knob: float = 0, beam: int = 1, telescopic_squeeze: bool = True
) -> None:
    """
    Applies the LHC coupling knob to reach the desired :math:`C^{-}` value.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        coupling_knob (float): Desired value for the Cminus, typically a few units of ``1E-3``.
            Defaults to 0 so users don't mess up coupling by mistake.
        beam (int): beam to apply the knob to. Defaults to beam 1.
        telescopic_squeeze (bool): if set to `True`, uses the knobs for Telescopic Squeeze configuration.
            Defaults to `True` as of run III.

    Example:
        .. code-block:: python

            >>> apply_lhc_coupling_knob(madx, coupling_knob=5e-4, beam=1)
    """
    logger.info("Applying coupling knob")
    logger.warning("You should re-match tunes & chromaticities after this")
    suffix = "_sq" if telescopic_squeeze else ""
    knob_name = f"CMRS.b{beam:d}{suffix}"

    logger.trace(f"Knob '{knob_name}' is {madx.globals[knob_name]} before implementation")
    madx.globals[knob_name] = coupling_knob
    logger.trace(f"Set '{knob_name}' to {madx.globals[knob_name]}")


def install_ac_dipole_as_kicker(
    madx: Madx,
    deltaqx: float,
    deltaqy: float,
    sigma_x: float,
    sigma_y: float,
    beam: int = 1,
    start_turn: int = 100,
    ramp_turns: int = 2000,
    top_turns: int = 6600,
) -> None:
    """
    Installs an AC dipole as a kicker element in (HL)LHC beam 1 or 2, for tracking. This function
    assumes that you have already defined lhcb1/lhcb2 sequence, made a beam for it (``BEAM``
    command or `~lhc.make_lhc_beams` function), matched to your desired working point and made
    a ``TWISS`` call.

    .. important::
        In a real machine, the AC Dipole does impact the orbit as well as the betatron
        functions when turned on (:cite:t:`Miyamoto:ACD:2008`, part III). In ``MAD-X``
        however, it cannot be modeled to do both at the same time. This routine introduces
        an AC Dipole as a kicker element so that its effect can be seen on particle trajectory
        in tracking. It **does not** affect ``TWISS`` functions.

    One can find a full example use of the function for tracking in the
    :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>` example gallery.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        deltaqx (float): the deltaQx (horizontal tune excitation) used by the AC dipole.
        deltaqy (float): the deltaQy (vertical tune excitation) used by the AC dipole.
        sigma_x (float): the horizontal amplitude to drive the beam to, in bunch sigma.
        sigma_y (float): the vertical amplitude to drive the beam to, in bunch sigma.
        beam (int): the LHC beam to install the AC Dipole into, either 1 or 2. Defaults to 1.
        start_turn (int): the turn at which to start ramping up the AC dipole. Defaults to 100.
        ramp_turns (int): the number of turns to use for the ramp-up and the ramp-down of the AC dipole.
            This number is important in order to preserve the adiabaticity of the cycle. Defaults to 2000
            as in the LHC.
        top_turns (int): the number of turns to drive the beam for. Defaults to 6600 as in the LHC.

    Example:
        .. code-block:: python

            >>> lhc.install_ac_dipole_as_kicker(
            ...     madx,
            ...     deltaqx=-0.01,  # driven horizontal tune to Qxd = 62.31 - 0.01 = 62.30
            ...     deltaqy=0.012,  # driven vertical tune to Qyd = 60.32 + 0.012 = 60.332
            ...     sigma_x=2,  # bunch amplitude kick in the horizontal plane
            ...     sigma_y=2,  # bunch amplitude kick in the vertical plane
            ...     beam=1,  # beam for which to install and kick
            ...     start_turn=100,  # when to turn on the AC Dipole
            ...     ramp_turns=2000,  # how many turns to ramp up/down the AC Dipole
            ...     top_turns=6600,  # how many turns to keep the AC Dipole at full kick
            ... )
    """
    logger.warning("This AC Dipole is implemented as a kicker and will not affect TWISS functions!")
    logger.info("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam")

    if top_turns > 6600:
        logger.warning(
            f"Configuring the AC Dipole for {top_turns:d} of driving is fine for MAD-X but is "
            "higher than what the device can do in the (HL)LHC! Beware."
        )
    ramp1, ramp2 = start_turn, start_turn + ramp_turns
    ramp3 = ramp2 + top_turns
    ramp4 = ramp3 + ramp_turns

    logger.debug("Retrieving tunes from internal tables")
    q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
    logger.trace(f"Retrieved values are q1 = {q1:.5f}, q2 = {q2:.5f}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    logger.trace("Querying BETX and BETY at AC Dipole location")
    # All below is done as model_creator macros with `.input()` calls
    madx.input(f"pbeam = beam%lhcb{beam:d}->pc;")
    madx.input(f"betxac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, betx);")
    madx.input(f"betyac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, bety);")

    logger.trace("Calculating AC Dipole voltage values")
    madx.input(f"voltx = 0.042 * pbeam * ABS({deltaqx}) / SQRT(180.0 * betxac) * {sigma_x}")
    madx.input(f"volty = 0.042 * pbeam * ABS({deltaqy}) / SQRT(177.0 * betyac) * {sigma_y}")

    logger.trace("Defining kicker elements for transverse planes")
    madx.input(
        f"MKACH.6L4.B{beam:d}: hacdipole, l=0, freq:={q1_dipole}, lag=0, volt=voltx, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )
    madx.input(
        f"MKACV.6L4.B{beam:d}: vacdipole, l=0, freq:={q2_dipole}, lag=0, volt=volty, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )

    logger.info(f"Installing AC Dipole kicker with driven tunes of Qx_D = {q1_dipole:.5f}  |  Qy_D = {q2_dipole:.5f}")
    madx.command.seqedit(sequence=f"lhcb{beam:d}")
    madx.command.flatten()
    # The kicker version is meant for a thin lattice and is installed a right at MKQA.6L4.B[12] (at=0)
    madx.command.install(element=f"MKACH.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element=f"MKACV.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-used for changes to take effect. Beware that this will reset it, "
        "remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def install_ac_dipole_as_matrix(madx: Madx, deltaqx: float, deltaqy: float, beam: int = 1) -> None:
    """
    Installs an AC dipole as a matrix element in (HL)LHC beam 1 or 2, to see its effect on TWISS functions
    This function assumes that you have already defined lhcb1/lhcb2 sequence, made a beam for it (``BEAM``
    command or `~lhc.make_lhc_beams` function), matched to your desired working point and made a ``TWISS``
    call.

    This function's use is very similar to that of `~.lhc.install_ac_dipole_as_kicker`.

    .. important::
        In a real machine, the AC Dipole does impact the orbit as well as the betatron
        functions when turned on (:cite:t:`Miyamoto:ACD:2008`, part III). In ``MAD-X``
        however, it cannot be modeled to do both at the same time. This routine introduces
        an AC Dipole as a matrix element so that its effect can be seen on ``TWISS`` functions.
        It **does not** affect tracking.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        deltaqx (float): the deltaQx (horizontal tune excitation) used by the AC dipole.
        deltaqy (float): the deltaQy (vertical tune excitation) used by the AC dipole.
        beam (int): the LHC beam to install the AC Dipole into, either 1 or 2. Defaults to 1.

    Example:
        .. code-block:: python

            >>> install_ac_dipole_as_matrix(madx, deltaqx=-0.01, deltaqy=0.012, beam=1)
    """
    logger.warning("This AC Dipole is implemented as a matrix and will not affect particle tracking!")
    logger.info("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam.")

    logger.debug("Retrieving tunes from internal tables")
    q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
    logger.trace(f"Retrieved values are q1 = {q1:.5f}, q2 = {q2:.5f}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    logger.trace("Querying BETX and BETY at AC Dipole location")
    # All below is done as model_creator macros with `.input()` calls
    madx.input(f"betxac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, betx);")
    madx.input(f"betyac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, bety);")

    logger.trace("Calculating AC Dipole matrix terms")
    madx.input(f"hacmap21 = 2 * (cos(2*pi*{q1_dipole}) - cos(2*pi*{q1})) / (betxac * sin(2*pi*{q1}));")
    madx.input(f"vacmap43 = 2 * (cos(2*pi*{q2_dipole}) - cos(2*pi*{q2})) / (betyac * sin(2*pi*{q2}));")

    logger.trace("Defining matrix elements for transverse planes")
    madx.input(f"hacmap: matrix, l=0, rm21=hacmap21;")
    madx.input(f"vacmap: matrix, l=0, rm43=vacmap43;")

    logger.info(f"Installing AC Dipole matrix with driven tunes of Qx_D = {q1_dipole:.5f}  |  Qy_D = {q2_dipole:.5f}")
    madx.command.seqedit(sequence=f"lhcb{beam:d}")
    madx.command.flatten()
    # The matrix version is meant for a thick lattice and is installed a little after MKQA.6L4.B[12]
    madx.command.install(element="hacmap", at="1.583 / 2", from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element="vacmap", at="1.583 / 2", from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-used for changes to take effect. Beware that this will reset it, "
        "remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def vary_independent_ir_quadrupoles(
    madx: Madx, quad_numbers: Sequence[int], ip: int, sides: Sequence[str] = ("r", "l"), beam: int = 1
) -> None:
    """
    Sends the ``VARY`` commands for the desired quadrupoles in the IR surrounding the provided *ip*.
    The independent quadrupoles for which this is implemented are Q4 to Q13 included. This is useful
    to setup some specific matching involving these elements.

    ..important::
        It is necessary to have defined a ``brho`` variable when creating your beams.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        quad_numbers (Sequence[int]): quadrupoles to be varied, by number (aka position from IP).
        ip (int): the IP around which to apply the instructions.
        sides (Sequence[str]): the sides of IP to act on. Should be `R` for right and `L` for left,
            accepts these letters case-insensitively. Defaults to both sides of the IP.
        beam (int): the beam for which to apply the instructions. Defaults to 1.

    Example:
        .. code-block:: python

            >>> vary_independent_ir_quadrupoles(
            ...     madx, quad_numbers=[10, 11, 12, 13], ip=1, sides=("r", "l")
            ... )
    """
    if (
        ip not in (1, 2, 5, 8)
        or any(side.upper() not in ("R", "L") for side in sides)
        or any(quad not in (4, 5, 6, 7, 8, 9, 10, 11, 12, 13) for quad in quad_numbers)
    ):
        logger.error("Either the IP number of the side provided are invalid, not applying any error.")
        raise ValueError("Invalid 'quad_numbers', 'ip', 'sides' argument")

    logger.debug(f"Preparing a knob involving quadrupoles {quad_numbers}")
    # Each quad has a specific power circuit used for their k1 boundaries
    power_circuits: Dict[int, str] = {
        4: "mqy",
        5: "mqml",
        6: "mqml",
        7: "mqm",
        8: "mqml",
        9: "mqm",
        10: "mqml",
        11: "mqtli",
        12: "mqt",
        13: "mqt",
    }
    for quad in quad_numbers:
        circuit = power_circuits[quad]
        for side in sides:
            logger.trace(f"Sending vary command for Q{quad}{side.upper()}{ip}")
            madx.command.vary(
                name=f"kq{'t' if quad >= 11 else ''}{'l' if quad == 11 else ''}{quad}.{side}{ip}b{beam}",
                step=1e-7,
                lower=f"-{circuit}.{'b' if quad == 7 else ''}{quad}{side}{ip}.b{beam}->kmax/brho",
                upper=f"+{circuit}.{'b' if quad == 7 else ''}{quad}{side}{ip}.b{beam}->kmax/brho",
            )


def reset_lhc_bump_flags(madx: Madx) -> None:
    """
    Resets all LHC IP bump flags to 0.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Example:
        .. code-block:: python

            >>> reset_lhc_bump_flags(madx)
    """
    logger.info("Resetting all LHC IP bump flags")
    ALL_BUMPS = (
        LHC_ANGLE_FLAGS
        + LHC_CROSSING_ANGLE_FLAGS
        + LHC_EXPERIMENT_STATE_FLAGS
        + LHC_IP2_SPECIAL_FLAG
        + LHC_IP_OFFSET_FLAGS
        + LHC_PARALLEL_SEPARATION_FLAGS
    )
    with madx.batch():
        madx.globals.update({bump: 0 for bump in ALL_BUMPS})


# ----- Output Utilities ----- #


def make_sixtrack_output(madx: Madx, energy: int) -> None:
    """
    Prepare output for a ``SixTrack`` run. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        energy (float): beam energy, in [GeV].

    Example:
        .. code-block:: python

            >>> make_sixtrack_output(madx, energy=6800)
    """
    logger.info("Preparing outputs for SixTrack")

    logger.debug("Powering RF cavities")
    madx.globals["VRF400"] = 8 if energy < 5000 else 16  # is 6 at injection for protons iirc?
    madx.globals["LAGRF400.B1"] = 0.5  # cavity phase difference in units of 2pi
    madx.globals["LAGRF400.B2"] = 0.0

    logger.debug("Executing TWISS and SIXTRACK commands")
    madx.twiss()  # used by sixtrack
    madx.sixtrack(cavall=True, radius=0.017)  # this value is only ok for HL(LHC) magnet radius


# ----- Miscellaneous Utilities ----- #


def make_lhc_thin(madx: Madx, sequence: str, slicefactor: int = 1, **kwargs) -> None:
    """
    Executes the ``MAKETHIN`` command for the LHC sequence as previously done in ``MAD-X`` macros.
    This will use the ``teapot`` style and will enforce ``makedipedge``.

    One can find an exemple use of this function in the :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>`
    and :ref:`Free Tracking <demo-free-tracking>` example galleries.

    Args:
        madx (cpymad.madx.Madx): an instantiated `~cpymad.madx.Madx` object.
        sequence (str): the sequence to use for the ``MAKETHIN`` command.
        slicefactor (int): the slice factor to apply in ``MAKETHIN``, which is a factor
            applied to default values for different elements, as did the old macro. Defaults
            to 1.
        **kwargs: any keyword argument will be transmitted to the ``MAD-X`` ``MAKETHN``
            command, namely ``style`` (will default to ``teapot``) and the ``makedipedge``
            flag (will default to `True`).

    Example:
        .. code-block:: python

            >>> make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
    """
    logger.info(f"Slicing sequence '{sequence}'")
    madx.select(flag="makethin", clear=True)
    four_slices_patterns = [r"mbx\.", r"mbrb\.", r"mbrc\.", r"mbrs\."]
    four_slicefactor_patterns = [
        r"mqwa\.",
        r"mqwb\.",
        r"mqy\.",
        r"mqm\.",
        r"mqmc\.",
        r"mqml\.",
        r"mqtlh\.",
        r"mqtli\.",
        r"mqt\.",
    ]

    logger.trace("Defining slices for general MB and MQ elements")
    madx.select(flag="makethin", class_="MB", slice_=2)
    madx.select(flag="makethin", class_="MQ", slice_=2 * slicefactor)

    logger.trace("Defining slices for triplets")
    madx.select(flag="makethin", class_="mqxa", slice_=16 * slicefactor)
    madx.select(flag="makethin", class_="mqxb", slice_=16 * slicefactor)

    logger.trace("Defining slices for various specifc mb elements")
    for pattern in four_slices_patterns:
        madx.select(flag="makethin", pattern=pattern, slice_=4)

    logger.trace("Defining slices for varous specifc mq elements")
    for pattern in four_slicefactor_patterns:
        madx.select(flag="makethin", pattern=pattern, slice_=4 * slicefactor)

    madx.use(sequence=sequence)
    style = kwargs.get("style", "teapot")
    makedipedge = kwargs.get("makedipedge", False)  # defaults to False to compensate default TEAPOT style
    madx.command.makethin(sequence=sequence, style=style, makedipedge=makedipedge)


def re_cycle_sequence(madx: Madx, sequence: str = "lhcb1", start: str = "IP3") -> None:
    """
    Re-cycles the provided *sequence* from a different starting point, given as *start*.

    One can find an exemple use of this function in the :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>`
    and :ref:`Free Tracking <demo-free-tracking>` example galleries.

    Args:
        madx (cpymad.madx.Madx): an instantiated `~cpymad.madx.Madx` object.
        sequence (str): the sequence to re-cycle.
        start (str): element to start the new cycle from.

    Example:
        .. code-block:: python

            >>> lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
    """
    logger.debug(f"Re-cycling sequence '{sequence}' from {start}")
    madx.command.seqedit(sequence=sequence)
    madx.command.flatten()
    madx.command.cycle(start=start)
    madx.command.endedit()


def get_lhc_bpms_list(madx: Madx) -> List[str]:
    """
    Returns the list of monitoring BPMs for the current LHC sequence in use.
    The BPMs are queried through a regex in the result of a ``TWISS`` command.

    .. note::
        As this function calls the ``TWISS`` command and requires that ``TWISS`` can
        succeed on your sequence.

    Args:
        madx (cpymad.madx.Madx): an instantiated cpymad.madx.Madx object.

    Returns:
        The `list` of BPM names.

    Example:
        .. code-block:: python

            >>> observation_bpms = get_lhc_bpms_list(madx)
    """
    twiss_df = twiss.get_twiss_tfs(madx).reset_index()
    bpms_df = twiss_df[twiss_df.NAME.str.contains("^bpm.*B[12]$", case=False, regex=True)]
    return bpms_df.NAME.tolist()


@deprecated(message="Please use its equivalent from the 'cpymadtools.coupling' module.")
def match_no_coupling_through_ripkens(
    madx: Madx, sequence: str = None, location: str = None, vary_knobs: Sequence[str] = None
) -> None:
    """
    Matching routine to get cross-term Ripken parameters :math:`\\beta_{12}` and :math:`\\beta_{21}`
    to be 0 at a given location.

    .. danger::
        This function is deprecated and will be removed in a future version. Please use
        its equivalent from the `~.cpymadtools.coupling` module.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): name of the sequence to activate for the matching.
        location (str): the name of the element at which one wants the cross-term Ripkens to be 0.
        vary_knobs (Sequence[str]): the variables names to ``VARY`` in the ``MAD-X`` routine.
    """
    logger.info(f"Matching Ripken parameters for no coupling at location {location}")
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


def get_lhc_tune_and_chroma_knobs(
    accelerator: str, beam: int = 1, telescopic_squeeze: bool = True
) -> Tuple[str, str, str, str]:
    """
    Gets names of knobs needed to match tunes and chromaticities as a tuple of strings,
    for the LHC or HLLHC machines. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        accelerator (str): Accelerator either 'LHC' (dQ[xy], dQp[xy] knobs) or 'HLLHC'
            (kqt[fd], ks[fd] knobs).
        beam (int): Beam to use, for the knob names. Defaults to 1.
        telescopic_squeeze (bool): if set to `True`, returns the knobs for Telescopic
            Squeeze configuration. Defaults to `True` to reflect run III scenarios.

    Returns:
        A `tuple` of strings with knobs for ``(qx, qy, dqx, dqy)``.

    Examples:
        .. code-block:: python

            >>> get_lhc_tune_and_chroma_knobs("LHC", beam=1, telescopic_squeeze=False)
            ('dQx.b1', 'dQy.b1', 'dQpx.b1', 'dQpy.b1')

        .. code-block:: python

            >>> get_lhc_tune_and_chroma_knobs("HLLHC", beam=2)
            ('kqtf.b2_sq', 'kqtd.b2_sq', 'ksf.b2_sq', 'ksd.b2_sq')
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


# ----- Helpers ----- #


def _all_lhc_arcs(beam: int) -> List[str]:
    """
    Generates and returns the names of all LHC arcs for a given beam.
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Args:
        beam (int): beam to get names for.

    Returns:
        The list of names.
    """
    return [f"A{i+1}{(i+1)%8+1}B{beam:d}" for i in range(8)]


def _get_k_strings(start: int = 0, stop: int = 8, orientation: str = "both") -> List[str]:
    """
    Returns the list of K-strings for various magnets and orders (``K1L``, ``K2SL`` etc strings).
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Args:
        start (int): the starting order, defaults to 0.
        stop (int): the order to go up to, defaults to 8.
        orientation (str): magnet orientation, can be `straight`, `skew` or `both`.
            Defaults to `both`.

    Returns:
        The `list` of names as strings.
    """
    if orientation not in ("straight", "skew", "both"):
        logger.error(f"Orientation '{orientation}' is not accepted, should be one of 'straight', 'skew', 'both'.")
        raise ValueError("Invalid 'orientation' parameter")

    if orientation == "straight":
        orientation = ("",)
    elif orientation == "skew":
        orientation = ("S",)
    else:  # both
        orientation = ("", "S")

    return [f"K{i:d}{s:s}L" for i in range(start, stop) for s in orientation]
