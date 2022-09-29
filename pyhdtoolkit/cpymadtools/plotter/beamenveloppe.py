"""
.. _cpymadtools-plotters-beamenveloppe:

Beam Enveloppe Plotters
-----------------------

Module with functions to create beam enveloppe plots through a `~cpymad.madx.Madx` object.
"""
from pathlib import Path
from typing import Tuple

import matplotlib
import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.models.beam import BeamParameters


def plot_envelope(
    madx: Madx,
    beam_params: BeamParameters,
    figsize: Tuple[int, int] = (13, 20),
    xlimits: Tuple[float, float] = None,
    hplane_ylim: Tuple[float, float] = None,
    vplane_ylim: Tuple[float, float] = None,
    savefig: str = None,
) -> matplotlib.figure.Figure:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing an estimation of the beam stay-clear enveloppe through the machine,
    as well as an estimation of the aperture limits of elements. One can find an example use of this
    function in the :ref:`beam enveloppe <demo-beam-enveloppe>` example gallery.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam_params (BeamParameters): a validated `~.models.beam.BeamParameters` object one can
            get from `~.optics.beam.compute_beam_parameters`.
        figsize (Tuple[int, int]): size of the figure, defaults to (13, 20).
        xlimits (Tuple[float, float]): will implement xlim (for the ``s`` coordinate) if this is
            not ``None``, using the tuple passed.
        hplane_ylim (Tuple[float, float]): the y limits for the horizontal plane plot (so
            that machine geometry doesn't make the  plot look shrinked). Defaults to `None`.
        vplane_ylim (Tuple[float, float]): the y limits for the vertical plane plot (so that
            machine geometry doesn't make the plot look shrinked). Defaults to `None`.
        savefig (str): if not `None`, will save the figure to file using the string value passed.

    Returns:
            The `~matplotlib.figure.Figure` on which the plots are drawn. The underlying axes can be
            accessed with ``fig.get_axes()``.
    """
    # pylint: disable=too-many-arguments
    # We need to interpolate in order to get high resolution along the S direction
    logger.debug("Plotting estimated machine aperture and beam envelope")
    logger.debug("Running interpolation in MAD-X")
    madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="rbend", slice_=10, range_="#s/#e")
    madx.command.twiss()

    logger.trace("Getting Twiss dframe from MAD-X")
    twiss_hr: pd.DataFrame = madx.table.twiss.dframe().copy()
    twiss_hr["betatronic_envelope_x"] = np.sqrt(twiss_hr.betx * beam_params.eg_x_m)
    twiss_hr["betatronic_envelope_y"] = np.sqrt(twiss_hr.bety * beam_params.eg_y_m)
    twiss_hr["dispersive_envelope_x"] = twiss_hr.dx * beam_params.deltap_p
    twiss_hr["dispersive_envelope_y"] = twiss_hr.dy * beam_params.deltap_p
    twiss_hr["envelope_x"] = np.sqrt(twiss_hr.betatronic_envelope_x ** 2 + (twiss_hr.dx * beam_params.deltap_p) ** 2)
    twiss_hr["envelope_y"] = np.sqrt(twiss_hr.betatronic_envelope_y ** 2 + (twiss_hr.dy * beam_params.deltap_p) ** 2)
    machine = twiss_hr[twiss_hr.apertype == "ellipse"]

    figure = plt.figure(figsize=figsize)
    logger.debug("Plotting the horizontal aperture")
    axis1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
    axis1.plot(twiss_hr.s, twiss_hr.envelope_x, color="b")
    axis1.plot(twiss_hr.s, -twiss_hr.envelope_x, color="b")
    axis1.fill_between(twiss_hr.s, twiss_hr.envelope_x, -twiss_hr.envelope_x, color="b", alpha=0.25)
    axis1.fill_between(twiss_hr.s, 3 * twiss_hr.envelope_x, -3 * twiss_hr.envelope_x, color="b", alpha=0.25)
    axis1.fill_between(machine.s, machine.aper_1, machine.aper_1 * 100, color="k", alpha=0.5)
    axis1.fill_between(machine.s, -machine.aper_1, -machine.aper_1 * 100, color="k", alpha=0.5)
    axis1.plot(machine.s, machine.aper_1, "k.-")
    axis1.plot(machine.s, -machine.aper_1, "k.-")
    axis1.set_xlim(xlimits)
    axis1.set_ylim(hplane_ylim)
    axis1.set_ylabel(r"$X \ [m]$")
    axis1.set_xlabel(r"$S \ [m]$")
    axis1.set_title(f"Horizontal aperture at {beam_params.pc_GeV} GeV/c")

    logger.debug("Plotting the vertical aperture")
    axis2 = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=1, sharex=axis1)
    axis2.plot(twiss_hr.s, twiss_hr.envelope_y, color="r")
    axis2.plot(twiss_hr.s, -twiss_hr.envelope_y, color="r")
    axis2.fill_between(twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25)
    axis2.fill_between(twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25)
    axis2.fill_between(twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25)
    axis2.fill_between(twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25)
    axis2.fill_between(machine.s, machine.aper_2, machine.aper_2 * 100, color="k", alpha=0.5)
    axis2.fill_between(machine.s, -machine.aper_2, -machine.aper_2 * 100, color="k", alpha=0.5)
    axis2.plot(machine.s, machine.aper_2, "k.-")
    axis2.plot(machine.s, -machine.aper_2, "k.-")
    axis2.set_ylim(vplane_ylim)
    axis2.set_ylabel(r"$Y \ [m]$")
    axis2.set_xlabel(r"$S \ [m]$")
    axis2.set_title(f"Vertical aperture at {beam_params.pc_GeV} GeV/c")

    logger.debug("Plotting the stay-clear envelope")
    axis3 = plt.subplot2grid((3, 3), (2, 0), colspan=3, rowspan=1, sharex=axis1)
    axis3.plot(machine.s, machine.aper_1 / machine.envelope_x, ".-b", label="Horizontal plane")
    axis3.plot(machine.s, machine.aper_2 / machine.envelope_y, ".-r", label="Vertical plane")
    axis3.set_xlim(xlimits)
    axis3.set_ylabel("$n1$")
    axis3.set_xlabel(r"$S \ [m]$")
    axis3.legend(loc="best")
    axis3.set_title(f"Stay-clear envelope at {beam_params.pc_GeV} GeV/c")

    if savefig:
        logger.debug(f"Saving aperture plot at '{Path(savefig).absolute()}'")
        plt.savefig(Path(savefig))
    return figure
