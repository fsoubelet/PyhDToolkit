"""
Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to elegantly plot the Twiss parameters output of a cpymad.MadX instance after it has ran.
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt


class LaTwiss:
    """
    A class to manage plotting the machine survey as well as an elegant plot for elements + Twiss parameters.
    """

    @staticmethod
    def _plot_lattice_series(
        ax: plt.axes,
        series,
        height: float = 1.0,
        v_offset: float = 0.0,
        color: str = "r",
        alpha: float = 0.5,
        lw: int = 3,
    ) -> None:
        """
        Will plot the layout of your machine as a patch of rectangles for different element types. Original code from
        Guido Sterbini.
        :param ax: an existing  matplotlib.axis `Axes` object to act on.
        :param series: ??
        :param height: ??
        :param v_offset: ??
        :param color:
        :param alpha:
        :param lw:
        :return: nothing, acts directly on the provided axis.
        """
        # pylint: disable=too-many-arguments
        ax.add_patch(
            patches.Rectangle(
                (series.s - series.l, v_offset - height / 2.0),
                series.l,  # width
                height,  # height
                color=color,
                alpha=alpha,
                lw=lw,
            )
        )

    @staticmethod
    def plot_latwiss(cpymad_instance, title: str, fig_size: tuple, ncells: int, **kwargs) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will create a plot representing nicely the
        lattice layout and the beta functions along with the horizontal dispertion function. Original code is from
        Guido Sterbini.
        :param cpymad_instance: an instanciated `cpymad.madx.Madx` object.
        :param title: title of your plot.
        :param fig_size: figure size.
        :param ncells: number of cells of your lattice.
        :return: nothing, plots and eventually saves the figure as a file.
        """
        # pylint: disable=too-many-locals
        # Getting kwargs and instantiating
        x_limits = kwargs.get("xlim", None)
        savefig = kwargs.get("savefig", False)
        twiss_dataframe = cpymad_instance.table.twiss.dframe()
        plt.figure(figsize=fig_size)

        # Create a subplot for the lattice patches
        ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
        plt.plot(twiss_dataframe.s, 0 * twiss_dataframe.s, "k")

        # Plotting the quadrupoles
        ax1.set_ylabel("1/f=K1L [m$^{-1}$]", color="red", fontsize=15)
        ax1.tick_params(axis="y", labelcolor="red")
        plt.ylim(-0.08, 0.08)
        plt.title(
            title
            + ", $\\mu_x$="
            + format(cpymad_instance.table.summ.Q1[0] / ncells, "2.3f")
            + ", $\\mu_y$="
            + format(cpymad_instance.table.summ.Q2[0] / ncells, "2.3f"),
            fontsize=15,
        )
        quadrupole1_dataframe = twiss_dataframe[(twiss_dataframe["keyword"] == "quadrupole")]
        for i in range(len(quadrupole1_dataframe)):
            aux = quadrupole1_dataframe.iloc[i]
            LaTwiss._plot_lattice_series(plt.gca(), aux, height=aux.k1l, v_offset=aux.k1l / 2, color="r")

        quadrupole2_dataframe = twiss_dataframe[(twiss_dataframe["keyword"] == "multipole")]
        for i in range(len(quadrupole2_dataframe)):
            aux = quadrupole2_dataframe.iloc[i]
            LaTwiss._plot_lattice_series(plt.gca(), aux, height=aux.k1l, v_offset=aux.k1l / 2, color="r")

        # Plotting the dipoles
        ax2 = ax1.twinx()
        ax2.set_ylabel("$\\theta$=K0L [rad]", color="blue", fontsize=15)
        ax2.tick_params(axis="y", labelcolor="blue")
        dipoles_dataframe = twiss_dataframe[(twiss_dataframe["keyword"] == "multipole")]
        for i in range(len(dipoles_dataframe)):
            aux = dipoles_dataframe.iloc[i]
            LaTwiss._plot_lattice_series(plt.gca(), aux, height=aux.k0l, v_offset=aux.k0l / 2, color="b")
        plt.ylim(-0.3, 0.3)

        # Plotting beta functions
        plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=ax1)
        plt.plot(twiss_dataframe.s, twiss_dataframe.betx, label="$\\beta_x$")
        plt.plot(twiss_dataframe.s, twiss_dataframe.bety, label="$\\beta_y$")
        plt.legend(loc=2, fontsize=15)
        plt.ylabel("$\\beta$-functions [m]", fontsize=15)
        plt.xlabel("s [m]", fontsize=15)
        plt.grid()

        # Plotting the dispersion
        ax3 = plt.gca().twinx()
        plt.plot(twiss_dataframe.s, twiss_dataframe.dx, color="brown", label="$D_x$", lw=2.5)
        plt.plot(twiss_dataframe.s, twiss_dataframe.dy, ls="-.", color="sienna", label="$D_y$", lw=2.5)
        plt.legend(loc=1, fontsize=15)
        ax3.set_ylabel("Dispersions [m]", color="brown", fontsize=15)
        ax3.tick_params(axis="y", labelcolor="brown")
        plt.ylim(-5, 150)
        if x_limits:
            plt.xlim(x_limits)
        if savefig:
            plt.savefig("latwiss", format="png", dpi=300)

    @staticmethod
    def plot_machine_survey(cpymad_instance, fig_size: tuple, **kwargs) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will create a plot representing the machine
        geometry in 2D. Original code is from Guido Sterbini.
        :param cpymad_instance: an instanciated `cpymad.madx.Madx` object.
        :param fig_size: figure size.
        :return: nothing, plots and eventually saves the figure as a file.
        """
        savefig = kwargs.get("savefig", False)
        cpymad_instance.input("survey;")
        my_survey = cpymad_instance.table.survey.dframe()

        plt.figure(figsize=fig_size)
        plt.scatter(my_survey.z, my_survey.x, c=my_survey.s)
        plt.axis("equal")
        plt.xlabel("z [m]", fontsize=17)
        plt.ylabel("x [m]", fontsize=17)
        plt.grid()
        cbar = plt.colorbar()
        cbar.set_label("s [m]", fontsize=17)
        plt.title("Machine Layout", fontsize=20)

        if savefig:
            plt.savefig("machine_layout", format="png", dpi=300)


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
