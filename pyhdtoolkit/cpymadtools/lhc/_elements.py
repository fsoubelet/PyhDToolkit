"""
.. _lhc-elements:

**Elements Utilities**

The functions below are utilities to install elements
or markers in the ``LHC`` in ``MAD-X``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from cpymad.madx import Madx


_MAX_TRACKING_TOP_TURNS: int = 6600


def install_ac_dipole_as_kicker(
    madx: Madx,
    /,
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

    Installs an AC dipole as a kicker element in (HL)LHC beam 1 or 2, for
    tracking. This function makes the assumption that the `lhcb1` / `lhcb2`
    sequence is already defined, sliced, with an associated beam (``BEAM``
    command or `~lhc.make_lhc_beams` function), is matched to the desired
    working point and a ``TWISS`` call has been made.

    Important
    ---------
        In a real machine, the AC Dipole **does** impact the orbit as well as
        the betatron functions when turned on (:cite:t:`Miyamoto:ACD:2008`,
        part III). In ``MAD-X`` however, it cannot be modeled to do both at
        the same time. This routine introduces an AC Dipole as a kicker
        element so that its effect can be seen on particle trajectory
        in tracking. It **does not** affect ``TWISS`` functions.

    Note
    ----
        The sequence should be sliced before calling this function, as the
        AC Dipole is installed at the location of ``MKQA.6L4.B[12]``. This
        is a minor inconvenience as the sequence should be sliced in order
        to perform tracking anyway.

    One can find a full example use of the function for tracking in the
    :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>` example gallery.

    Warning
    -------
        Installing the AC Dipole modifies the sequence, and the ``USE``
        command will be called again at the end of this function. This
        will remove any errors that were installed in the sequence.

        As the errors impact the optics functions which are used during the
        installation of the AC Dipole, it would not be correct to implement
        them only after installing the element.

        Therefore, it is recommended to install the errors and save them with
        the ``ESAVE`` or ``ETABLE`` command, call this function, then
        re-implement the errors with the ``SETERR`` command.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    deltaqx : float
        The deltaQx (horizontal tune excitation) used by the AC dipole.
        This is added on top of the current matched tune.
    deltaqy : float
        The deltaQy (vertical tune excitation) used by the AC dipole.
        This is added on top of the current matched tune.
    sigma_x : float
        The horizontal amplitude to drive the beam to, in bunch sigma.
    sigma_y : float
        The vertical amplitude to drive the beam to, in bunch sigma.
    beam : int
        The LHC beam to install the AC Dipole into, either 1 or 2.
        Defaults to 1.
    start_turn : int
        The turn at which to start ramping up the AC dipole during the
        tracking. Defaults to 100.
    ramp_turns : int
        The number of turns to use for the ramp-up and the ramp-down of
        the AC dipole. This number is important in order to preserve the
        adiabaticity of the cycle. Defaults to 2000, as in the LHC.
    top_turns : int
        The number of turns to drive the beam for at full amplitude of the
        exciting oscillations. Defaults to 6600, as in the LHC.

    Example
    -------
        .. code-block:: python

            install_ac_dipole_as_kicker(
                madx,
                deltaqx=-0.01,  # driven horizontal tune to Qxd = 62.31 - 0.01 = 62.30
                deltaqy=0.012,  # driven vertical tune to Qyd = 60.32 + 0.012 = 60.332
                sigma_x=2,  # bunch amplitude kick in the horizontal plane
                sigma_y=2,  # bunch amplitude kick in the vertical plane
                beam=1,  # beam for which to install and kick
                start_turn=100,  # when to turn on the AC Dipole
                ramp_turns=2000,  # how many turns to ramp up/down the AC Dipole
                top_turns=6600,  # how many turns to keep the AC Dipole at full kick
            )
    """
    logger.warning("This AC Dipole is implemented as a kicker and will not affect TWISS functions!")
    logger.debug("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam")

    if top_turns > _MAX_TRACKING_TOP_TURNS:
        logger.warning(
            f"Configuring the AC Dipole for {top_turns:d} of driving is fine for MAD-X "
            "but is higher than what the device can do in the (HL)LHC! Beware."
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
    # The kicker version is meant for a thin lattice and is installed right at MKQA.6L4.B[12] (at=0)
    madx.command.install(element=f"MKACH.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element=f"MKACV.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-USEd for changes to take effect. "
        "Beware that this will reset it, remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def install_ac_dipole_as_matrix(madx: Madx, /, deltaqx: float, deltaqy: float, beam: int = 1) -> None:
    """
    .. versionadded:: 0.15.0

    Installs an AC dipole as a matrix element in (HL)LHC beam 1 or 2, to
    see its effect on TWISS functions. This function makes the assumption
    that the `lhcb1` / `lhcb2` sequence is already defined, sliced, with
    an associated beam (``BEAM`` command or `~lhc.make_lhc_beams` function),
    is matched to the desired working point and a ``TWISS`` call has been made.

    This function's use is very similar to that of
    :func:`install_ac_dipole_as_kicker`.

    Important
    ---------
        In a real machine, the AC Dipole **does** impact the orbit as well as
        the betatron functions when turned on (:cite:t:`Miyamoto:ACD:2008`,
        part III). In ``MAD-X`` however, it cannot be modeled to do both at
        the same time. This routine introduces an AC Dipole as a matrix element
        so that its effect can be seen on ``TWISS`` functions. It **does not**
        affect tracking.

    Warning
    -------
        Installing the AC Dipole modifies the sequence, and the ``USE``
        command will be called again at the end of this function. This
        will remove any errors that were installed in the sequence.

        As the errors impact the optics functions which are used during the
        installation of the AC Dipole, it would not be correct to implement
        them only after installing the element.

        Therefore, it is recommended to install the errors and save them with
        the ``ESAVE`` or ``ETABLE`` command, call this function, then
        re-implement the errors with the ``SETERR`` command.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    deltaqx : float
        The deltaQx (horizontal tune excitation) used by the AC dipole.
        This is added on top of the current matched tune.
    deltaqy : float
        The deltaQy (vertical tune excitation) used by the AC dipole.
        This is added on top of the current matched tune.
    beam : int
        The LHC beam to install the AC Dipole into, either 1 or 2.
        Defaults to 1.

    Example
    -------
        .. code-block:: python

            install_ac_dipole_as_matrix(madx, deltaqx=-0.01, deltaqy=0.012, beam=1)
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
    madx.input("hacmap: matrix, l=0, rm21=hacmap21;")
    madx.input("vacmap: matrix, l=0, rm43=vacmap43;")

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


def add_markers_around_lhc_ip(madx: Madx, /, sequence: str, ip: int, n_markers: int, interval: float) -> None:
    """
    .. versionadded:: 1.0.0

    Adds some simple marker elements left and right of an IP, to increase
    the granularity of optics functions returned from a ``TWISS`` call.

    Warning
    -------
        It is most likely needed to have sliced the sequence before calling
        this function, as otherwise there is a risk on getting a negative
        drift depending on the affected IP. This would lead to the remote
        ``MAD-X`` process to crash.

    Warning
    -------
        After editing the *sequence* to add markers, the ``USE`` command will
        be called for the changes to apply. This means the caveats of ``USE``
        apply, for instance the erasing of previously defined errors, orbits
        corrections etc.

        Therefore, it is recommended to install the errors and save them with
        the ``ESAVE`` or ``ETABLE`` command, call this function, then
        re-implement the errors with the ``SETERR`` command.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    sequence : str
        Which sequence to use the routine on.
    ip : int
        The interaction point around which to add markers.
    n_markers : int
        How many markers to add on each side of the IP.
    interval : float
        The distance between markers, in [m]. Giving ``interval=0.05`` will
        place a marker every 5cm (starting 5cm away from the IP) on each side.

    Example
    -------
        .. code-block:: python

            add_markers_around_lhc_ip(
                madx, sequence=f"lhcb1", ip=1, n_markers=1000, interval=0.001
            )
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
