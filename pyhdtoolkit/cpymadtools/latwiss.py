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

from pyhdtoolkit.utils.defaults import PLOT_PARAMS

plt.rcParams.update(PLOT_PARAMS)
plt.rcParams.update({"xtick.direction": "in", "ytick.direction": "in"})  # need to reiterate these somehow

# ----- Plotters ----- #


def plot_latwiss(
    madx: Madx,
    title: str,
    figsize: Tuple[int, int] = (18, 11),
    savefig: str = None,
    xoffset: float = 0,
    xlimits: Tuple[float, float] = None,
    plot_dipoles: bool = True,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    disp_ylim: Tuple[float, float] = (-10, 125),
    beta_ylim: Tuple[float, float] = None,
    k0l_lim: Tuple[float, float] = (-0.25, 0.25),
    k1l_lim: Tuple[float, float] = (-0.08, 0.08),
    k2l_lim: Tuple[float, float] = None,
    **kwargs,
) -> matplotlib.figure.Figure:
    """
    Provided with an active Cpymad class after having ran a script, will create a plot representing nicely
    the lattice layout and the beta functions along with the horizontal dispertion function. This is very
    heavily refactored code, inspired by code from Guido Sterbini.

    WARNING: This WILL FAIL if you have not included 'q' or 'Q' in your quadrupoles' names, and 'b' or 'B'
    in your dipoles' names when defining your MAD-X sequence.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        title (str): title of your plot.
        figsize (Tuple[int, int]): size of the figure, defaults to (16, 10).
        savefig (str): will save the figure if this is not None, using the string value passed.
        xoffset (float): An offset applied to the S coordinate before plotting. This is useful is you want
            to center a plot around a specific point or element, which would then become located at s = 0.
            Beware this offset is applied before applying the `xlimits`. Offset defaults to 0 (no change).
        xlimits (Tuple[float, float]): will implement xlim (for the s coordinate) if this is
            not None, using the tuple passed.
        plot_dipoles (bool): if True, dipole patches will be plotted on the layout subplot of
            the figure. Defaults to True. Dipoles are plotted in blue.
        plot_quadrupoles (bool): if True, quadrupole patches will be plotted on the layout
            subplot of the figure. Defaults to True. Quadrupoles are plotted in red.
        plot_bpms (bool): if True, additional patches will be plotted on the layout subplot to represent
            Beam Position Monitors. BPMs are plotted in dark grey.
        disp_ylim (Tuple[float, float]): vertical axis limits for the dispersion values.
            Defaults to (-10, 125).
        beta_ylim (Tuple[float, float]): vertical axis limits for the betatron function values.
            Defaults to None, to be determined by matplotlib based on the provided beta values.
        k0l_lim (Tuple[float, float]): vertical axis limits for the k0l values used for the
            height of dipole patches. Defaults to (-0.25, 0.25).
        k1l_lim (Tuple[float, float]): vertical axis limits for the k1l values used for the
            height of quadrupole patches. Defaults to (-0.08, 0.08).
        k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
            the figure, and the provided values act as vertical axis limits for the k2l values used for the
            height of sextupole patches.

    Keyword Args:
        Any keyword argument to be transmitted to `_plot_machine_layout`, later on to `plot_lattice_series`
        and then `matplotlib.patches.Rectangle`, such as lw etc.

    WARNING:
        Currently the function tries to plot legends for the different layout patches. The position of the
        different legends has been hardcoded in corners and might require users to tweak the axis limits
        (through `k0l_lim`, `k1l_lim` and `k2l_lim`) to ensure legend labels and plotted elements don't
        overlap.

    Returns:
         The figure on which the plots are drawn. The underlying axes can be accessed with
         'fig.get_axes()'. Eventually saves the figure as a file.
    """
    # pylint: disable=too-many-arguments
    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    logger.info("Plotting optics functions and machine layout")
    logger.debug("Getting Twiss dataframe from cpymad")
    twiss_df = madx.table.twiss.dframe().copy()
    twiss_df.s = twiss_df.s - xoffset
    xlimits = (twiss_df.s.min(), twiss_df.s.max()) if xlimits is None else xlimits
    twiss_df = twiss_df[twiss_df.s.between(xlimits[0], xlimits[1])] if xlimits else twiss_df

    # Create a subplot for the lattice patches (takes a third of figure)
    figure = plt.figure(figsize=figsize)
    quadrupole_patches_axis = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
    _plot_machine_layout(
        madx,
        quadrupole_patches_axis=quadrupole_patches_axis,
        title=title,
        xoffset=xoffset,
        xlimits=xlimits,
        plot_dipoles=plot_dipoles,
        plot_quadrupoles=plot_quadrupoles,
        plot_bpms=plot_bpms,
        k0l_lim=k0l_lim,
        k1l_lim=k1l_lim,
        k2l_lim=k2l_lim,
        **kwargs,
    )

    # Plotting beta functions on remaining two thirds of the figure
    logger.debug("Setting up betatron functions subplot")
    betatron_axis = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=quadrupole_patches_axis)
    betatron_axis.plot(twiss_df.s, twiss_df.betx, label="$\\beta_x$", lw=2)
    betatron_axis.plot(twiss_df.s, twiss_df.bety, label="$\\beta_y$", lw=2)
    betatron_axis.legend(loc=2)
    betatron_axis.set_ylabel("$\\beta_{x,y}$ $[m]$")
    betatron_axis.set_xlabel("$S$ $[m]$")

    logger.trace("Setting up dispersion functions subplot")
    dispertion_axis = betatron_axis.twinx()
    dispertion_axis.plot(twiss_df.s, twiss_df.dx, color="brown", label="$D_x$", lw=2)
    dispertion_axis.plot(twiss_df.s, twiss_df.dy, ls="-.", color="sienna", label="$D_y$", lw=2)
    dispertion_axis.legend(loc=1)
    dispertion_axis.set_ylabel("$D_{x,y}$ $[m]$", color="brown")
    dispertion_axis.tick_params(axis="y", labelcolor="brown")
    dispertion_axis.grid(False)

    if beta_ylim:
        logger.debug("Setting ylim for betatron functions plot")
        betatron_axis.set_ylim(beta_ylim)

    if disp_ylim:
        logger.debug("Setting ylim for dispersion plot")
        dispertion_axis.set_ylim(disp_ylim)

    if xlimits:
        logger.debug("Setting xlim for longitudinal coordinate")
        plt.xlim(xlimits)

    if savefig:
        logger.info(f"Saving latwiss plot as {savefig}")
        plt.savefig(savefig)
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
    madx.command.survey()
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
        plt.scatter(survey.z, survey.x, c=survey.s, marker=".")

    plt.axis("equal")
    plt.colorbar().set_label("$S$ $[m]$")
    plt.xlabel("$Z$ $[m]$")
    plt.ylabel("$X$ $[m]$")
    plt.title(title)

    if savefig:
        logger.info(f"Saving machine survey plot as {savefig}")
        plt.savefig(savefig)
    return figure


