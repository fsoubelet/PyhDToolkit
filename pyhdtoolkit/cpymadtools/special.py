"""
Module cpymadtools.special
--------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X actions with a cpymad.madx.Madx object, that are very specific to
what I do in LHC and HLLHC use cases.
"""
from typing import List, Sequence

import numpy as np

from cpymad.madx import Madx
from loguru import logger

# ----- Setup Utlites ----- #


def make_lhc_beams(madx: Madx, energy: float = 6500, emittance: float = 3.75e-6, **kwargs) -> None:
    """
    Define beams with default configuratons for `LHCB1` and `LHCB2` sequences.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        energy (float): beam energy in GeV. Defaults to 6500.
        emittance (float): emittance in meters, which will be used to calculate geometric emittance,
            then fed to the BEAM command.

    Keyword Args:
        Any keyword argument that can be given to the MAD-X BEAM command.
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
            npart=1.0e10,
            ex=geometric_emit,
            ey=geometric_emit,
            **kwargs,
        )


def power_landau_octupoles(madx: Madx, mo_current: float, beam: int, defective_arc: bool = False) -> None:
    """
    Power the Landau octupoles in the (HL)LHC.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        mo_current (float): MO powering in Amps.
        beam (int): beam to use.
        defective_arc: If set to `True`, the KOD in Arc 56 are powered for less Imax.
    """
    try:
        brho = madx.globals.nrj * 1e9 / madx.globals.clight  # clight is MAD-X constant
    except AttributeError as madx_error:
        logger.error(
            "The global MAD-X variable 'NRJ' should have been set in the optics files but is not defined."
        )
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
    Deactivate all arc sextupoles in the (HL)LHC.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        beam (int): beam to use.
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
    Applies the LHC colinearity knob. If you don't know what this is, you should not be using this
    function.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        colinearity_knob_value (float): Units of the colinearity knob to apply. Defaults to 0 so users
            don't mess up local coupling by mistake. This should be a positive integer, normally between 1
            and 10.
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.
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
    Applies the LHC rigidity waist shift knob, moving the waist left or right of IP. If you don't know what
    this is, you should not be using this function. The waist shift is done by unbalancing the
    triplet powering knob of the left and right-hand sides of the IP.

    Warning: Applying the shift will modify your tunes and most likely flip them, making a subsequent
    matching impossible if your lattice has coupling. To avoid this, match to tunes split further apart
    before applying the waist shift knob, and then match to the desired working point. For instance for
    the LHC, matching to (62.27, 60.36) before applying and afterwards rematching to (62.31, 60.32) usually
    works well.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        rigidty_waist_shift_value (float): Units of the rigidity waist shift knob (positive values only).
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.
        side (str): Which side of the IP to move the waist to, determines a sign in the calculation.
            Defaults to 'left', which means s_waist < s_ip (and setting it to 'right' would move the waist
            to s_waist > s_ip).
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
    madx: Madx, coupling_knob: float = 0, beam: int = 1, telescopic_squeeze: bool = False
) -> None:
    """
    Applies the LHC coupling knob to reach the desired C- value.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        coupling_knob (float): Desired value for the Cminus, typically a few units of 1E-3. Defaults to 0
        so users don't mess up coupling by mistake
        beam (int): beam to apply the knob to, defaults to beam 1.
        telescopic_squeeze (bool): if set to True, uses the knobs for Telescopic Squeeze configuration.
            Defaults to False.
    """
    logger.info("Applying coupling knob")
    logger.warning("You should re-match tunes & chromaticities after this")
    suffix = "_sq" if telescopic_squeeze else ""
    knob_name = f"CMRS.b{beam:d}{suffix}"

    logger.trace(f"Knob '{knob_name}' is {madx.globals[knob_name]} before implementation")
    madx.globals[knob_name] = coupling_knob
    logger.trace(f"Set '{knob_name}' to {madx.globals[knob_name]}")


def install_ac_dipole(
    madx: Madx,
    deltaqx: float,
    deltaqy: float,
    sigma_x: float,
    sigma_y: float,
    geometric_emit: float = None,
    start_turn: int = 100,
    ramp_turns: int = 2000,
    top_turns: int = 6600,
) -> None:
    """
    Installs an AC dipole for BEAM 1 ONLY.
    This function assumes that you have already defined lhcb1, made a beam for it (BEAM command or
    `make_lhc_beams` function) and matched to your desired working point.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        deltaqx (float): the deltaQx (horizontal tune excitation) used by the AC dipole.
        deltaqy (float): the deltaQy (vertical tune excitation) used by the AC dipole.
        sigma_x (float): the horizontal amplitude to drive the beam to, in bunch sigma.
        sigma_y (float): the vertical amplitude to drive the beam to, in bunch sigma.
        geometric_emit (float): the geometric emittance that was used when defining the beam. If not
            provided, it is assumed that 'geometric_emit' is a defined global in MAD-X, and the value will
            be directly queried from the internal tables.
        start_turn (int): the turn at which to start ramping up the AC dipole. Defaults to 100.
        ramp_turns (int): the number of turns to use for the ramp-up and the ramp-down of the AC dipole.
            This number is important in order to preserve the adiabaticity of the cycle. Defaults to 2000
            as in the LHC.
        top_turns (int): the number of turns to drive the beam for. Defaults to 6600 as in the LHC.
    """
    if top_turns > 6600:
        logger.warning(
            f"Configuring the AC Dipole for {top_turns} of driving is fine for MAD-X but is "
            "higher than what the device can do in the (HL)LHC! Beware."
        )
    ramp1, ramp2 = start_turn, start_turn + ramp_turns
    ramp3 = ramp2 + top_turns
    ramp4 = ramp3 + ramp_turns

    logger.debug("Retrieving tunes from internal tables")
    q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
    logger.trace(f"Retrieved values are q1 = {q1}, q2 = {q2}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    if not geometric_emit:
        logger.debug(
            "No value provided for the geometric emittance used when creating the beam, the value will be "
            "queried from MAD-X's global 'geometric_emit'"
        )
        geometric_emit = madx.globals["geometric_emit"]

    logger.info(f"Installing AC Dipole to drive the tunes to Qx_D = {q1_dipole}  |  Qy_D = {q2_dipole}")
    madx.input(
        f"MKACH.6L4.B1: hacdipole, l=0, freq:={q1_dipole}, lag=0, volt:=voltx, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )
    madx.input(
        f"MKACV.6L4.B1: vacdipole, l=0, freq:={q2_dipole}, lag=0, volt:=volty, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )
    madx.command.seqedit(sequence="lhcb1")
    madx.command.flatten()
    madx.command.install(element="MKACH.6L4.B1", at="0.0", from_="MKQA.6L4.B1")
    madx.command.install(element="MKACV.6L4.B1", at="0.0", from_="MKQA.6L4.B1")
    madx.command.endedit()

    logger.trace("Querying BETX and BETY at AC Dipole location")
    madx.input("betax_acd = table(twiss, MKQA.6L4.B1, betx);")
    madx.input("betay_acd = table(twiss, MKQA.6L4.B1, bety);")

    betax_acd = madx.globals["betax_acd"]
    betay_acd = madx.globals["betay_acd"]
    brho = madx.sequence.lhcb1.beam.brho
    voltx = sigma_x * np.sqrt(geometric_emit) * brho * np.abs(deltaqx) * 4 * np.pi / np.sqrt(betax_acd)
    volty = sigma_y * np.sqrt(geometric_emit) * brho * np.abs(deltaqy) * 4 * np.pi / np.sqrt(betay_acd)
    madx.globals["voltx"] = voltx
    madx.globals["volty"] = volty


def vary_independent_ir_quadrupoles(
    madx: Madx, quad_numbers: Sequence[int], ip: int, sides: Sequence[str] = ("r", "l"), beam: int = 1
) -> None:
    """
    Send the `vary` commands for the desired quadrupoles in the IRs. The independent quadrupoles for which
    this is implemented are Q4 to Q13 included. This is useful to setup some specific matching involving
    these elements.

    It is necessary to have defined a 'brho' variable when creating your beams.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        quad_numbers (Sequence[int]): quadrupoles to be varied, by number (aka position from IP).
        ip (int): the IP around which to apply the instructions. Defaults to 1.
        sides (Sequence[str]): the sides of IP to act on. Should be `R` for right and `L` for left.
            Defaults to both sides of the IP.
        beam (int): the beam for which to apply the instructions. Defaults to 1.
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


