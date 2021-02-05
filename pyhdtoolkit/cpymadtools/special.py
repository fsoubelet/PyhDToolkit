"""
Module cpymadtools.special
--------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to perform MAD-X actions with a cpymad.madx.Madx object, that are very specific to
LHC and HLLHC use cases.
"""
from typing import List

from cpymad.madx import Madx
from loguru import logger

# ----- Utlites ----- #


def power_landau_octupoles(
    cpymad_instance: Madx, mo_current: float, beam: int, defective_arc: bool = False
) -> None:
    """
    Power the Landau octupoles in the (HL)LHC.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        mo_current (float): MO powering in Amps.
        beam (int): beam to use.
        defective_arc: If set to `True`, the KOD in Arc 56 are powered for less Imax.
    """
    try:
        brho = cpymad_instance.globals.nrj * 1e9 / cpymad_instance.globals.clight  # clight is MAD-X constant
    except AttributeError as madx_error:
        logger.error(
            "The global MAD-X variable 'NRJ' should have been set in the optics files but is not defined."
        )
        raise EnvironmentError("No 'NRJ' variable found in scripts") from madx_error

    logger.info(
        f"Powering Landau Octupoles, beam {beam} @ {cpymad_instance.globals.nrj} GeV with {mo_current} A."
    )
    strength = mo_current / cpymad_instance.globals.Imax_MO * cpymad_instance.globals.Kmax_MO / brho
    beam = 2 if beam == 4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            octupole = f"KO{fd}.{arc}"
            logger.trace(f"Powering element '{octupole}' at {strength} Amps")
            cpymad_instance.globals[octupole] = strength

    if defective_arc and (beam == 1):
        cpymad_instance.globals["KOD.A56B1"] = strength * 4.65 / 6  # defective MO group


def deactivate_lhc_arc_sextupoles(cpymad_instance: Madx, beam: int) -> None:
    """
    Deactivate all arc sextupoles in the (HL)LHC.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
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
                cpymad_instance.globals[sextupole] = 0.0


def apply_lhc_colinearity_knob(
    cpymad_instance: Madx, colinearity_knob_value: float = 0, ir: int = None
) -> None:
    """
    Applies the LHC colinearity knob. If you don't know what this is, you should not be using this
    function.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        colinearity_knob_value (float): Units of the colinearity knob to apply. Defaults to 0 so users
            don't mess up local coupling by mistake. This should be a positive integer, normally between 1
            and 10.
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.
    """
    logger.info(f"Applying Colinearity knob with a unit setting of {colinearity_knob_value}")
    logger.warning("You should re-match tunes & chromaticities after this")
    knob_variables = (f"kqsx3.r{ir:d}", f"kqsx3.l{ir:d}")  # MQSX IP coupling correctors
    right_knob, left_knob = knob_variables

    cpymad_instance.globals[right_knob] = colinearity_knob_value * 1e-4
    cpymad_instance.globals[left_knob] = -1 * colinearity_knob_value * 1e-4


def apply_lhc_rigidity_waist_shift_knob(
    cpymad_instance: Madx, rigidty_waist_shift_value: float = 0, ir: int = None, side: str = "left"
) -> None:
    """
    Applies the LHC rigidity waist shift knob, moving the waist left or right of IP. If you don't know what
    this is, you should not be using this function.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        rigidty_waist_shift_value (float): Units of the rigidity waist shift knob (positive values only).
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.
        side (str): Which side of the IP to move the waist to, determines a sign in the calculation.
            Defaults to 'left', which means s_waist < s_ip (and setting it to 'right' would move the waist
            to s_waist > s_ip).
    """
    logger.info(f"Applying Rigidity Waist Shift knob with a unit setting of {rigidty_waist_shift_value}")
    logger.warning("You should re-match tunes & chromaticities after this")
    knob_variables = (f"kqx.r{ir:d}", f"kqx.l{ir:d}")  # Closest IP triplet
    right_knob, left_knob = knob_variables

    current_right_knob = cpymad_instance.globals[right_knob]
    current_left_knob = cpymad_instance.globals[left_knob]

    if side == "left":
        cpymad_instance.globals[right_knob] = (1 - rigidty_waist_shift_value * 0.005) * current_right_knob
        cpymad_instance.globals[left_knob] = (1 + rigidty_waist_shift_value * 0.005) * current_left_knob
    elif side == "right":
        cpymad_instance.globals[right_knob] = (1 + rigidty_waist_shift_value * 0.005) * current_right_knob
        cpymad_instance.globals[left_knob] = (1 - rigidty_waist_shift_value * 0.005) * current_left_knob
    else:
        logger.error(f"Given side '{side}' invalid, only 'left' and 'right' are accepted values.")
        raise ValueError("Invalid value for parameter 'side'.")


def apply_lhc_coupling_knob(
    cpymad_instance: Madx, coupling_knob: float = 0, beam: int = 1, telescopic_squeeze: bool = False
) -> None:
    """
    Applies the LHC coupling knob to reach the desired C- value.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
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

    logger.trace(f"Knob '{knob_name}' is {cpymad_instance.globals[knob_name]} before implementation")
    cpymad_instance.globals[knob_name] = coupling_knob


def make_sixtrack_output(cpymad_instance: Madx, energy: int) -> None:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO JOSCHUA DILLY (@JoschD).
    Prepare output for sixtrack run.

    Args:
        cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
        energy (float): beam energy in GeV.
    """
    logger.info("Preparing outputs for SixTrack")

    logger.debug("Powering RF cavities")
    cpymad_instance.globals["VRF400"] = 8 if energy < 5000 else 16  # is 6 at injection for protons iirc?
    cpymad_instance.globals["LAGRF400.B1"] = 0.5  # cavity phase difference in units of 2pi
    cpymad_instance.globals["LAGRF400.B2"] = 0.0

    logger.debug("Executing TWISS and SIXTRACK commands")
    cpymad_instance.twiss()  # used by sixtrack
    cpymad_instance.sixtrack(cavall=True, radius=0.017)  # this value is only ok for HL(LHC) magnet radius


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
