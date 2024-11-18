"""
.. _lhc-powering:

**Powering Utilities**

The functions below are magnets or knobs powering utilities for the ``LHC``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cpymad.madx import Madx

_BEAM4: int = 4  # LHC beam 4 is special case
_QUAD_CIRCUIT_HAS_B: int = 7  # Q7 has a .b in the circuit name
_MAX_IR_QUAD_NUMBER: int = 11  # beyond Q11 are MQTs etc


def apply_lhc_colinearity_knob(madx: Madx, /, colinearity_knob_value: float = 0, ir: int | None = None) -> None:
    """
    .. versionadded:: 0.15.0

    Applies the a trim of the LHC colinearity knob.

    Warning
    -------
        If you don't know what this is, then you most likely should not be
        using this function.

    Tip
    ---
        The convention, which is also the one I implemented in ``LSA`` for the
        ``LHC``, is that a positive value of the colinearity knob results in a
        powering increase of the ``MQSX`` *right* of the IP, and a powering
        decrease of the ``MQSX`` *left* of the IP.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    colinearity_knob_value : float
        Units of the colinearity knob to apply. Defaults to 0 so users don't mess
        up local IR coupling by mistake. This should be a positive integer, normally
        between 1 and 10.
    ir : int
        The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
        Classically 1 or 5.

    Example
    -------
        .. code-block:: python

            apply_lhc_colinearity_knob(madx, colinearity_knob_value=5, ir=1)
    """
    if ir is None or ir not in (1, 2, 5, 8):
        logger.error("Invalid IR number provided, not applying any error.")
        msg = "Invalid 'ir' argument"
        raise ValueError(msg)

    logger.debug(f"Applying Colinearity knob with a unit setting of {colinearity_knob_value}")
    logger.warning("You should re-match tunes & chromaticities after this colinearity knob is applied")
    knob_variables = (f"KQSX3.R{ir:d}", f"KQSX3.L{ir:d}")  # MQSX IP coupling correctors powering
    right_knob, left_knob = knob_variables

    madx.globals[right_knob] = colinearity_knob_value * 1e-4
    logger.debug(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    madx.globals[left_knob] = -1 * colinearity_knob_value * 1e-4
    logger.debug(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_colinearity_knob_delta(madx: Madx, /, colinearity_knob_delta: float = 0, ir: int | None = None) -> None:
    """
    .. versionadded:: 0.21.0

    This is essentially the same as `.apply_lhc_colinearity_knob`, but instead
    of a applying fixed powering value, it applies a delta to the (potentially)
    existing value.

    Warning
    -------
        If you don't know what this is, then you most likely should not be
        using this function.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    colinearity_knob_value : float
        Units of the colinearity knob to vary the existing knob with.
        Defaults to 0 so users don't mess up local IR coupling by mistake.
        This should be a positive integer, normally between 1 and 10.
    ir : int
        The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
        Classically 1 or 5.

    Example
    -------
        .. code-block:: python

            apply_lhc_colinearity_knob_delta(madx, colinearity_knob_delta=3.5, ir=1)
    """
    if ir is None or ir not in (1, 2, 5, 8):
        logger.error("Invalid IR number provided, not applying any error.")
        msg = "Invalid 'ir' argument"
        raise ValueError(msg)

    logger.debug(f"Applying Colinearity knob delta of {colinearity_knob_delta}")
    logger.warning("You should re-match tunes & chromaticities after this delta is applied")
    knob_variables = (f"KQSX3.R{ir:d}", f"KQSX3.L{ir:d}")  # MQSX IP coupling correctors powering
    right_knob, left_knob = knob_variables

    logger.debug("Query current knob values")
    current_right = madx.eval(right_knob)  # ugly, but avoids KeyError if not defined yet
    current_left = madx.eval(left_knob)  # augly, but avoids KeyError if not defined yet
    logger.debug(f"Current right knob value is {current_right}")
    logger.debug(f"Current left knob value is {current_left}")

    madx.globals[right_knob] = current_right + colinearity_knob_delta * 1e-4
    logger.debug(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    madx.globals[left_knob] = current_left - colinearity_knob_delta * 1e-4
    logger.debug(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_rigidity_waist_shift_knob(
    madx: Madx, /, rigidty_waist_shift_value: float = 0, ir: int | None = None, side: str = "left"
) -> None:
    """
    .. versionadded:: 0.15.0

    Applies a trim of the LHC rigidity waist shift knob, moving the waist left
    or right of IP. The waist shift is achieved by moving all four betatron
    waists simltaneously: unbalancing the triplet powering knobs of the left
    and right-hand sides of the IP.

    Warning
    -------
        If you don't know what this is, then you most likely should not be
        using this function.

    Important
    ---------
        Applying the shift will modify your tunes and is likely to flip them,
        making a subsequent matching impossible if your lattice has coupling.
        To avoid this, one should match to tunes split further apart before
        applying the waist shift knob, and then match to the desired working
        point. For instance for the LHC, matching to (62.27, 60.36) before
        applying and afterwards rematching to (62.31, 60.32) usually works
        quite well.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    rigidty_waist_shift_value : float
        Units of the rigidity waist shift knob (positive values only). Defaults
        to 0 so users don't mess up the IR setup by mistake.
    ir : int
        The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
        Classically 1 or 5.
    side : str
        Which side of the IP to move the waist to. This parameter determines a
        sign in the calculation. Defaults to `left`, which means that
        :math:`s_{\\mathrm{waist}} \\lt s_{\\mathrm{ip}}` (and setting it to
        `right` would move the waist such that
        :math:`s_{\\mathrm{waist}} \\gt s_{\\mathrm{ip}}`).

    Example
    -------
        .. code-block:: python

            # It is recommended to re-match tunes after this routine
            matching.match_tunes(madx, "lhc", "lhcb1", 62.27, 60.36)
            apply_lhc_rigidity_waist_shift_knob(madx, rigidty_waist_shift_value=1.5, ir=5)
            matching.match_tunes(madx, "lhc", "lhcb1", 62.31, 60.32)
    """
    if ir is None or ir not in (1, 2, 5, 8):
        logger.error("Invalid IR number provided, not applying any error.")
        msg = "Invalid 'ir' argument"
        raise ValueError(msg)

    logger.debug(f"Applying Rigidity Waist Shift knob with a unit setting of {rigidty_waist_shift_value}")
    logger.warning("You should re-match tunes & chromaticities after this rigid waist shift knob is applied")
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
        msg = "Invalid value for parameter 'side'."
        raise ValueError(msg)

    logger.debug(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    logger.debug(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_coupling_knob(
    madx: Madx, /, coupling_knob: float = 0, beam: int = 1, telescopic_squeeze: bool = True
) -> None:
    """
    .. versionadded:: 0.15.0

    Applies a trim of the LHC coupling knob to reach the desired :math:`|C^{-}|`
    (global coupling) value.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    coupling_knob : float
        Desired value for the Cminus, typically a few units of ``1E-3``.
        Defaults to 0 so users don't mess up coupling by mistake.
    beam : int
        Beam to apply the knob to. Defaults to beam 1.
    telescopic_squeeze : bool
        If set to `True`, uses the ``(HL)LHC`` knobs for Telescopic
        Squeeze configuration. Defaults to `True` to reflect Run 3
        scenarios since `v0.9.0`.

    Example
    -------
        .. code-block:: python

            apply_lhc_coupling_knob(madx, coupling_knob=5e-4, beam=1)
    """
    # NOTE: for maintainers, no `_op` suffix on ATS coupling knobs, only `_sq` even in Run 3
    logger.debug("Applying coupling knob")
    logger.warning("You should re-match tunes & chromaticities after this coupling knob is applied")
    suffix = "_sq" if telescopic_squeeze else ""
    # NOTE: Only using this knob will give a dqmin very close to coupling_knob
    # If one wants to also assign f"CMIS.b{beam:d}{suffix}" the dqmin will be > coupling_knob
    knob_name = f"CMRS.b{beam:d}{suffix}"

    logger.debug(f"Knob '{knob_name}' is {madx.globals[knob_name]} before implementation")
    madx.globals[knob_name] = coupling_knob
    logger.debug(f"Set '{knob_name}' to {madx.globals[knob_name]}")


def carry_colinearity_knob_over(madx: Madx, /, ir: int, to_left: bool = True) -> None:
    """
    .. versionadded:: 0.20.0

    Removes the powering setting on one side of the colinearty knob and applies
    it to the other side.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    ir : int
        The Interaction Region around which to apply the change, should be
        one of [1, 2, 5, 8].
    to_left : bool
        If `True`, the magnet right of IP is de-powered of and its powering
        is transferred to the magnet left of IP. If `False`, then the opposite
        happens. Defaults to `True`.

    Example
    -------
        .. code-block:: python

            carry_colinearity_knob_over(madx, ir=5, to_left=True)
    """
    side = "left" if to_left else "right"
    logger.debug(f"Carrying colinearity knob powering around IP{ir:d} over to the {side} side")

    left_variable, right_variable = f"kqsx3.l{ir:d}", f"kqsx3.r{ir:d}"
    left_powering, right_powering = madx.globals[left_variable], madx.globals[right_variable]
    logger.debug(f"Current powering values are: '{left_variable}'={left_powering} | '{right_variable}'={left_powering}")

    new_left = left_powering + right_powering if to_left else 0
    new_right = 0 if to_left else left_powering + right_powering
    logger.debug(f"New powering values are: '{left_variable}'={new_left} | '{right_variable}'={new_right}")
    madx.globals[left_variable] = new_left
    madx.globals[right_variable] = new_right
    logger.debug("New powerings applied")


def power_landau_octupoles(madx: Madx, /, beam: int, mo_current: float, defective_arc: bool = False) -> None:
    """
    .. versionadded:: 0.15.0

    Powers the Landau octupoles in the (HL)LHC.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    beam : int
        The beam to use.
    mo_current : float
        The MO powering in [A].
    defective_arc : bool
        If set to `True`, the ``KOD`` in Arc 56 are powered for less ``Imax``.
        Defaults to `False`.

    Example
    -------
        .. code-block:: python

            power_landau_octupoles(madx, beam=1, mo_current=350, defect_arc=True)
    """
    try:
        brho = madx.globals.nrj * 1e9 / madx.globals.clight  # clight is MAD-X constant
    except AttributeError as madx_error:
        logger.exception("The global MAD-X variable 'NRJ' should have been set in the optics files but is not defined.")
        msg = "No 'NRJ' variable found in scripts"
        raise AttributeError(msg) from madx_error

    logger.debug(f"Powering Landau Octupoles, beam {beam} @ {madx.globals.nrj} GeV with {mo_current} A.")
    strength = mo_current / madx.globals.Imax_MO * madx.globals.Kmax_MO / brho
    beam = 2 if beam == _BEAM4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            octupole = f"KO{fd}.{arc}"
            logger.debug(f"Powering element '{octupole}' at {strength} Amps")
            madx.globals[octupole] = strength

    if defective_arc and (beam == 1):
        madx.globals["KOD.A56B1"] = strength * 4.65 / 6  # defective MO group


def deactivate_lhc_arc_sextupoles(madx: Madx, /, beam: int) -> None:
    """
    .. versionadded:: 0.15.0

    Deactivates all arc sextupoles in the (HL)LHC.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    beam : int
        The beam to use.

    Example
    -------
        .. code-block:: python

            deactivate_lhc_arc_sextupoles(madx, beam=1)
    """
    # KSF1 and KSD2 - Strong sextupoles of sectors 81/12/45/56
    # KSF2 and KSD1 - Weak sextupoles of sectors 81/12/45/56
    # Rest: Weak sextupoles in sectors 78/23/34/67
    logger.debug(f"Deactivating all arc sextupoles for beam {beam}.")
    beam = 2 if beam == _BEAM4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            for i in (1, 2):
                sextupole = f"KS{fd}{i:d}.{arc}"
                logger.debug(f"De-powering element '{sextupole}'")
                madx.globals[sextupole] = 0.0


def vary_independent_ir_quadrupoles(
    madx: Madx, /, quad_numbers: Sequence[int], ip: int, sides: Sequence[str] = ("r", "l"), beam: int = 1
) -> None:
    """
    .. versionadded:: 0.15.0

    Sends the ``VARY`` commands for the desired quadrupoles in the IR surrounding
    the provided *ip*. The independent quadrupoles for which this is implemented
    are Q4 to Q13 included. This is useful to setup some specific matching involving
    these elements.

    Important
    ---------
        It is necessary to have defined a ``brho`` variable when creating your beams.
        If one has used the `~lhc.make_lhc_beams` function to create the beams, this
        has already been done automatically.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    quad_numbers : Sequence[int]
        Quadrupoles to be varied, by number (aka position from IP).
    ip : int
        The IP around which to apply the instructions.
    sides : Sequence[str]
        Sides of the IP for which to apply error on the triplets, either
        L, R or both, case insensitive. Defaults to both.
    beam : int
        The beam for which to apply the instructions. Defaults to 1.

    Example
    -------
        .. code-block:: python

            vary_independent_ir_quadrupoles(
                madx, quad_numbers=[10, 11, 12, 13], ip=1, sides=("r", "l")
            )
    """
    if (
        ip not in (1, 2, 5, 8)
        or any(side.upper() not in ("R", "L") for side in sides)
        or any(quad not in (4, 5, 6, 7, 8, 9, 10, 11, 12, 13) for quad in quad_numbers)
    ):
        logger.error("Either the IP number of the side provided are invalid, not applying any error.")
        msg = "Invalid 'quad_numbers', 'ip', 'sides' argument"
        raise ValueError(msg)

    logger.debug(f"Preparing a knob involving quadrupoles {quad_numbers}")
    # Each quad has a specific power circuit used for their k1 boundaries
    power_circuits: dict[int, str] = {
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
            logger.debug(f"Sending vary command for Q{quad}{side.upper()}{ip}")
            madx.command.vary(
                name=f"kq{'t' if quad >= _MAX_IR_QUAD_NUMBER else ''}{'l' if quad == _MAX_IR_QUAD_NUMBER else ''}{quad}.{side}{ip}b{beam}",
                step=1e-7,
                lower=f"-{circuit}.{'b' if quad == _QUAD_CIRCUIT_HAS_B else ''}{quad}{side}{ip}.b{beam}->kmax/brho",
                upper=f"+{circuit}.{'b' if quad == _QUAD_CIRCUIT_HAS_B else ''}{quad}{side}{ip}.b{beam}->kmax/brho",
            )


def switch_magnetic_errors(madx: Madx, /, **kwargs) -> None:
    """
    .. versionadded:: 0.7.0

    Applies magnetic field orders. This will only work for ``LHC`` and ``HLLHC``
    machines. Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    **kwargs:
        The setting works through keyword arguments, and several specific kwargs
        are expected. `default` sets global default to this value (defaults to
        `False`). `AB#` sets the default for all of that order, the order being
        the `#` number. `A#` or `B#` sets the default for systematic and random
        of this id. `A#s`, `B#r`, etc. sets the specific value for this given
        order. In all kwargs, the order # should be in the range [1...15], where
        1 == dipolar field.

    Examples
    --------

        Set random values for (alsmost) all of these orders:

        .. code-block:: python

            random_kwargs = {}
            for order in range(1, 16):
                for ab in "AB":
                    random_kwargs[f"{ab}{order:d}"] = random.randint(0, 20)
            switch_magnetic_errors(madx, **random_kwargs)

        Set a given value for ``B6`` order magnetic errors only:

        .. code-block:: python

            switch_magnetic_errors(madx, **{"B6": 1e-4})
    """
    logger.debug("Setting magnetic errors")
    global_default = kwargs.get("default", False)

    for order in range(1, 16):
        logger.debug(f"Setting up for order {order}")
        order_default = kwargs.get(f"AB{order:d}", global_default)

        for ab in "AB":
            ab_default = kwargs.get(f"{ab}{order:d}", order_default)
            for sr in "sr":
                name = f"{ab}{order:d}{sr}"
                error_value = int(kwargs.get(name, ab_default))
                logger.debug(f"Setting global for 'ON_{name}' to {error_value}")
                madx.globals[f"ON_{name}"] = error_value


# ----- Helpers ----- #


def _all_lhc_arcs(beam: int) -> list[str]:
    """
    Generates and returns the names of all LHC arcs for a given beam.
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Parameters
    ----------
    beam : int
        The beam to get arc names for.

    Returns
    -------
    list[str]
        The list of arc names.
    """
    return [f"A{i+1}{(i+1)%8+1}B{beam:d}" for i in range(8)]