# ----- Utility plotters ----- #


def _plot_lattice_series(
    ax: matplotlib.axes.Axes,
    series: pd.DataFrame,
    height: float = 1.0,
    v_offset: float = 0.0,
    color: str = "r",
    alpha: float = 0.5,
    **kwargs,
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

    Keyword Args:
        Any kwarg that can be given to matplotlib.patches.Rectangle(), for instance `lw` for the edge line
        width.
    """
    ax.add_patch(
        patches.Rectangle(
            (series.s - series.l, v_offset - height / 2.0),  # anchor point
            series.l,  # width
            height,  # height
            color=color,
            alpha=alpha,
            **kwargs,
        )
    )


def _plot_machine_layout(
    madx: Madx,
    quadrupole_patches_axis: matplotlib.axes.Axes,
    title: str,
    xoffset: float = 0,
    xlimits: Tuple[float, float] = None,
    plot_dipoles: bool = True,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    k0l_lim: Tuple[float, float] = (-0.25, 0.25),
    k1l_lim: Tuple[float, float] = (-0.08, 0.08),
    k2l_lim: Tuple[float, float] = None,
    **kwargs,
) -> None:
    """
    Provided with an active Cpymad class after having ran a script, will plot the lattice layout and the
    on a given axis. This is the function that takes care of the machine layout in `plot_latwiss`, and
    is in theory a private function, though if you know what you are doing you may use it individually.

    WARNING: This WILL FAIL if you have not included 'q' or 'Q' in your quadrupoles' names, and 'b' or 'B'
    in your dipoles' names when defining your MAD-X sequence.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        quadrupole_patches_axis (matplotlib.axes.Axes): the axis on which to plot. Will also create the
            appropriate new axes with `twinx()` to plot the element orders asked for.
        title (str): title of your plot.
        xoffset (float): An offset applied to the S coordinate before plotting. This is useful is you want
            to center a plot around a specific point or element, which would then become located at s = 0.
            Beware this offset is applied before applying the `xlimits`. Offset defaults to 0 (no change).
        xlimits (Tuple[float, float]): will implement xlim (for the s coordinate) if this is
            not None, using the tuple passed.
        plot_dipoles (bool): if True, dipole patches will be plotted on the layout subplot of
            the figure. Defaults to True. Dipoles are plotted in blue.
        plot_quadrupoles (bool): if True, quadrupole patches will be plotted on the layout
            subplot of the figure. Defaults to True. Quadrupoles are plotted in red.
        plot_bpms (bool): if True, additional patches will be plotted on the layout subplot to represent
            Beam Position Monitors. BPMs are plotted in dark grey.
        k0l_lim (Tuple[float, float]): vertical axis limits for the k0l values used for the
            height of dipole patches. Defaults to (-0.25, 0.25).
        k1l_lim (Tuple[float, float]): vertical axis limits for the k1l values used for the
            height of quadrupole patches. Defaults to (-0.08, 0.08).
        k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
            the figure, and the provided values act as vertical axis limits for the k2l values used for the
            height of sextupole patches.

    Keyword Args:
        Any keyword argument to be transmitted to `_plot_lattice_series`, and later on to
        `matplotlib.patches.Rectangle`, such as lw etc.

    WARNING:
        Currently the function tries to plot legends for the different layout patches. The position of the
        different legends has been hardcoded in corners and might require users to tweak the axis limits
        (through `k0l_lim`, `k1l_lim` and `k2l_lim`) to ensure legend labels and plotted elements don't
        overlap.
    """
    # pylint: disable=too-many-arguments
    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    logger.trace("Getting Twiss dataframe from cpymad")
    twiss_df = madx.table.twiss.dframe().copy()
    twiss_df.s = twiss_df.s - xoffset
    twiss_df = twiss_df[twiss_df.s.between(xlimits[0], xlimits[1])] if xlimits else twiss_df

    logger.debug("Plotting machine layout")
    logger.trace(f"Plotting from axis '{quadrupole_patches_axis}'")
    quadrupole_patches_axis.set_ylabel("$1/f=K_{1}L$ $[m^{-1}]$", color="red")  # quadrupole in red
    quadrupole_patches_axis.tick_params(axis="y", labelcolor="red")
    quadrupole_patches_axis.set_ylim(k1l_lim)
    quadrupole_patches_axis.set_xlim(xlimits)
    quadrupole_patches_axis.set_title(title)
    quadrupole_patches_axis.plot(twiss_df.s, 0 * twiss_df.s, "k")  # 0-level line
    quadrupole_patches_axis.grid(False)

    dipole_patches_axis = quadrupole_patches_axis.twinx()
    dipole_patches_axis.set_ylabel("$\\theta=K_{0}L$ $[rad]$", color="royalblue")  # dipoles in blue
    dipole_patches_axis.tick_params(axis="y", labelcolor="royalblue")
    dipole_patches_axis.set_ylim(k0l_lim)
    dipole_patches_axis.grid(False)

    # All elements can be defined as a 'multipole', but dipoles can also be defined as 'rbend' or 'sbend',
    # quadrupoles as 'quadrupoles' and sextupoles as 'sextupoles'. Function does not handle higher orders.
    logger.debug("Extracting element-specific dataframes")
    dipoles_df = twiss_df[
        (twiss_df.keyword.isin(["multipole", "rbend", "sbend"]))
        & (twiss_df.name.str.contains("B", case=False))
    ]
    quadrupoles_df = twiss_df[
        (twiss_df.keyword.isin(["multipole", "quadrupole"])) & (twiss_df.name.str.contains("Q", case=False))
    ]
    sextupoles_df = twiss_df[
        (twiss_df.keyword.isin(["multipole", "sextupole"])) & (twiss_df.name.str.contains("S", case=False))
    ]
    bpms_df = twiss_df[(twiss_df.keyword.isin(["monitor"])) & (twiss_df.name.str.contains("BPM", case=False))]

    if plot_dipoles:  # beware 'sbend' and 'rbend' have an 'angle' value and not a 'k0l'
        logger.debug("Plotting dipole patches")
        plotted_elements = 0  # will help us not declare a label for legend at every patch
        for dipole_name, dipole in dipoles_df.iterrows():  # by default twiss.dframe() has names as index
            if dipole.k0l != 0 or dipole.angle != 0:
                logger.trace(f"Plotting dipole element '{dipole_name}'")
                _plot_lattice_series(
                    dipole_patches_axis,
                    dipole,
                    height=dipole.k0l if dipole.k0l != 0 else dipole.angle,
                    v_offset=dipole.k0l / 2 if dipole.k0l != 0 else dipole.angle / 2,
                    color="royalblue",
                    label="MB" if plotted_elements == 0 else None,
                    **kwargs,
                )
                plotted_elements += 1
        dipole_patches_axis.legend(loc=1, fontsize=16)

    if plot_quadrupoles:
        logger.debug("Plotting quadrupole patches")
        plotted_elements = 0
        for quadrupole_name, quadrupole in quadrupoles_df.iterrows():
            logger.trace(f"Plotting quadrupole element '{quadrupole_name}'")
            _plot_lattice_series(
                quadrupole_patches_axis,
                quadrupole,
                height=quadrupole.k1l,
                v_offset=quadrupole.k1l / 2,
                color="r",
                label="MQ" if plotted_elements == 0 else None,
                **kwargs,
            )
            plotted_elements += 1
        quadrupole_patches_axis.legend(loc=2, fontsize=16)

    if k2l_lim:
        logger.debug("Plotting sextupole patches")
        sextupoles_patches_axis = quadrupole_patches_axis.twinx()
        sextupoles_patches_axis.set_ylabel("K2L [m$^{-2}$]", color="darkgoldenrod")
        sextupoles_patches_axis.tick_params(axis="y", labelcolor="darkgoldenrod")
        sextupoles_patches_axis.spines["right"].set_position(("axes", 1.1))
        sextupoles_patches_axis.set_ylim(k2l_lim)
        plotted_elements = 0
        for sextupole_name, sextupole in sextupoles_df.iterrows():
            logger.trace(f"Plotting sextupole element '{sextupole_name}'")
            _plot_lattice_series(
                sextupoles_patches_axis,
                sextupole,
                height=sextupole.k2l,
                v_offset=sextupole.k2l / 2,
                color="goldenrod",
                label="MS" if plotted_elements == 0 else None,
                **kwargs,
            )
            plotted_elements += 1
        sextupoles_patches_axis.legend(loc=3, fontsize=16)
        sextupoles_patches_axis.grid(False)

    if plot_bpms:
        logger.debug("Plotting BPM patches")
        bpm_patches_axis = quadrupole_patches_axis.twinx()
        bpm_patches_axis.set_axis_off()  # hide yticks, labels etc
        bpm_patches_axis.set_ylim(-1.6, 1.6)
        plotted_elements = 0
        for bpm_name, bpm in bpms_df.iterrows():
            logger.trace(f"Plotting BPM element '{bpm_name}'")
            _plot_lattice_series(
                bpm_patches_axis,
                bpm,
                height=2,
                v_offset=0,
                color="dimgrey",
                label="BPM" if plotted_elements == 0 else None,
                **kwargs,
            )
            plotted_elements += 1
        bpm_patches_axis.legend(loc=4, fontsize=16)
        bpm_patches_axis.grid(False)


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
