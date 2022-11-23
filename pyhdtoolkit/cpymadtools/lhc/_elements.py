"""
.. _lhc-elements:

**Elements Utilities**

The functions below are utilities to install elements or markers in the ``LHC``.
"""
from cpymad.madx import Madx
from loguru import logger


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
    .. versionadded:: 0.15.0

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

            >>> install_ac_dipole_as_kicker(
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
    logger.debug("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam")

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
    logger.debug(f"Retrieved values are q1 = {q1:.5f}, q2 = {q2:.5f}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    logger.debug("Querying BETX and BETY at AC Dipole location")
    # All below is done as model_creator macros with `.input()` calls
    madx.input(f"pbeam = beam%lhcb{beam:d}->pc;")
    madx.input(f"betxac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, betx);")
    madx.input(f"betyac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, bety);")

    logger.debug("Calculating AC Dipole voltage values")
    madx.input(f"voltx = 0.042 * pbeam * ABS({deltaqx}) / SQRT(180.0 * betxac) * {sigma_x}")
    madx.input(f"volty = 0.042 * pbeam * ABS({deltaqy}) / SQRT(177.0 * betyac) * {sigma_y}")

    logger.debug("Defining kicker elements for transverse planes")
    madx.input(
        f"MKACH.6L4.B{beam:d}: hacdipole, l=0, freq:={q1_dipole}, lag=0, volt=voltx, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )
    madx.input(
        f"MKACV.6L4.B{beam:d}: vacdipole, l=0, freq:={q2_dipole}, lag=0, volt=volty, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )

    logger.debug(f"Installing AC Dipole kicker with driven tunes of Qx_D = {q1_dipole:.5f}  |  Qy_D = {q2_dipole:.5f}")
    madx.command.seqedit(sequence=f"lhcb{beam:d}")
    madx.command.flatten()
    # The kicker version is meant for a thin lattice and is installed a right at MKQA.6L4.B[12] (at=0)
    madx.command.install(element=f"MKACH.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element=f"MKACV.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-USEd for changes to take effect. Beware that this will reset it, "
        "remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def install_ac_dipole_as_matrix(madx: Madx, deltaqx: float, deltaqy: float, beam: int = 1) -> None:
    """
    .. versionadded:: 0.15.0

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
    logger.debug("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam.")

    logger.debug("Retrieving tunes from internal tables")
    q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
    logger.debug(f"Retrieved values are q1 = {q1:.5f}, q2 = {q2:.5f}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    logger.debug("Querying BETX and BETY at AC Dipole location")
    # All below is done as model_creator macros with `.input()` calls
    madx.input(f"betxac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, betx);")
    madx.input(f"betyac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, bety);")

    logger.debug("Calculating AC Dipole matrix terms")
    madx.input(f"hacmap21 = 2 * (cos(2*pi*{q1_dipole}) - cos(2*pi*{q1})) / (betxac * sin(2*pi*{q1}));")
    madx.input(f"vacmap43 = 2 * (cos(2*pi*{q2_dipole}) - cos(2*pi*{q2})) / (betyac * sin(2*pi*{q2}));")

    logger.debug("Defining matrix elements for transverse planes")
    madx.input(f"hacmap: matrix, l=0, rm21=hacmap21;")
    madx.input(f"vacmap: matrix, l=0, rm43=vacmap43;")

    logger.debug(f"Installing AC Dipole matrix with driven tunes of Qx_D = {q1_dipole:.5f}  |  Qy_D = {q2_dipole:.5f}")
    madx.command.seqedit(sequence=f"lhcb{beam:d}")
    madx.command.flatten()
    # The matrix version is meant for a thick lattice and is installed a little after MKQA.6L4.B[12]
    madx.command.install(element="hacmap", at="1.583 / 2", from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element="vacmap", at="1.583 / 2", from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-USEd for changes to take effect. Beware that this will reset it, "
        "remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def add_markers_around_lhc_ip(madx: Madx, sequence: str, ip: int, n_markers: int, interval: float) -> None:
    """
    .. versionadded:: 1.0.0

    Adds some simple marker elements left and right of an IP point, to increase the granularity of optics
    functions returned from a ``TWISS`` call.

    .. warning::
        You will most likely need to have sliced the sequence before calling this function,
        as otherwise there is a risk on getting a negative drift depending on the affected
        IP. This would lead to the remote ``MAD-X`` process to crash.

    .. warning::
        After editing the *sequence* to add markers, the ``USE`` command will be run for the changes to apply.
        This means the caveats of ``USE`` apply, for instance the erasing of previously defined errors, orbits
        corrections etc.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): which sequence to use the routine on.
        ip (int): The interaction point around which to add markers.
        n_markers (int): how many markers to add on each side of the IP.
        interval (float): the distance between markers, in [m]. Giving ``interval=0.05`` will
            place a marker every 5cm (starting 5cm away from the IP on each side).

    Example:
        .. code-block:: python

            >>> add_markers_around_lhc_ip(
            ...     madx, sequence=f"lhcb1", ip=1, n_markers=1000, interval=0.001
            ... )
    """
    logger.debug(f"Adding {n_markers:d} markers on each side of IP{ip:d}")
    madx.command.seqedit(sequence=sequence)
    madx.command.flatten()
    for i in range(1, n_markers + 1):
        madx.command.install(
            element=f"MARKER.LEFT.IP{ip:d}.{i:02d}", class_="MARKER", at=-i * interval, from_=f"IP{ip:d}"
        )
        madx.command.install(
            element=f"MARKER.RIGHT.IP{ip:d}.{i:02d}", class_="MARKER", at=i * interval, from_=f"IP{ip:d}"
        )
    madx.command.flatten()
    madx.command.endedit()
    logger.warning(
        f"Sequence '{sequence}' will be USEd for new markers to be taken in consideration, beware that this will erase errors etc."
    )
    madx.use(sequence=sequence)