# ----- Output Utilities ----- #


def make_sixtrack_output(madx: Madx, energy: int) -> None:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Prepare output for sixtrack run.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        energy (float): beam energy in GeV.
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
    Makethin for the LHC sequence as previously done in MAD-X macros. This will use the `teapot` style and
    will enforce `makedipedge`.

    Args:
        madx (Madx): an instantiated cpymad.madx.Madx object.
        sequence (str): the sequence to use for the MAKETHIN command.
        slicefactor (int): the slice factor to apply in makethin. Defaults to 1.

    Keyword Args:
        The keyword arguments for the MAD-X MAKETHN commands, namely `style` (will default to `teapot`) and
        the `makedipedge` flag (will default to True).
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
    madx.select(flag="makethin", class_="MB", slice=2)
    madx.select(flag="makethin", class_="MQ", slice=2 * slicefactor)

    logger.trace("Defining slices for triplets")
    madx.select(flag="makethin", class_="mqxa", slice=16 * slicefactor)
    madx.select(flag="makethin", class_="mqxb", slice=16 * slicefactor)

    logger.trace("Defining slices for various specifc mb elements")
    for pattern in four_slices_patterns:
        madx.select(flag="makethin", pattern=pattern, slice=4)

    logger.trace("Defining slices for varous specifc mq elements")
    for pattern in four_slicefactor_patterns:
        madx.select(flag="makethin", pattern=pattern, slice=4 * slicefactor)

    madx.use(sequence=sequence)
    style = kwargs.get("style", "teapot")
    makedipedge = kwargs.get("makedipedge", False)  # defaults to False to compensate default TEAPOT style
    madx.command.makethin(sequence=sequence, style=style, makedipedge=makedipedge)


