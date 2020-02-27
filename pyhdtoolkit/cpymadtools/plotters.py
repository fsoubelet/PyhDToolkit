"""
Created on 2019.12.08
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to plot different output results from a cpymad.MadX object's simulation results.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors

COLORS_DICT = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
BY_HSV = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name) for name, color in COLORS_DICT.items())
SORTED_COLORS = [name for hsv, name in BY_HSV]


class DynamicAperturePlotter:
    """
    A class to plot the dynamic aperture of your machine.
    """

    @staticmethod
    def plot_dynamic_aperture(vx_coords, vy_coords, n_particles) -> None:
        """
        Plots a visual aid for the dynamic aperture after a tracking. Initial amplitudes are on the Y axis,
        and the turn at which they were lost is in the X axis.
        :param vx_coords: horizontal coordinates over turns.
        :param vy_coords: vertical coordinates over turns.
        :param n_particles: number of particles simulated.
        :return: nothing, plots the figure.
        """
        plt.figure(figsize=(12, 7))
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


class PhaseSpacePlotter:
    """
    A class to plot normalized phase space.
    """

    @staticmethod
    def plot_normalized_phase_space(cpymad_instance, u_coordinates, pu_coordinates, **kwargs) -> None:
        """
        Plots the normalized phase space of a particle distribution when provided by position and momentum coordinates
        for a specific plane.
        :param cpymad_instance: an instanciated `cpymad.madx.Madx` object.
        :param u_coordinates: coordinates of particles.
        :param pu_coordinates: momentum coordinates of particles.
        :param kwargs: The looked for keywords are `size`, `plane`, and `savefig`. They give the possibility of
        specifying the size of the plotted figure, the provided physical plane (horizontal / vertical) and wether or
        not to save the figure to file.
        :return: nothing, plots the figure.
        """
        size = kwargs.get("size", None)
        plane = kwargs.get("plane", "Horizontal")
        savefig = kwargs.get("savefig", False)

        plt.figure(figsize=size) if size else plt.figure(figsize=(16, 8))
        plt.title("Normalized Phase Space", fontsize=20)

        # Getting the P matrix to compute normalized coordinates
        alpha = cpymad_instance.table.twiss.alfx[0] if plane == "Horizontal" else cpymad_instance.table.twiss.alfy[0]
        beta = cpymad_instance.table.twiss.betx[0] if plane == "Horizontal" else cpymad_instance.table.twiss.bety[0]
        p_matrix = np.array([[np.sqrt(beta), 0], [-alpha / np.sqrt(beta), 1 / np.sqrt(beta)]])
        p_matrix_inv = np.linalg.inv(p_matrix)

        # Plotting phase space
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
            plt.savefig("normalized_phase_space", format="png", dpi=300)

    @staticmethod
    def plot_normalized_phase_space_colored(cpymad_instance, u_coordinates, pu_coordinates, **kwargs) -> None:
        """
        Plots the normalized phase space of a particle distribution when provided by position and momentum coordinates
        for a specific plane. Each particle trajectory has its own color on the plot, within the limit of pyplot's 156
        named colors. The sequence repeats after the 156th color.
        :param cpymad_instance: an instanciated `cpymad.madx.Madx` object.
        :param u_coordinates: coordinates of particles.
        :param pu_coordinates: momentum coordinates of particles.
        :param kwargs: The looked for keywords are `size`, `plane`, and `savefig`. They give the possibility of
        specifying the size of the plotted figure, the provided physical plane (horizontal / vertical) and wether or
        not to save the figure to file.
        :return: nothing, plots the figure.
        """
        # pylint: disable=too-many-locals
        size = kwargs.get("size", None)
        plane = kwargs.get("plane", "Horizontal")
        savefig = kwargs.get("savefig", False)

        # Getting a sufficiently long array of colors to use
        colors = int(np.floor(len(u_coordinates) / 100)) * SORTED_COLORS
        while len(colors) > len(u_coordinates):
            colors.pop()

        plt.figure(figsize=size) if size else plt.figure(figsize=(16, 8))
        plt.title("Normalized Phase Space", fontsize=20)

        # Getting the P matrix to compute normalized coordinates
        alpha = cpymad_instance.table.twiss.alfx[0] if plane == "Horizontal" else cpymad_instance.table.twiss.alfy[0]
        beta = cpymad_instance.table.twiss.betx[0] if plane == "Horizontal" else cpymad_instance.table.twiss.bety[0]
        p_matrix = np.array([[np.sqrt(beta), 0], [-alpha / np.sqrt(beta), 1 / np.sqrt(beta)]])
        p_matrix_inv = np.linalg.inv(p_matrix)

        # Plotting
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
            plt.savefig("normalized_phase_space_colored", format="png", dpi=300)


class TuneDiagramPlotter:
    """
    A class to plot a blank tune diagram with Farey sequences, as well as your working points.
    """

    @staticmethod
    def farey_sequence(order: int) -> list:
        """
        Return the n-th farey_sequence sequence, ascending. Original code from Rogelio Tomás.
        :param order: the order up to which we want to calculate the sequence.
        :return: the sequence as a list.
        """
        seq = [[0, 1]]
        a, b, c, d = 0, 1, 1, order
        while c <= order:
            k = int((order + b) / d)
            a, b, c, d = c, d, k * c - a, k * d - b
            seq.append([a, b])
        return seq

    @staticmethod
    def plot_blank_tune_diagram() -> None:
        """
        Plotting the tune diagram up to the 6th order. Original code from Rogelio Tomás.
        :return: nothing.
        """
        plt.figure(figsize=(13, 13))
        plt.ylim((0, 1))
        plt.xlim((0, 1))
        x = np.linspace(0, 1, 1000)
        for i in range(1, 6):
            farey_sequences = TuneDiagramPlotter.farey_sequence(i)
            for f in farey_sequences:
                h, k = f  # Node h/k on the axes
                for sequence in farey_sequences:
                    p, q = sequence
                    c = float(p * h)
                    a = float(k * p)  # Resonance linea Qx + b*Qy = clinkedtop / q
                    b = float(q - k * p)
                    if a > 0:
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

    @staticmethod
    def plot_tune_diagram(
        cpymad_instance,
        v_qx: np.array = np.array([0]),
        vxgood: np.array = np.array([False]),
        v_qy: np.array = np.array([0]),
        vygood: np.array = np.array([False]),
    ) -> None:
        """
        Plots the evolution of particles' tunes on a Tune Diagram.
        :param cpymad_instance: an instanciated `cpymad.madx.Madx` object.
        :param v_qx: values of the horizontal tune Qx. Can be only one value.
        :param vxgood:
        :param v_qy: values of the vertical tune Qy. Can be only one value.
        :param vygood:
        :return: nothing, plots the figure.
        """
        TuneDiagramPlotter.plot_blank_tune_diagram()
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


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
