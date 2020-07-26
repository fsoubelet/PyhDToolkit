"""
Module cpymadtools.plotters
---------------------------

Created on 2019.12.08
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to plot different output results from a cpymad.madx.Madx object's
simulation results.
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from loguru import logger
from matplotlib import colors as mcolors

from pyhdtoolkit.plotting.settings import PLOT_PARAMS

try:
    from cpymad.madx import Madx
except ModuleNotFoundError:
    Madx = None


plt.rcParams.update(PLOT_PARAMS)

COLORS_DICT = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
BY_HSV = sorted(
    (tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
    for name, color in COLORS_DICT.items()
)
SORTED_COLORS = [name for hsv, name in BY_HSV]


class AperturePlotter:
    """
    A class to plot the physical aperture of your machine.
    """

    @staticmethod
    def plot_aperture(
        cpymad_instance: Madx,
        beam_params: dict,
        figsize: tuple = (13, 20),
        xlimits: tuple = None,
        hplane_ylim: tuple = (-0.12, 0.12),
        vplane_ylim: tuple = (-0.12, 0.12),
        savefig: str = None,
    ) -> matplotlib.figure.Figure:
        """
        Plot the physical aperture of your machine, already defined into the provided
        cpymad.Madx object.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            beam_params: a beam_parameters dictionary obtained through
                         cpymadtools.helpers.beam_parameters.
            figsize: size of the figure, defaults to (15, 15).
            xlimits: will implement xlim (for the s coordinate) if this is not None, using the
                     tuple passed.
            hplane_ylim: the y limits for the horizontal plane plot (so that machine geometry
                         doesn't make the  plot look shrinked).
            vplane_ylim: the y limits for the vertical plane plot (so that machine geometry
                         doesn't make the plot look shrinked).
            savefig: will save the figure if this is not None, using the string value passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        # We need to interpolate in order to get high resolution along the s direction
        logger.debug("Running interpolation in cpymad")
        cpymad_instance.input(
            """
        select, flag=interpolate, class=drift, slice=4, range=#s/#e;
        select, flag=interpolate, class=quadrupole, slice=8, range=#s/#e;
        select, flag=interpolate, class=sbend, slice=10, range=#s/#e;
        select, flag=interpolate, class=rbend, slice=10, range=#s/#e;
        twiss;
        """
        )

        logger.debug("Getting Twiss dframe from cpymad")
        twiss_hr = cpymad_instance.table.twiss.dframe()
        twiss_hr["betatronic_envelope_x"] = np.sqrt(twiss_hr.betx * beam_params["eg_y_m"])
        twiss_hr["betatronic_envelope_y"] = np.sqrt(twiss_hr.bety * beam_params["eg_y_m"])
        twiss_hr["dispersive_envelope_x"] = twiss_hr.dx * beam_params["deltap_p"]
        twiss_hr["dispersive_envelope_y"] = twiss_hr.dy * beam_params["deltap_p"]
        twiss_hr["envelope_x"] = np.sqrt(
            twiss_hr.betatronic_envelope_x ** 2 + (twiss_hr.dx * beam_params["deltap_p"]) ** 2
        )
        twiss_hr["envelope_y"] = np.sqrt(
            twiss_hr.betatronic_envelope_y ** 2 + (twiss_hr.dy * beam_params["deltap_p"]) ** 2
        )
        machine = twiss_hr[twiss_hr.apertype == "ellipse"]

        figure = plt.figure(figsize=figsize)

        logger.debug("Plotting the horizontal aperture")
        axis1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
        axis1.plot(twiss_hr.s, twiss_hr.envelope_x, color="b")
        axis1.plot(twiss_hr.s, -twiss_hr.envelope_x, color="b")
        axis1.fill_between(
            twiss_hr.s, twiss_hr.envelope_x, -twiss_hr.envelope_x, color="b", alpha=0.25
        )
        axis1.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_x, -3 * twiss_hr.envelope_x, color="b", alpha=0.25
        )
        axis1.fill_between(machine.s, machine.aper_1, machine.aper_1 * 100, color="k", alpha=0.5)
        axis1.fill_between(machine.s, -machine.aper_1, -machine.aper_1 * 100, color="k", alpha=0.5)
        axis1.plot(machine.s, machine.aper_1, "k.-")
        axis1.plot(machine.s, -machine.aper_1, "k.-")
        axis1.set_xlim(xlimits)
        axis1.set_ylim(hplane_ylim)
        axis1.set_ylabel("x [m]")
        axis1.set_xlabel("s [m]")
        axis1.set_title(f"Horizontal aperture at {beam_params['pc_GeV']} GeV/c")

        logger.debug("Plotting the vertical aperture")
        axis2 = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=1, sharex=axis1)
        axis2.plot(twiss_hr.s, twiss_hr.envelope_y, color="r")
        axis2.plot(twiss_hr.s, -twiss_hr.envelope_y, color="r")
        axis2.fill_between(
            twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25
        )
        axis2.fill_between(
            twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25
        )
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
        axis2.set_ylabel("y [m]")
        axis2.set_xlabel("s [m]")
        axis2.set_title(f"Vertical aperture at {beam_params['pc_GeV']} GeV/c")

        logger.debug("Plotting the stay-clear envelope")
        axis3 = plt.subplot2grid((3, 3), (2, 0), colspan=3, rowspan=1, sharex=axis1)
        axis3.plot(machine.s, machine.aper_1 / machine.envelope_x, ".-b", label="Horizontal plane")
        axis3.plot(machine.s, machine.aper_2 / machine.envelope_y, ".-r", label="Vertical plane")
        axis3.set_xlim(xlimits)
        axis3.set_ylabel("n1")
        axis3.set_xlabel("s [m]")
        axis3.legend(loc="best")
        axis3.set_title(f"Stay-clear envelope at {beam_params['pc_GeV']} GeV/c")

        if savefig:
            logger.info(f"Saving aperture plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure


class DynamicAperturePlotter:
    """
    A class to plot the dynamic aperture of your machine.
    """

    @staticmethod
    def plot_dynamic_aperture(
        vx_coords: np.ndarray, vy_coords: np.ndarray, n_particles: int, savefig: str = None
    ) -> matplotlib.figure.Figure:
        """
        Plots a visual aid for the dynamic aperture after a tracking. Initial amplitudes are on the
        vertical axis, and the turn at which they were lost is in the horizontal axis.

        Args:
            vx_coords: array-like, horizontal coordinates over turns.
            vy_coords: array-like, vertical coordinates over turns.
            n_particles: number of particles simulated.
            savefig: will save the figure if this is not None, using the string value passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        figure = plt.figure(figsize=(12, 7))
        turn_lost = []
        x_in_lost = []

        for particle in range(n_particles):
            nb = len(vx_coords[particle]) - max(
                np.isnan(vx_coords[particle]).sum(), np.isnan(vy_coords[particle]).sum()
            )
            turn_lost.append(nb)
            x_in_lost.append(vx_coords[particle][0] ** 2 + vy_coords[particle][0] ** 2)
        turn_lost = np.array(turn_lost)
        x_in_lost = np.array(x_in_lost)

        plt.scatter(turn_lost, x_in_lost * 1000, linewidths=0.7, c="darkblue", marker=".")
        plt.title("Amplitudes lost over turns", fontsize=20)
        plt.xlabel("Number of Turns Survived", fontsize=17)
        plt.ylabel("Initial amplitude [mm]", fontsize=17)

        if savefig:
            logger.info(f"Saving dynamic aperture plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure


class PhaseSpacePlotter:
    """
    A class to plot normalized phase space.
    """

    @staticmethod
    def plot_normalized_phase_space(
        cpymad_instance: Madx,
        u_coordinates: np.ndarray,
        pu_coordinates: np.ndarray,
        savefig: str = None,
        size: tuple = (16, 8),
        plane: str = "Horizontal",
    ) -> matplotlib.figure.Figure:
        """
        Plots the normalized phase space of a particle distribution when provided by position and
        momentum coordinates for a specific plane.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            u_coordinates: coordinates of particles.
            pu_coordinates: momentum coordinates of particles.
            savefig: will save the figure if this is not None, using the string value passed.
            size: tuple with the wanted matplotlib figure size.
            plane: string with the physical plane to plot.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        figure = plt.figure(figsize=size)
        plt.title("Normalized Phase Space", fontsize=20)

        # Getting the P matrix to compute normalized coordinates
        logger.debug("Getting Twiss functions from cpymad")
        alpha = (
            cpymad_instance.table.twiss.alfx[0]
            if plane == "Horizontal"
            else cpymad_instance.table.twiss.alfy[0]
        )
        beta = (
            cpymad_instance.table.twiss.betx[0]
            if plane == "Horizontal"
            else cpymad_instance.table.twiss.bety[0]
        )

        logger.debug("Computing P-matrix to get normalized coordinates")
        p_matrix = np.array([[np.sqrt(beta), 0], [-alpha / np.sqrt(beta), 1 / np.sqrt(beta)]])
        p_matrix_inv = np.linalg.inv(p_matrix)

        logger.debug(f"Plotting normalised phase space for {plane.lower()}")
        for index, u_particle in enumerate(u_coordinates):
            u = np.array([u_coordinates[index], pu_coordinates[index]])
            u_bar = p_matrix_inv @ u
            plt.scatter(u_bar[0, :] * 1e3, u_bar[1, :] * 1e3, s=0.1, c="k")
            if plane == "Horizontal":
                plt.xlabel("$\\bar{x}  [mm]$", fontsize=17)
                plt.ylabel("$\\bar{px} [mrad]$", fontsize=17)
                plt.axis("Equal")
            elif plane == "Vertical":
                plt.xlabel("$\\bar{y}  [mm]$", fontsize=17)
                plt.ylabel("$\\bar{py} [mrad]$", fontsize=17)
                plt.axis("Equal")
            else:
                raise ValueError("Plane should be either Horizontal or Vertical")

        if savefig:
            logger.info(f"Saving normalized phase space plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure

    @staticmethod
    def plot_normalized_phase_space_colored(
        cpymad_instance: Madx,
        u_coordinates: np.ndarray,
        pu_coordinates: np.ndarray,
        savefig: str = None,
        size: tuple = (16, 8),
        plane: str = "Horizontal",
    ) -> matplotlib.figure.Figure:
        """
        Plots the normalized phase space of a particle distribution when provided by position and
        momentum coordinates for a specific plane. Each particle trajectory has its own color on
        the plot, within the limit of pyplot's 156 named colors. The sequence repeats after the
        156th color.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            u_coordinates: coordinates of particles.
            pu_coordinates: momentum coordinates of particles.
            savefig: will save the figure if this is not None, using the string value passed.
            size: tuple with the wanted matplotlib figure size.
            plane: string with the physical plane to plot.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        # pylint: disable=too-many-locals
        # Getting a sufficiently long array of colors to use
        colors = int(np.floor(len(u_coordinates) / 100)) * SORTED_COLORS
        while len(colors) > len(u_coordinates):
            colors.pop()

        figure = plt.figure(figsize=size)
        plt.title("Normalized Phase Space", fontsize=20)

        logger.debug("Getting Twiss functions from cpymad")
        alpha = (
            cpymad_instance.table.twiss.alfx[0]
            if plane == "Horizontal"
            else cpymad_instance.table.twiss.alfy[0]
        )
        beta = (
            cpymad_instance.table.twiss.betx[0]
            if plane == "Horizontal"
            else cpymad_instance.table.twiss.bety[0]
        )

        logger.debug("Computing P-matrix to get normalized coordinates")
        p_matrix = np.array([[np.sqrt(beta), 0], [-alpha / np.sqrt(beta), 1 / np.sqrt(beta)]])
        p_matrix_inv = np.linalg.inv(p_matrix)

        logger.debug(f"Plotting colored normalised phase space for {plane.lower()}")
        for index, u_particle in enumerate(u_coordinates):
            u = np.array([u_coordinates[index], pu_coordinates[index]])
            u_bar = p_matrix_inv @ u
            plt.scatter(u_bar[0, :] * 1e3, u_bar[1, :] * 1e3, s=0.1, c=colors[index])
            if plane == "Horizontal":
                plt.xlabel("$\\bar{x}  [mm]$", fontsize=17)
                plt.ylabel("$\\bar{px} [mrad]$", fontsize=17)
                plt.axis("Equal")
            elif plane == "Vertical":
                plt.xlabel("$\\bar{y}  [mm]$", fontsize=17)
                plt.ylabel("$\\bar{py} [mrad]$", fontsize=17)
                plt.axis("Equal")
            else:
                raise ValueError("Plane should be either Horizontal or Vertical")

        if savefig:
            logger.info(f"Saving colored normalized phase space plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure


class TuneDiagramPlotter:
    """
    A class to plot a blank tune diagram with Farey sequences, as well as your working points.
    """

    @staticmethod
    def farey_sequence(order: int) -> list:
        """
        Returns the n-th farey_sequence sequence, ascending. Original code from Rogelio Tomás.

        Args:
            order: the order up to which we want to calculate the sequence.

        Returns:
            The sequence as a list.
        """
        seq = [[0, 1]]
        a, b, c, d = 0, 1, 1, order
        while c <= order:
            k = int((order + b) / d)
            a, b, c, d = c, d, k * c - a, k * d - b
            seq.append([a, b])
        return seq

    @staticmethod
    def plot_blank_tune_diagram() -> matplotlib.figure.Figure:
        """
        Plotting the tune diagram up to the 6th order. Original code from Rogelio Tomás.

        Returns:
            Nothing, just plots.
        """
        logger.debug("Plotting resonance lines from Farey sequence")

        figure = plt.figure(figsize=(13, 13))
        plt.ylim((0, 1))
        plt.xlim((0, 1))

        x = np.linspace(0, 1, 1000)
        for i in range(1, 6):
            farey_sequences = TuneDiagramPlotter.farey_sequence(i)
            for f in farey_sequences:
                h, k = f  # Node h/k on the axes
                for sequence in farey_sequences:
                    p, q = sequence
                    a = float(k * p)  # Resonance linea Qx + b*Qy = clinkedtop / q
                    if a > 0:
                        b = float(q - k * p)
                        c = float(p * h)
                        plt.plot(x, c / a - x * b / a, "b", alpha=0.1)
                        plt.plot(x, c / a + x * b / a, "b", alpha=0.1)
                        plt.plot(c / a - x * b / a, x, "b", alpha=0.1)
                        plt.plot(c / a + x * b / a, x, "b", alpha=0.1)
                        plt.plot(c / a - x * b / a, 1 - x, "b", alpha=0.1)
                        plt.plot(c / a + x * b / a, 1 - x, "b", alpha=0.1)
                    if q == k and p == 1:  # FN elements below 1/k
                        break
        plt.title("Tune Diagram", fontsize=20)
        plt.axis("square")
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.xlabel("$Q_{x}}$", fontsize=17)
        plt.ylabel("$Q_{y}$", fontsize=17)
        return figure

    @staticmethod
    def plot_tune_diagram(
        cpymad_instance: Madx,
        v_qx: np.array = np.array([0]),
        vxgood: np.array = np.array([False]),
        v_qy: np.array = np.array([0]),
        vygood: np.array = np.array([False]),
        savefig: str = None,
    ) -> matplotlib.figure.Figure:
        """
        Plots the evolution of particles' tunes on a Tune Diagram.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            v_qx: values of the horizontal tune Qx. Can be only one value.
            vxgood: ??
            v_qy: values of the vertical tune Qy. Can be only one value.
            vygood: ??
            savefig: will save the figure if this is not None, using the string value passed.

        Returns:
            Nothing, plots the figure.
        """
        figure = TuneDiagramPlotter.plot_blank_tune_diagram()

        logger.debug("Getting Tunes from cpymad")
        new_q1 = cpymad_instance.table.summ.dframe().q1[0]
        new_q2 = cpymad_instance.table.summ.dframe().q2[0]

        if vxgood.any() and vygood.any():
            plt.plot(v_qx[vxgood * vygood], v_qy[vxgood * vygood], ".r")
            plt.plot(new_q1 - np.floor(new_q1), new_q2 - np.floor(new_q2), ".g")

        elif vxgood.any() and ~vygood.any():
            tp = np.ones(len(vxgood)) * (new_q2 - np.floor(new_q2))
            plt.plot(v_qx[vxgood], tp[vxgood], ".r")
            plt.plot(new_q1 - np.floor(new_q1), new_q2 - np.floor(new_q2), ".g")

        elif ~vxgood.any() and vygood.any():
            tp = np.ones(len(vygood)) * (new_q1 - np.floor(new_q1))
            plt.plot(tp[vygood], v_qy[vygood], ".r")
            plt.plot(new_q1 - np.floor(new_q1), new_q2 - np.floor(new_q2), ".g")

        if savefig:
            logger.info(f"Saving Tune diagram plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure
