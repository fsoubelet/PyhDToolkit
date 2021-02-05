"""
Module tfstools.latwiss
--------------------------

Created on 2020.10.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to elegantly plot the Twiss parameters output of a MADX twiss command,
either from a file on disk or a loaded TfsDataFrame.
"""
from pathlib import Path
from typing import Dict, List, Tuple, Union

import matplotlib.axes
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
import tfs

from loguru import logger

from pyhdtoolkit.plotting.settings import PLOT_PARAMS

plt.rcParams.update(PLOT_PARAMS)


# ----- Plotting Functionality -----


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


def plot_latwiss(
    twiss_ouptut: Union[str, Path, tfs.TfsDataFrame, pd.DataFrame] = None,
    title: str = None,
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
        twiss_ouptut (Union[str, Path, tfs.TfsDataFrame, pd.DataFrame]): the output of the MADX
            twiss command, either loaded as a tfs.TfsDataFrame or the location of the output
            file on disk.
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
    twiss_df: tfs.TfsDataFrame = _get_tfs_dataframe_from_input(twiss_ouptut)
    twiss_df.columns = [colname.lower() for colname in twiss_df.columns]
    _assert_necessary_columns(twiss_df, columns=["s", "keyword", "betx", "bety", "dx", "dy"])
    elements_df = _make_survey_groups(twiss_df)

    logger.info("Setting up figure")
    figure = plt.figure(figsize=figsize)

    # Create a subplot for the lattice patches (takes a third of figure)
    logger.trace("Setting up element patches subplots")
    quadrupole_patches_axis = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
    dipole_patches_axis = quadrupole_patches_axis.twinx()
    quadrupole_patches_axis.set_ylabel(r"1/f=K1L [m$^{-1}$]", color="red")  # quadrupole in red
    quadrupole_patches_axis.tick_params(axis="y", labelcolor="red")
    dipole_patches_axis.set_ylabel(r"$\theta$=K0L [rad]", color="blue")  # dipoles in blue
    dipole_patches_axis.tick_params(axis="y", labelcolor="blue")
    quadrupole_patches_axis.set_ylim(k1l_lim)
    dipole_patches_axis.set_ylim(k0l_lim)
    dipole_patches_axis.grid(False)
    quadrupole_patches_axis.set_title(title)
    quadrupole_patches_axis.plot(twiss_df.s, 0 * twiss_df.s, "k")

    # Plotting dipole patches, beware 'sbend' and 'rbend' have an 'angle' value and not a 'k0l'
    if plot_dipoles:
        _assert_necessary_columns(twiss_df, columns=["k0l", "angle"])
        dipoles_df = elements_df["dipoles"]
        logger.debug("Plotting dipole patches")
        for _, dipole in dipoles_df.iterrows():
            if dipole.k0l != 0:
                logger.trace("Plotting dipole element")
                _plot_lattice_series(
                    dipole_patches_axis, dipole, height=dipole.k0l, v_offset=dipole.k0l / 2, color="b",
                )
            elif dipole.angle != 0:
                logger.trace("Plotting 'sbend' / 'rbend' element")
                _plot_lattice_series(
                    dipole_patches_axis, dipole, height=dipole.angle, v_offset=dipole.angle / 2, color="b",
                )

    # Plotting the quadrupole patches
    if plot_quadrupoles:
        _assert_necessary_columns(twiss_df, columns=["k1l"])
        quadrupoles_df = elements_df["quadrupoles"]
        logger.debug("Plotting quadrupole patches")
        for _, quad in quadrupoles_df.iterrows():
            _plot_lattice_series(
                quadrupole_patches_axis, quad, height=quad.k1l, v_offset=quad.k1l / 2, color="r"
            )

    # Plotting the sextupole patches
    if plot_sextupoles:
        _assert_necessary_columns(twiss_df, columns=["k2l"])
        sextupoles_df = elements_df["sextupoles"]
        logger.debug("Plotting sextupole patches")
        for _, sext in sextupoles_df.iterrows():
            _plot_lattice_series(dipole_patches_axis, sext, height=sext.k2l, v_offset=sext.k2l / 2, color="y")

    # Plotting beta functions on remaining two thirds of the figure
    logger.trace("Setting up betatron functions subplot")
    betatron_axis = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=quadrupole_patches_axis)
    betatron_axis.plot(twiss_df.s, twiss_df.betx, label=r"$\beta_{x}$", lw=1.5)
    betatron_axis.plot(twiss_df.s, twiss_df.bety, label=r"$\beta_{y}$", lw=1.5)
    betatron_axis.legend(loc=2)
    betatron_axis.set_ylabel(r"$\beta$-functions [m]")
    if beta_ylim:
        logger.debug("Setting ylim for betatron functions plot")
        betatron_axis.set_ylim(beta_ylim)
    betatron_axis.set_xlabel("s [m]")

    # Plotting the dispersion
    logger.trace("Setting up dispersion functions subplot")
    dispertion_axis = betatron_axis.twinx()
    dispertion_axis.plot(twiss_df.s, twiss_df.dx, color="brown", label=r"$D_{x}$", lw=2)
    dispertion_axis.plot(twiss_df.s, twiss_df.dy, ls="-.", color="sienna", label=r"$D_{y}$", lw=2)
    dispertion_axis.legend(loc=1)
    dispertion_axis.set_ylabel("Dispersion [m]", color="brown")
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
        plt.savefig(savefig, format="pdf", dpi=350)
    return figure


# ----- Helpers ----1-


def _get_tfs_dataframe_from_input(
    twiss_input: Union[str, Path, tfs.TfsDataFrame, pd.DataFrame]
) -> tfs.TfsDataFrame:
    """

    Args:
        twiss_input (Union[str, Path, tfs.TfsDataFrame. pd.DataFrame]): the output of the MADX
            twiss command, either loaded as a tfs.TfsDataFrame or the location of the output file
            on disk.

    Returns:
        A TfsDataFrame or pd.DataFrame with the data.
    """
    if isinstance(twiss_input, (Path, str)):
        logger.trace("Loading Twiss dataframe from disk")
        return tfs.read(Path(twiss_input))
    if isinstance(twiss_input, (pd.DataFrame, tfs.TfsDataFrame)):
        logger.trace("Copying input dataframe")
        return twiss_input.copy()
    logger.error(
        "Expected either a string, Path object or TfsDataFrame, but provided input "
        f"was of type '{type(twiss_input)}'"
    )
    raise ValueError(f"Invalid input type for argument 'twiss_input': {type(twiss_input)}")


def _assert_necessary_columns(dataframe: Union[pd.DataFrame, tfs.TfsDataFrame], columns: List[str]) -> None:
    """
    Checks the presence of needed inputs for the latwiss plot in the provided dataframe. Will
    raise a KeyError if any of them is missing.

    Args:
        dataframe (Union[pd.DataFrame, tfs.TfsDataFrame]): the dataframe used for the data.
        columns (List[str]): list of column names to check for.
    """
    if any(colname not in dataframe.columns for colname in columns):
        logger.error(
            "Some necessary columns are missing in the provided dataframe.\n"
            f"The required columns are: {columns}\n"
            f"The detected columns are: {dataframe.columns.to_numpy()}"
        )
        raise KeyError("Missing columns in the provided dataframe")


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
        "quadrupoles": survey_df[
            (survey_df.keyword.isin(["multipole", "quadrupole"]))
            & (survey_df.name.str.contains("Q", case=False))
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
