"""
.. _plotting-envelope:

Beam Enveloppe Plotters
-----------------------

Module with functions to create beam enveloppe plots through a `~cpymad.madx.Madx` object.
"""
from typing import Tuple

import matplotlib
import matplotlib.axes
import numpy as np
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.models.beam import BeamParameters
from pyhdtoolkit.plotting.utils import maybe_get_ax


def plot_envelope(
    madx: Madx,
    beam_params: BeamParameters,
    xlimits: Tuple[float, float] = None,
    ylimits: Tuple[float, float] = None,
    plane: str = "Horizontal",
    title: str = None,
    **kwargs,
) -> matplotlib.axes.Axes:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing an estimation of the beam stay-clear enveloppe through the machine,
    as well as an estimation of the aperture limits of elements. One can find an example use of this
    function in the :ref:`beam enveloppe <demo-beam-enveloppe>` example gallery.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam_params (BeamParameters): a validated `~.models.beam.BeamParameters` object one can
            get from `~.optics.beam.compute_beam_parameters`.
        xlimits (Tuple[float, float]): will implement xlim (for the ``s`` coordinate) if this is
            not ``None``, using the tuple passed.
        ylimits (Tuple[float, float]): the y limits for the horizontal plane plot (so
            that machine geometry doesn't make the  plot look shrinked). Defaults to `None`.
        plane (str): the physical plane to plot for, should be either ``Horizontal`` or ``Vertical``,
            and is case-insensitive. Defaults to ``Horizontal``.
        title (Optional[str]): if provided, is set as title of the plot. Defaults to `None`.
        **kwargs: If either `ax` or `axis` is found in the kwargs, the corresponding value is used as the
            axis object to plot on.

    Returns:
            The `~matplotlib.axes.Axes` on which the beam envelope is drawn.

    Example:
        .. code-block:: python

            >>> title = f"Horizontal aperture at {beam_injection.pc_GeV} GeV/c"
            >>> fig, ax = plt.subplots(figsize=(10, 9))
            >>> plot_envelope(madx, beam_injection, title=title)
    """
    if plane.lower() not in ("horizontal", "vertical"):
        logger.error(f"Plane should be either Horizontal or Vertical but '{plane}' was given")
        raise ValueError("Invalid plane value")
    # pylint: disable=too-many-arguments
    # We need to interpolate in order to get high resolution along the S direction
    logger.debug("Plotting estimated machine aperture and beam envelope")

    _interpolate_madx(madx)
    twiss_hr = _get_twiss_hr_from_madx(madx, beam_params)
    machine = twiss_hr[twiss_hr.apertype == "ellipse"]

    axis, kwargs = maybe_get_ax(**kwargs)

    if plane.lower() == "horizontal":
        logger.debug("Plotting the horizontal aperture")
        axis.plot(twiss_hr.s, twiss_hr.envelope_x, color="b")
        axis.plot(twiss_hr.s, -twiss_hr.envelope_x, color="b")
        axis.fill_between(twiss_hr.s, twiss_hr.envelope_x, -twiss_hr.envelope_x, color="b", alpha=0.25)
        axis.fill_between(twiss_hr.s, 3 * twiss_hr.envelope_x, -3 * twiss_hr.envelope_x, color="b", alpha=0.25)
        axis.fill_between(machine.s, machine.aper_1, machine.aper_1 * 100, color="k", alpha=0.5)
        axis.fill_between(machine.s, -machine.aper_1, -machine.aper_1 * 100, color="k", alpha=0.5)
        axis.plot(machine.s, machine.aper_1, "k.-")
        axis.plot(machine.s, -machine.aper_1, "k.-")
        axis.set_ylabel(r"$X \ [m]$")
        axis.set_xlabel(r"$S \ [m]$")
    else:
        logger.debug("Plotting the vertical aperture")
        axis.plot(twiss_hr.s, twiss_hr.envelope_y, color="r")
        axis.plot(twiss_hr.s, -twiss_hr.envelope_y, color="r")
        axis.fill_between(twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25)
        axis.fill_between(twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25)
        axis.fill_between(twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25)
        axis.fill_between(twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25)
        axis.fill_between(machine.s, machine.aper_2, machine.aper_2 * 100, color="k", alpha=0.5)
        axis.fill_between(machine.s, -machine.aper_2, -machine.aper_2 * 100, color="k", alpha=0.5)
        axis.plot(machine.s, machine.aper_2, "k.-")
        axis.plot(machine.s, -machine.aper_2, "k.-")
        axis.set_ylabel(r"$Y \ [m]$")
        axis.set_xlabel(r"$S \ [m]$")

    axis.set_xlim(xlimits)
    axis.set_ylim(ylimits)
    axis.set_title(title)
    return axis


def plot_stay_clear(
    madx: Madx,
    beam_params: BeamParameters,
    xlimits: Tuple[float, float] = None,
    title: str = None,
    **kwargs,
) -> matplotlib.axes.Axes:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing an estimation of the beam stay-clear through the machine,
    One can find an example use of this function in the :ref:`beam enveloppe <demo-beam-enveloppe>`
    example gallery.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam_params (BeamParameters): a validated `~.models.beam.BeamParameters` object one can
            get from `~.optics.beam.compute_beam_parameters`.
        xlimits (Tuple[float, float]): will implement xlim (for the ``s`` coordinate) if this is
            not ``None``, using the tuple passed.
        title (Optional[str]): if provided, is set as title of the plot. Defaults to `None`.
        **kwargs: If either `ax` or `axis` is found in the kwargs, the corresponding value is used as the
            axis object to plot on.

    Returns:
            The `~matplotlib.axes.Axes` on which the stay-clear is drawn.

    Example:
        .. code-block:: python

            >>> title = f"Stay-Clear at {beam_flattop.pc_GeV} GeV/c"
            >>> fig, ax = plt.subplots(figsize=(10, 9))
            >>> plot_stay_clear(madx, beam_flattop, title=title)
    """
    _interpolate_madx(madx)
    twiss_hr = _get_twiss_hr_from_madx(madx, beam_params)
    machine = twiss_hr[twiss_hr.apertype == "ellipse"]

    logger.debug("Plotting the stay-clear envelope")
    axis, kwargs = maybe_get_ax(**kwargs)
    axis.plot(machine.s, machine.aper_1 / machine.envelope_x, ".-b", label="Horizontal")
    axis.plot(machine.s, machine.aper_2 / machine.envelope_y, ".-r", label="Vertical")
    axis.set_xlim(xlimits)
    axis.set_ylabel(r"$\mathrm{n1}$")
    axis.set_xlabel(r"$S \ [m]$")
    axis.legend()
    axis.set_title(title)
    return axis


# ----- Helpers ----- #


def _interpolate_madx(madx: Madx) -> None:
    """Run interpolation on the provided MAD-X instance with default slice values."""
    logger.debug("Running interpolation in MAD-X")
    madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="rbend", slice_=10, range_="#s/#e")
    madx.command.twiss()


def _get_twiss_hr_from_madx(madx: Madx, beam_params: BeamParameters) -> pd.DataFrame:
    """Get twiss hr from the provided MAD-X instance."""
    logger.trace("Getting Twiss dframe from MAD-X")
    twiss_hr: pd.DataFrame = madx.table.twiss.dframe().copy()
    twiss_hr["betatronic_envelope_x"] = np.sqrt(twiss_hr.betx * beam_params.eg_x_m)
    twiss_hr["betatronic_envelope_y"] = np.sqrt(twiss_hr.bety * beam_params.eg_y_m)
    twiss_hr["dispersive_envelope_x"] = twiss_hr.dx * beam_params.deltap_p
    twiss_hr["dispersive_envelope_y"] = twiss_hr.dy * beam_params.deltap_p
    twiss_hr["envelope_x"] = np.sqrt(twiss_hr.betatronic_envelope_x**2 + (twiss_hr.dx * beam_params.deltap_p) ** 2)
    twiss_hr["envelope_y"] = np.sqrt(twiss_hr.betatronic_envelope_y**2 + (twiss_hr.dy * beam_params.deltap_p) ** 2)
    return twiss_hr