def re_cycle_sequence(madx: Madx, sequence: str = "lhcb1", start: str = "IP3") -> None:
    """
    Re-cycle the provided sequence from a different starting point.

    Args:
        madx (Madx): an instantiated cpymad.madx.Madx object.
        sequence (str): the sequence to re cycle.
        start (str): element to start the new cycle from.
    """
    logger.debug(f"Re-cycling sequence '{sequence}' from {start}")
    madx.command.seqedit(sequence=sequence)
    madx.command.flatten()
    madx.command.cycle(start=start)
    madx.command.endedit()


def match_no_coupling_through_ripkens(
    madx: Madx, sequence: str = None, location: str = None, vary_knobs: Sequence[str] = None
) -> None:
    """
    Matching routine to get cross-term Ripken parameters beta_12 and beta_21 to be 0 at a given location.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        sequence (str): name of the sequence to activate for the matching.
        location (str): the name of the element at which one wants the cross-term Ripkens to be 0.
        vary_knobs (Sequence[str]): the variables names to 'vary' in the MADX routine.
    """
    logger.info(f"Matching Ripken parameters for no coupling at location {location}")
    logger.debug("Creating macro tu update Ripkens")
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


def _all_lhc_arcs(beam: int) -> List[str]:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Names of all LHC arcs for a given beam.

    Args:
        beam (int): beam to get names for.

    Returns:
        The list of names.
    """
    return [f"A{i+1}{(i+1)%8+1}B{beam:d}" for i in range(8)]


def _get_k_strings(start: int = 0, stop: int = 8, orientation: str = "both") -> List[str]:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Returns the list of K-strings for various magnets and orders (K1L, K2SL etc strings).

    Args:
        start (int): the starting order, defaults to 0.
        stop (int): the order to go up to, defaults to 8.
        orientation (str): magnet orientation, can be 'straight', 'skew' or 'both'. Defaults to 'both'.

    Returns:
        The list of names as strings.
    """
    if orientation not in ("straight", "skew", "both",):
        logger.error(
            f"Orientation '{orientation}' is not accepted, should be one of 'straight', 'skew', 'both'."
        )
        raise ValueError("Invalid 'orientation' parameter")

    if orientation == "straight":
        orientation = ("",)
    elif orientation == "skew":
        orientation = ("S",)
    else:  # both
        orientation = ("", "S")

    return [f"K{i:d}{s:s}L" for i in range(start, stop) for s in orientation]
