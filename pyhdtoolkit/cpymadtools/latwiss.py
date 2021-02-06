"""
Module cpymadtools.latwiss
--------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to elegantly plot the Twiss parameters output of a cpymad.madx.Madx
instance after it has ran, or machine survey.
"""
from typing import Dict, Tuple

import matplotlib.axes
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.plotting.settings import PLOT_PARAMS

plt.rcParams.update(PLOT_PARAMS)


# ----- Utilities ----- #


def _plot_lattice_series(
    ax: matplotlib.axes.Axes,
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
        ax (matplotlib.axes.Axes): an existing  matplotlib.axis `Axes` object to act on.
        series (pd.DataFrame): a dataframe with your elements' data.
        height (float): value to reach for the patch on the y axis.
        v_offset (float): vertical offset for the patch.
        color (str): color kwarg to transmit to pyplot.
        alpha (float): alpha kwarg to transmit to pyplot.
        lw (int): linewidth kwarg to transmit to pyplot.
    """
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


def plot_latwiss(
    madx: Madx,
    title: str,
    figsize: Tuple[int, int] = (16, 10),
    savefig: str = None,
    xlimits: Tuple[float, float] = None,
    plot_dipoles: bool = True,
    plot_quadrupoles: bool = True,
    plot_sextupoles: bool = False,
    disp_ylim: Tuple[float, float] = (-10, 125),
    beta_ylim: Tuple[float, float] = None,
    k0l_lim: Tuple[float, float] = (-0.25, 0.25),
    k1l_lim: Tuple[float, float] = (-0.08, 0.08),
) -> matplotlib.figure.Figure:
    """
    Provided with an active Cpymad class after having ran a script, will create a plot
    representing nicely the lattice layout and the beta functions along with the horizontal
    dispertion function. This is heavily refactored code, but the original is from Guido
    Sterbini.

    WARNING: This will FAIL if you have not included 'q' or 'Q' in your quadrupoles' names,
    and 'b' or 'B' in your dipoles' names when defining your MAD-X sequence.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        title (str): title of your plot.
        figsize (Tuple[int, int]): size of the figure, defaults to (16, 10).
        savefig (str): will save the figure if this is not None, using the string value passed.
        xlimits (Tuple[float, float]): will implement xlim (for the s coordinate) if this is
            not None, using the tuple passed.
        plot_dipoles (bool): if True, dipole patches will be plotted on the layout subplot of
            the figure. Defaults to True. Dipoles are plotted in blue.
        plot_quadrupoles (bool): if True, quadrupole patches will be plotted on the layout
            subplot of the figure. Defaults to True. Quadrupoles are plotted in red.
        plot_sextupoles (bool): if True, sextupole patches will be plotted on the layout subplot
            of the figure. Defaults to False. Sextupoles are plotted in yellow.
        disp_ylim (Tuple[float, float]): vertical axis limits for the dispersion values.
            Defaults to (-10, 125).
        beta_ylim (Tuple[float, float]): vertical axis limits for the betatron function values.
            Defaults to None, to be determined by matplotlib based on the provided beta values.
        k0l_lim (Tuple[float, float]): vertical axis limits for the k0l values used for the
            height of dipole patches. Defaults to (-0.25, 0.25).
        k1l_lim (Tuple[float, float]): vertical axis limits for the k1l values used for the
            height of quadrupole patches. Defaults to (-0.08, 0.08).

    Returns:
         The figure on which the plots are drawn. The underlying axes can be accessed with
         'fig.get_axes()'. Eventually saves the figure as a file.
    """
    # pylint: disable=too-many-arguments
    logger.debug("Getting Twiss dataframe from cpymad")
    twiss_df = madx.table.twiss.dframe()
    figure = plt.figure(figsize=figsize)

    # Create a subplot for the lattice patches (takes a third of figure)
    logger.trace("Setting up element patches subplots")
    quadrupole_patches_axis = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
    dipole_patches_axis = quadrupole_patches_axis.twinx()
    quadrupole_patches_axis.set_ylabel("1/f=K1L [m$^{-1}$]", color="red")  # quadrupole in red
    quadrupole_patches_axis.tick_params(axis="y", labelcolor="red")
    dipole_patches_axis.set_ylabel("$\\theta$=K0L [rad]", color="blue")  # dipoles in blue
    dipole_patches_axis.tick_params(axis="y", labelcolor="blue")
    quadrupole_patches_axis.set_ylim(k1l_lim)
    dipole_patches_axis.set_ylim(k0l_lim)
    dipole_patches_axis.grid(False)
    quadrupole_patches_axis.set_title(title)
    quadrupole_patches_axis.plot(twiss_df.s, 0 * twiss_df.s, "k")

    # All elements can be defined as a 'multipole', but dipoles can also be defined as
    # 'rbend' or 'sbend', quadrupoles as 'quadrupoles' and sextupoles as 'sextupoles'
    logger.debug("Extracting element-specific dataframes")
    quadrupoles_df = twiss_df[
        (twiss_df.keyword.isin(["multipole", "quadrupole"])) & (twiss_df.name.str.contains("Q", case=False))
    ]
    dipoles_df = twiss_df[
        (twiss_df.keyword.isin(["multipole", "rbend", "sbend"]))
        & (twiss_df.name.str.contains("B", case=False))
    ]
    sextupoles_df = twiss_df[
        (twiss_df.keyword.isin(["multipole", "sextupole"])) & (twiss_df.name.str.contains("S", case=False))
    ]

    # Plotting dipole patches, beware 'sbend' and 'rbend' have an 'angle' value and not a 'k0l'
    if plot_dipoles:
        logger.debug("Plotting dipole patches")
        for _, dipole in dipoles_df.iterrows():
            if dipole.k0l != 0:
                logger.trace("Plotting dipole element")
                _plot_lattice_series(
                    dipole_patches_axis, dipole, height=dipole.k0l, v_offset=dipole.k0l / 2, color="b",
                )
            if dipole.angle != 0:
                logger.trace("Plotting 'sbend' / 'rbend' element")
                _plot_lattice_series(
                    dipole_patches_axis, dipole, height=dipole.angle, v_offset=dipole.angle / 2, color="b",
                )

    # Plotting the quadrupole patches
    if plot_quadrupoles:
        logger.debug("Plotting quadrupole patches")
        for _, quad in quadrupoles_df.iterrows():
            _plot_lattice_series(
                quadrupole_patches_axis, quad, height=quad.k1l, v_offset=quad.k1l / 2, color="r"
            )

    # Plotting the sextupole patches
    if plot_sextupoles:
        logger.debug("Plotting sextupole patches")
        for _, sext in sextupoles_df.iterrows():
            _plot_lattice_series(dipole_patches_axis, sext, height=sext.k2l, v_offset=sext.k2l / 2, color="y")

    # Plotting beta functions on remaining two thirds of the figure
    logger.trace("Setting up betatron functions subplot")
    betatron_axis = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=quadrupole_patches_axis)
    betatron_axis.plot(twiss_df.s, twiss_df.betx, label="$\\beta_x$", lw=1.5)
    betatron_axis.plot(twiss_df.s, twiss_df.bety, label="$\\beta_y$", lw=1.5)
    betatron_axis.legend(loc=2)
    betatron_axis.set_ylabel("$\\beta$-functions [m]")

    if beta_ylim:
        logger.debug("Setting ylim for betatron functions plot")
        betatron_axis.set_ylim(beta_ylim)
    betatron_axis.set_xlabel("s [m]")

    # Plotting the dispersion
    logger.trace("Setting up dispersion functions subplot")
    dispertion_axis = betatron_axis.twinx()
    dispertion_axis.plot(twiss_df.s, twiss_df.dx, color="brown", label="$D_x$", lw=2)
    dispertion_axis.plot(twiss_df.s, twiss_df.dy, ls="-.", color="sienna", label="$D_y$", lw=2)
    dispertion_axis.legend(loc=1)
    dispertion_axis.set_ylabel("Dispersions [m]", color="brown")
    dispertion_axis.tick_params(axis="y", labelcolor="brown")
    dispertion_axis.grid(False)

    if disp_ylim:
        logger.debug("Setting ylim for dispersion plot")
        dispertion_axis.set_ylim(disp_ylim)

    if xlimits:
        logger.debug("Setting xlim for longitudinal coordinate")
        plt.xlim(xlimits)

    if savefig:
        logger.info(f"Saving latwiss plot as {savefig}")
        plt.savefig(savefig, format="pdf", dpi=500)
    return figure


def plot_machine_survey(
    madx: Madx,
    title: str = "Machine Layout",
    figsize: Tuple[int, int] = (16, 11),
    savefig: str = None,
    show_elements: bool = False,
    high_orders: bool = False,
) -> matplotlib.figure.Figure:
    """
    Provided with an active Cpymad class after having ran a script, will create a plot
    representing the machine geometry in 2D. Original code is from Guido Sterbini.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        title (str): title of your plot.
        figsize (Tuple[int, int]): size of the figure, defaults to (16, 10).
        savefig (str): will save the figure if this is not None, using the string value passed.
        show_elements (bool): if True, will try to plot by differentiating elements.
            Experimental, defaults to False.
        high_orders (bool): if True, plot sextupoles and octupoles when show_elements is True,
            otherwise only up to quadrupoles. Defaults to False.

    Returns:
         The figure on which the plots are drawn. The underlying axes can be accessed with
         'fig.get_axes()'. Eventually saves the figure as a file.
    """
    logger.debug("Getting machine survey from cpymad")
    madx.input("survey;")
    survey = madx.table.survey.dframe()
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
            element_dfs["quad_foc"].z, element_dfs["quad_foc"].x, marker="o", color="blue", label="QF",
        )
        plt.scatter(
            element_dfs["quad_defoc"].z, element_dfs["quad_defoc"].x, marker="o", color="red", label="QD",
        )

        if high_orders:
            logger.debug("Plotting high order magnetic elements (up to octupoles)")
            plt.scatter(
                element_dfs["sextupoles"].z, element_dfs["sextupoles"].x, marker=".", color="m", label="MS",
            )
            plt.scatter(
                element_dfs["octupoles"].z, element_dfs["octupoles"].x, marker=".", color="cyan", label="MO",
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
        plt.savefig(savefig, format="pdf", dpi=500)
    return figure


# ----- Helpers ----- #


def _make_survey_groups(survey_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Gets a survey dataframe and returns different sub-dataframes corresponding to different
    magnetic elements.

    Args:
        survey_df (pd.DataFrame): machine survey dataframe obtained from your Madx instance, with
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
