"""
Module cpymadtools.plotters
---------------------------

Created on 2019.12.08
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to plot different output results from a cpymad.madx.Madx object's
simulation results.
"""
from functools import partial
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cpymad.madx import Madx
from loguru import logger
from matplotlib import colors as mcolors

from pyhdtoolkit.models.beam import BeamParameters
from pyhdtoolkit.optics.twiss import courant_snyder_transform
from pyhdtoolkit.utils.defaults import PLOT_PARAMS

plt.rcParams.update(PLOT_PARAMS)

COLORS_DICT = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
BY_HSV = sorted(
    (tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name) for name, color in COLORS_DICT.items()
)
SORTED_COLORS = [name for hsv, name in BY_HSV]


class BeamEnvelopePlotter:
    """
    A class to plot the physical aperture of your machine.
    """

    @staticmethod
    def plot_envelope(
        madx: Madx,
        beam_params: BeamParameters,
        figsize: Tuple[int, int] = (13, 20),
        xlimits: Tuple[float, float] = None,
        hplane_ylim: Tuple[float, float] = (-0.12, 0.12),
        vplane_ylim: Tuple[float, float] = (-0.12, 0.12),
        savefig: str = None,
    ) -> matplotlib.figure.Figure:
        """
        Provided with an active `cpymad` instance after having ran a script, plots an estimation of the beam
        stay-clear enveloppe in your machine, as well as an estimation of the aperture limits.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            beam_params (BeamParameters): a validated BeamParameters object from
                `pyhdtoolkit.optics.beam.compute_beam_parameters`.
            figsize (Tuple[int, int]): size of the figure, defaults to (13, 20).
            xlimits (Tuple[float, float]): will implement xlim (for the s coordinate) if this is
                not None, using the tuple passed.
            hplane_ylim (Tuple[float, float]): the y limits for the horizontal plane plot (so
                that machine geometry doesn't make the  plot look shrinked). Defaults to (-0.12, 0.12).
            vplane_ylim (Tuple[float, float]): the y limits for the vertical plane plot (so that
                machine geometry doesn't make the plot look shrinked). Defaults to (-0.12, 0.12).
            savefig (str): will save the figure if this is not None, using the string value passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        # pylint: disable=too-many-arguments
        # We need to interpolate in order to get high resolution along the S direction
        logger.info("Plotting estimated machine aperture and beam envelope")
        logger.debug("Running interpolation in MAD-X")
        madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
        madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
        madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
        madx.command.select(flag="interpolate", class_="rbend", slice_=10, range_="#s/#e")
        madx.command.twiss()

        logger.trace("Getting Twiss dframe from MAD-X")
        twiss_hr: pd.DataFrame = madx.table.twiss.dframe().copy()
        twiss_hr["betatronic_envelope_x"] = np.sqrt(twiss_hr.betx * beam_params.eg_y_m)
        twiss_hr["betatronic_envelope_y"] = np.sqrt(twiss_hr.bety * beam_params.eg_y_m)
        twiss_hr["dispersive_envelope_x"] = twiss_hr.dx * beam_params.deltap_p
        twiss_hr["dispersive_envelope_y"] = twiss_hr.dy * beam_params.deltap_p
        twiss_hr["envelope_x"] = np.sqrt(
            twiss_hr.betatronic_envelope_x ** 2 + (twiss_hr.dx * beam_params.deltap_p) ** 2
        )
        twiss_hr["envelope_y"] = np.sqrt(
            twiss_hr.betatronic_envelope_y ** 2 + (twiss_hr.dy * beam_params.deltap_p) ** 2
        )
        machine = twiss_hr[twiss_hr.apertype == "ellipse"]

        figure = plt.figure(figsize=figsize)
        logger.debug("Plotting the horizontal aperture")
        axis1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
        axis1.plot(twiss_hr.s, twiss_hr.envelope_x, color="b")
        axis1.plot(twiss_hr.s, -twiss_hr.envelope_x, color="b")
        axis1.fill_between(twiss_hr.s, twiss_hr.envelope_x, -twiss_hr.envelope_x, color="b", alpha=0.25)
        axis1.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_x, -3 * twiss_hr.envelope_x, color="b", alpha=0.25
        )
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
        axis2.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25
        )
        axis2.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25
        )
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
            logger.info(f"Saving aperture plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure


class DynamicAperturePlotter:
    """
    A class to plot the dynamic aperture of your machine.
    """

    @staticmethod
    def plot_dynamic_aperture(
        x_coords: np.ndarray, y_coords: np.ndarray, n_particles: int, savefig: str = None
    ) -> matplotlib.figure.Figure:
        """
        Plots a visual aid for the dynamic aperture after a tracking. Initial amplitudes are on the
        vertical axis, and the turn at which they were lost is in the horizontal axis.

        Args:
            x_coords (np.ndarray): numpy array of horizontal coordinates over turns.
            y_coords (np.ndarray): numpy array of vertical coordinates over turns.
            n_particles (int): number of particles simulated.
            savefig (str): will save the figure if this is not None, using the string value passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        logger.info(f"Plotting the '{len(x_coords)} turns' aperture")
        figure = plt.figure(figsize=(12, 7))
        turn_lost_at = []
        amp_lost = []

        logger.trace("Determining turns at which particles have been lost")
        for particle in range(n_particles):
            amp_lost.append(x_coords[particle][0] ** 2 + y_coords[particle][0] ** 2)  # initial amplitude
            # this is ok since once coordinates go to `nan` they don't come back, particle is lost
            turn_lost_at.append(
                min(
                    pd.Series(x_coords[particle]).last_valid_index()
                    + 2,  # starts at 0, lost after last valid
                    pd.Series(y_coords[particle]).last_valid_index()
                    + 2,  # starts at 0, lost after last valid
                )
            )
        turn_lost_at = np.array(turn_lost_at)
        amp_lost = np.array(amp_lost)

        plt.scatter(turn_lost_at, amp_lost * 1000, linewidths=0.7, c="darkblue", marker=".")
        plt.title("Amplitudes lost over turns")
        plt.xlabel("Number of Turns Survived")
        plt.ylabel("Initial amplitude $[mm]$")

        if savefig:
            logger.info(f"Saving dynamic aperture plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure


class PhaseSpacePlotter:
    """
    A class to plot Courant-Snyder coordinates phase space.
    """

    @staticmethod
    def plot_courant_snyder_phase_space(
        madx: Madx,
        u_coordinates: np.ndarray,
        pu_coordinates: np.ndarray,
        savefig: str = None,
        size: Tuple[int, int] = (16, 8),
        plane: str = "Horizontal",
    ) -> matplotlib.figure.Figure:
        """
        Plots the Courant-Snyder phase space of a particle distribution when provided by position
        and momentum coordinates for a specific plane.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            u_coordinates (np.ndarray): numpy array of particles' coordinates for the given plane. Here
                u_coordinates[0] should be all tracked coordinates for the first particle and so on.
            pu_coordinates (np.ndarray): numpy array of particles' momentum coordinates for the
                given plane.Here pu_coordinates[0] should be all tracked momenta for the first particle
                and so on.
            savefig (str): will save the figure if this is not None, using the string value passed.
            size (Tuple[int, int]): the wanted matplotlib figure size. Defaults to (16, 8).
            plane (str): the physical plane to plot. Defaults to 'Horizontal'.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        if plane.upper() not in ("HORIZONTAL", "VERTICAL"):
            logger.error(f"Plane should be either Horizontal or Vertical but '{plane}' was given")
            raise ValueError("Invalid plane value")

        logger.info("Plotting phase space for normalized Courant-Snyder coordinates")
        figure = plt.figure(figsize=size)
        plt.title("Courant-Snyder Phase Space")

        # Getting the twiss parameters for the P matrix to compute Courant-Snyder coordinates
        logger.debug("Getting Twiss functions from MAD-X")
        alpha = madx.table.twiss.alfx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.alfy[0]
        beta = madx.table.twiss.betx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.bety[0]

        logger.debug(f"Plotting phase space for the {plane.lower()} plane")
        for index, _ in enumerate(u_coordinates):
            logger.trace(f"Getting and plotting Courant-Snyder coordinates for particle {index}")
            u = np.array([u_coordinates[index], pu_coordinates[index]])
            u_bar = courant_snyder_transform(u, alpha, beta)
            plt.scatter(u_bar[0, :] * 1e3, u_bar[1, :] * 1e3, s=0.1, c="k")
            if plane.upper() == "HORIZONTAL":
                plt.xlabel(r"$\bar{x} \ [mm]$")
                plt.ylabel(r"$\bar{px} \ [mrad]$")
            else:
                plt.xlabel(r"$\bar{y} \ [mm]$")
                plt.ylabel(r"$\bar{py} \ [mrad]$")
            plt.axis("Equal")

        if savefig:
            logger.info(f"Saving Courant-Snyder phase space plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure

    @staticmethod
    def plot_courant_snyder_phase_space_colored(
        madx: Madx,
        u_coordinates: np.ndarray,
        pu_coordinates: np.ndarray,
        savefig: str = None,
        size: Tuple[int, int] = (16, 8),
        plane: str = "Horizontal",
    ) -> matplotlib.figure.Figure:
        """
        Plots the Courant-Snyder phase space of a particle distribution when provided by position
        and momentum coordinates for a specific plane. Each particle trajectory has its own color on
        the plot, within the limit of pyplot's 156 named colors. The sequence repeats after the
        156th color.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            u_coordinates (np.ndarray): numpy array of particles' coordinates for the given plane. Here
                u_coordinates[0] should be all tracked coordinates for the first particle and so on.
            pu_coordinates (np.ndarray): numpy array of particles' momentum coordinates for the
                given plane.Here pu_coordinates[0] should be all tracked momenta for the first particle
                and so on.
            savefig (str): will save the figure if this is not None, using the string value passed.
            size (Tuple[int, int]): the wanted matplotlib figure size. Defaults to (16, 8).
            plane (str): the physical plane to plot. Defaults to 'Horizontal'.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        if plane.upper() not in ("HORIZONTAL", "VERTICAL"):
            logger.error(f"Plane should be either horizontal or vertical but '{plane}' was given")
            raise ValueError("Invalid plane value")

        # Getting a sufficiently long array of colors to use
        colors = int(np.floor(len(u_coordinates) / 100)) * SORTED_COLORS
        while len(colors) > len(u_coordinates):
            colors.pop()

        logger.info("Plotting colored phase space for normalized Courant-Snyder coordinates")
        figure = plt.figure(figsize=size)
        plt.title("Courant-Snyder Phase Space")

        # Getting the twiss parameters for the P matrix to compute Courant-Snyder coordinates
        logger.debug("Getting Twiss functions from MAD-X")
        alpha = madx.table.twiss.alfx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.alfy[0]
        beta = madx.table.twiss.betx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.bety[0]

        logger.debug(f"Plotting colored phase space for the {plane.lower()} plane")
        for index, _ in enumerate(u_coordinates):
            logger.trace(f"Getting and plotting Courant-Snyder coordinates for particle {index}")
            u = np.array([u_coordinates[index], pu_coordinates[index]])
            u_bar = courant_snyder_transform(u, alpha, beta)
            plt.scatter(u_bar[0, :] * 1e3, u_bar[1, :] * 1e3, s=0.1, c=colors[index])
            if plane.upper() == "HORIZONTAL":
                plt.xlabel(r"$\bar{x} \ [mm]$")
                plt.ylabel(r"$\bar{px} \ [mrad]$")
            else:
                plt.xlabel(r"$\bar{y} \ [mm]$")
                plt.ylabel(r"$\bar{py} \ [mrad]$")
            plt.axis("Equal")

        if savefig:
            logger.info(f"Saving colored Courant-Snyder phase space plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure


class TuneDiagramPlotter:
    """
    A class to plot a blank tune diagram with Farey sequences, as well as your working points.
    """

    order_to_alpha: Dict[int, float] = {1: 1, 2: 0.75, 3: 0.65, 4: 0.55, 5: 0.45, 6: 0.35}
    order_to_rgb: Dict[int, np.ndarray] = {
        1: np.array([152, 52, 48]) / 255,  # a brown
        2: np.array([57, 119, 175]) / 255,  # a blue
        3: np.array([239, 133, 54]) / 255,  # an orange
        4: np.array([82, 157, 62]) / 255,  # a green
        5: np.array([197, 57, 50]) / 255,  # a red
        6: np.array([141, 107, 184]) / 255,  # a purple
    }
    order_to_linestyle: Dict[int, str] = {
        1: "solid",
        2: "solid",
        3: "solid",
        4: "dashed",
        5: "dashed",
        6: "dashed",
    }
    order_to_linewidth: Dict[int, float] = {1: 2, 2: 1.75, 3: 1.5, 4: 1.25, 5: 1, 6: 0.75}
    order_to_label: Dict[int, str] = {
        1: "1st order",
        2: "2nd order",
        3: "3rd order",
        4: "4th order",
        5: "5th order",
        6: "6th order",
    }

    @staticmethod
    def farey_sequence(order: int) -> List[Tuple[int, int]]:
        """
        Returns the n-th farey_sequence sequence, ascending. Original code from Rogelio Tomás (see Numerical
        Methods 2018 CAS proceedings: https://arxiv.org/abs/2006.10661).

        Args:
            order (int): the order up to which we want to calculate the sequence.

        Returns:
            The sequence as a list of plottable 2D points.
        """
        logger.trace(f"Computing Farey sequence for order {order}")
        seq = [[0, 1]]
        a, b, c, d = 0, 1, 1, order
        while c <= order:
            k = int((order + b) / d)
            a, b, c, d = c, d, k * c - a, k * d - b
            seq.append((a, b))
        return seq

    @staticmethod
    def _plot_resonance_lines_for_order(order: int, axis: matplotlib.axes.Axes, **kwargs) -> None:
        """
        Plot resonance lines from farey sequences of the given order on the current figure.

        Args:
            order (int): the order of the resonance.
            axis (matplotlib.axes.Axes): the axis on which to plot the resonance lines.

        Keyword Args:
            Any keyword argument is given to plt.plot().
        """
        order_label = TuneDiagramPlotter.order_to_label[order]
        logger.debug(f"Plotting {order_label} resonance lines")
        axis.plot([], [], label=order_label, **kwargs)  # to avoid legend duplication in loops below

        x, y = np.linspace(0, 1, 1000), np.linspace(0, 1, 1000)
        farey_sequences = TuneDiagramPlotter.farey_sequence(order)
        clip = partial(np.clip, a_min=0, a_max=1)  # clip all values to plot to [0, 1]

        for node in farey_sequences:
            h, k = node  # Node h/k on the axes
            for sequence in farey_sequences:
                p, q = sequence
                a = float(k * p)  # Resonance line a*Qx + b*Qy = c (linked to p/q)
                if a > 0:
                    b, c = float(q - k * p), float(p * h)
                    axis.plot(x, clip(c / a - x * b / a), **kwargs)
                    axis.plot(x, clip(c / a + x * b / a), **kwargs)
                    axis.plot(clip(c / a - x * b / a), y, **kwargs)
                    axis.plot(clip(c / a + x * b / a), y, **kwargs)
                    axis.plot(clip(c / a - x * b / a), 1 - y, **kwargs)
                    axis.plot(clip(c / a + x * b / a), 1 - y, **kwargs)
                if q == k and p == 1:  # FN elements below 1/k
                    break

    @staticmethod
    def plot_blank_tune_diagram(
        title: str = "",
        legend_title: str = None,
        max_order: int = 6,
        differentiate_orders: bool = False,
        figsize: Tuple[float, float] = (12, 12),
        **kwargs,
    ) -> matplotlib.figure.Figure:
        """
        Plotting the tune diagram up to the 6th order. Original code from Rogelio Tomás.
        The first order lines make up the [(0, 0), (0, 1), (1, 1), (1, 0)] square and will only be seen
        when redefining the limits of the figure, which are by default [0, 1] on each axis.

        Args:
            title (str): title of your plot, to be given to the figure. Defaults to an empty string.
            legend_title (str): if given, will be used as the title of the plot's legend. If set to `None`,
                then creating a legend for the figure will not be done by this function and left up to the
                user's care (a call to `pyplot.legend` will do). Defaults to `None`.
            max_order (int): the order up to which to plot resonance lines for, should not exceed 6.
                Defaults to 6.
            differentiate_orders (bool): if `True`, the lines for each order will be of a different color.
                When set to False, there is still minimal differentation through alpha, linewidth and
                linestyle. Defaults to `False`.
            figsize (Tuple[int, int]): size of the figure, defaults to (12, 12).

        Keyword Args:
            Any keyword argument will be transmitted to the `_plot_resonance_lines_for_order` functino
            and later on to `pyplot.plot`. Be aware that `alpha`, `ls`, `lw`, `color` and `label` are
            already set by this function and providing them as kwargs might lead to errors.

        Returns:
             The figure on which resonance lines from farey sequences are drawn, up to the specified max
             order.
        """
        if max_order > 6 or max_order < 1:
            logger.error("Plotting is not supported outside of 1st-6th order (and not recommended)")
            raise ValueError("The 'max_order' argument should be between 1 and 6 included")

        logger.info(f"Plotting resonance lines up to {TuneDiagramPlotter.order_to_label[max_order]}")
        figure, axis = plt.subplots(figsize=figsize)

        for order in range(max_order, 0, -1):  # high -> low so most importants ones (low) are plotted on top
            alpha, ls, lw, rgb = (
                TuneDiagramPlotter.order_to_alpha[order],
                TuneDiagramPlotter.order_to_linestyle[order],
                TuneDiagramPlotter.order_to_linewidth[order],
                TuneDiagramPlotter.order_to_rgb[order] if differentiate_orders is True else "blue",
            )
            TuneDiagramPlotter._plot_resonance_lines_for_order(
                order, axis, alpha=alpha, ls=ls, lw=lw, color=rgb, **kwargs,
            )

        plt.title(title)
        axis.set_xlim([0, 1])
        axis.set_ylim([0, 1])
        plt.xlabel("$Q_{x}$")
        plt.ylabel("$Q_{y}$")

        if legend_title is not None:
            logger.debug("Adding legend with given title")
            plt.legend(title=legend_title)
        return figure
