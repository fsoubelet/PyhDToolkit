"""
Module cpymadtools.latwiss
--------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to elegantly plot the Twiss parameters output of a cpymad.madx.Madx instance
after it has ran.
"""

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

from loguru import logger

from pyhdtoolkit.plotting.settings import PLOT_PARAMS

try:
    import cpymad
    from cpymad.madx import Madx
except ModuleNotFoundError:
    pass


plt.rcParams.update(PLOT_PARAMS)


class LaTwiss:
    """
    A class to manage plotting the machine survey as well as an elegant plot for elements as
    well as Twiss parameters.
    """

    @staticmethod
    def _plot_lattice_series(
        ax: plt.axes,
        series: pd.DataFrame,
        height: float = 1.0,
        v_offset: float = 0.0,
        color: str = "r",
        alpha: float = 0.5,
        lw: int = 3,
    ) -> None:
        """
        Plots the layout of your machine as a patch of rectangles for different element types.
        Original code from Guido Sterbini.

        Args:
            ax: an existing  matplotlib.axis `Axes` object to act on.
            series: a pandas DataFrame
            height: value to reach for the patch on the y axis.
            v_offset: vertical offset for the patch.
            color: kwarg to transmit to pyplot.
            alpha: kwarg to transmit to pyplot.
            lw: kwarg to transmit to pyplot.

        Returns:
             Nothing, acts directly on the provided axis.
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
    def plot_latwiss(
        cpymad_instance: Madx,
        title: str,
        figsize: tuple = (16, 10),
        savefig: str = None,
        xlimits: tuple = None,
        **kwargs,
    ) -> matplotlib.figure.Figure:
        """
        Provided with an active Cpymad class after having ran a script, will create a plot
        representing nicely the lattice layout and the beta functions along with the horizontal
        dispertion function. This is heavily refactored code, but the original is from Guido
        Sterbini.

        WARNING: This will FAIL if you have not included 'q' or 'Q' in your quadrupoles' names,
        and 'b' or 'B' in your dipoles' names when defining your MAD-X sequence.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            title: title of your plot.
            figsize: size of the figure, defaults to (16, 10)
            savefig: will save the figure if this is not None, using the string value passed.
            xlimits: will implement xlim (for the s coordinate) if this is not None, using the
                     tuple passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        # pylint: disable=too-many-locals
        plot_quadrupoles: bool = kwargs.get("plot_quadrupoles", True)
        plot_dipoles: bool = kwargs.get("plot_dipoles", True)
        plot_sextupoles: bool = kwargs.get("plot_sextupoles", False)
        disp_ylim: tuple = kwargs.get("disp_ylim", (-10, 125))
        beta_ylim: tuple = kwargs.get("beta_ylim", None)
        k0l_lim: tuple = kwargs.get("k0l_lim", (-0.25, 0.25))
        k1l_lim: tuple = kwargs.get("k1l_lim", (-0.08, 0.08))

        # Get data from Madx instance
        logger.debug("Getting Twiss dframe from cpymad")
        twiss_df = cpymad_instance.table.twiss.dframe()
        figure = plt.figure(figsize=figsize)

        # Create a subplot for the lattice patches (takes a third of figure)
        logger.trace("Setting up subplots patches subplots")
        axis1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
        axis2 = axis1.twinx()
        axis1.set_ylabel("1/f=K1L [m$^{-1}$]", color="red")  # quadrupole in red
        axis1.tick_params(axis="y", labelcolor="red")
        axis2.set_ylabel("$\\theta$=K0L [rad]", color="blue")  # dipoles in blue
        axis2.tick_params(axis="y", labelcolor="blue")
        axis1.set_ylim(k1l_lim)
        axis2.set_ylim(k0l_lim)
        axis2.grid(False)
        axis1.set_title(title)
        axis1.plot(twiss_df.s, 0 * twiss_df.s, "k")

        # All elements can be defined as a 'multipole', but dipoles can also be defined as
        # 'rbend' or 'sbend', quadrupoles as 'quadrupoles' and sextupoles as 'sextupoles'
        logger.debug("Extracting element-specific dframes")
        quadrupoles_df = twiss_df[
            (twiss_df.keyword.isin(["multipole", "quadrupole"]))
            & (twiss_df.name.str.contains("Q", case=False))
        ]
        dipoles_df = twiss_df[
            (twiss_df.keyword.isin(["multipole", "rbend", "sbend"]))
            & (twiss_df.name.str.contains("B", case=False))
        ]
        sextupoles_df = twiss_df[
            (twiss_df.keyword.isin(["multipole", "sextupole"]))
            & (twiss_df.name.str.contains("S", case=False))
        ]

        # Plotting dipole patches, beware 'sbend' and 'rbend' have an 'angle' value and not a 'k0l'
        if plot_dipoles:
            logger.debug("Plotting dipole patches")
            for _, dipole in dipoles_df.iterrows():
                if dipole.k0l != 0:
                    logger.trace("Plotting dipole elements")
                    LaTwiss._plot_lattice_series(
                        axis2, dipole, height=dipole.k0l, v_offset=dipole.k0l / 2, color="b"
                    )
                if dipole.angle != 0:
                    logger.trace("Plotting 'sbend' and 'rbend' elements")
                    LaTwiss._plot_lattice_series(
                        axis2, dipole, height=dipole.angle, v_offset=dipole.angle / 2, color="b"
                    )

        # Plotting the quadrupole patches
        if plot_quadrupoles:
            logger.debug("Plotting quadrupole patches")
            for _, quad in quadrupoles_df.iterrows():
                LaTwiss._plot_lattice_series(
                    axis1, quad, height=quad.k1l, v_offset=quad.k1l / 2, color="r"
                )

        # Plotting the sextupole patches
        if plot_sextupoles:
            logger.debug("Plotting sextupole patches")
            for _, sext in sextupoles_df.iterrows():
                LaTwiss._plot_lattice_series(
                    axis2, sext, height=sext.k2l, v_offset=sext.k2l / 2, color="y"
                )

        # Plotting beta functions on remaining two thirds of the figure
        logger.trace("Setting up betatron functions subplot")
        axis3 = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=axis1)
        axis3.plot(twiss_df.s, twiss_df.betx, label="$\\beta_x$", lw=1.5)
        axis3.plot(twiss_df.s, twiss_df.bety, label="$\\beta_y$", lw=1.5)
        axis3.legend(loc=2)
        axis3.set_ylabel("$\\beta$-functions [m]")
        if beta_ylim:
            logger.debug("Setting pre-defined ylim for beta functions plot")
            axis3.set_ylim(beta_ylim)
        axis3.set_xlabel("s [m]")

        # Plotting the dispersion
        logger.trace("Setting up dispersion functions subplot")
        axis4 = axis3.twinx()
        axis4.plot(twiss_df.s, twiss_df.dx, color="brown", label="$D_x$", lw=2)
        axis4.plot(twiss_df.s, twiss_df.dy, ls="-.", color="sienna", label="$D_y$", lw=2)
        axis4.legend(loc=1)
        axis4.set_ylabel("Dispersions [m]", color="brown")
        axis4.tick_params(axis="y", labelcolor="brown")
        axis4.grid(False)
        if disp_ylim:
            logger.debug("Setting pre-defined ylim for dispersion plot")
            axis4.set_ylim(disp_ylim)

        if xlimits:
            logger.debug("Setting pre-defined xlim for longitudinal coordinate")
            plt.xlim(xlimits)
        if savefig:
            logger.info(f"Saving latwiss plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure

    @staticmethod
    def plot_machine_survey(
        cpymad_instance: Madx,
        title: str = "Machine Layout",
        figsize: tuple = (16, 11),
        savefig: str = None,
        show_elements: bool = False,
        high_orders: bool = False,
    ) -> matplotlib.figure.Figure:
        """
        Provided with an active Cpymad class after having ran a script, will create a plot
        representing the machine geometry in 2D. Original code is from Guido Sterbini.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            title: title of your plot.
            figsize: size of the figure, defaults to (16, 10)
            savefig: will save the figure if this is not None, using the string value passed.
            show_elements: if True, will try to plot by differentiating elements. Experimental,
                           default False.
            high_orders: if True, plot sextupoles and octupoles when show_elements is True,
                         otherwise only up to quadrupoles. Default False.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        logger.debug("Getting machine survey from cpymad")
        cpymad_instance.input("survey;")
        survey = cpymad_instance.table.survey.dframe()
        figure = plt.figure(figsize=figsize)

        if show_elements:
            logger.debug("Plotting survey with elements differentiation")
            element_dfs = _make_survey_groups(survey)
            plt.scatter(
                element_dfs["dipoles"].z,
                element_dfs["dipoles"].x,
                marker=".",
                c=element_dfs["dipoles"].s,
                cmap="copper",
                label="Dipoles",
            )
            plt.scatter(
                element_dfs["quad_foc"].z,
                element_dfs["quad_foc"].x,
                marker="o",
                color="blue",
                label="QF",
            )
            plt.scatter(
                element_dfs["quad_defoc"].z,
                element_dfs["quad_defoc"].x,
                marker="o",
                color="red",
                label="QD",
            )
            if high_orders:
                logger.debug("Plotting high order magnetic elements (up to octupoles)")
                plt.scatter(
                    element_dfs["sextupoles"].z,
                    element_dfs["sextupoles"].x,
                    marker=".",
                    color="m",
                    label="MS",
                )
                plt.scatter(
                    element_dfs["octupoles"].z,
                    element_dfs["octupoles"].x,
                    marker=".",
                    color="cyan",
                    label="MO",
                )
            plt.legend(loc=2)

        else:
            logger.debug("Plotting survey without elements differentiation")
            plt.scatter(survey.z, survey.x, c=survey.s)

        plt.axis("equal")
        plt.colorbar().set_label("s [m]")
        plt.xlabel("z [m]")
        plt.ylabel("x [m]")
        plt.title(title)

        if savefig:
            logger.info(f"Saving machine survey plot as {savefig}")
            plt.savefig(savefig, format="png", dpi=500)
        return figure


# ---------------------- Private Utilities ---------------------- #


def _make_survey_groups(survey_df: pd.DataFrame) -> dict:
    """
    Gets a survey dataframe and returns different sub-dataframes corresponding to different
    magnetic elements.

    Args:
        survey_df: a pandas DataFrame obtained from your Madx instance, with
                   <instance>.table.survey.dframe().

    Returns:
        A dictionary containing a dataframe for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.
    """
    logger.debug("Getting different element groups dframes from MAD-X survey")
    return {
        "dipoles": survey_df[
            (survey_df.keyword.isin(["multipole", "sbend", "rbend"]))
            & (survey_df.name.str.contains("B", case=False))
        ],
        "quad_foc": survey_df[
            (survey_df.keyword.isin(["multipole", "quadrupole"]))
            & (survey_df.name.str.contains("Q", case=False))
            & (survey_df.name.str.contains("F", case=False))
        ],
        "quad_defoc": survey_df[
            (survey_df.keyword.isin(["multipole", "quadrupole"]))
            & (survey_df.name.str.contains("Q", case=False))
            & (survey_df.name.str.contains("D", case=False))
        ],
        "sextupoles": survey_df[
            (survey_df.keyword.isin(["multipole", "sextupole"]))
            & (survey_df.name.str.contains("S", case=False))
        ],
        "octupoles": survey_df[
            (survey_df.keyword.isin(["multipole", "octupole"]))
            & (survey_df.name.str.contains("O", case=False))
        ],
    }


def _synchronise_grids(axis_1: matplotlib.axes.Axes, axis_2: matplotlib.axes.Axes) -> None:
    """
    !!! warning
        Experimental! This is currently not stable and may disappear in a future release.

    Little trick to make both y axis synchronise on their grid lines when plotting in dual axis.
    Only the second provided axis will be altered.
    Somehow doesn't work well yet with ticks not starting from 0 up.

    Args:
        axis_1: a matplotlib axis object.
        axis_2: a matplotlib axis object share the x axis with axis_1.

    Returns:
        Nothing, alters the y axis on the provided axis_2.
    """
    logger.warning("Grid synchronization is experimental and may mess up your vertical axis")
    ylim_1 = axis_1.get_ylim()
    len_1 = ylim_1[1] - ylim_1[0]
    yticks_1 = axis_1.get_yticks()
    relative_distance = [(y - ylim_1[0]) / len_1 for y in yticks_1]

    ylim_2 = list(axis_2.get_ylim())
    ylim_2 = [e - ylim_2[0] for e in ylim_2]  # can be a weird offset, fix this
    len_2 = ylim_2[1] - ylim_2[0]
    yticks_2 = [ry * len_2 + ylim_2[0] for ry in relative_distance]

    axis_2.set_yticks(yticks_2)
    axis_2.set_ylim(ylim_2)
    axis_1.yaxis.grid(True, which="major")
    axis_2.yaxis.grid(True, which="major")
