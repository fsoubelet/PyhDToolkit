"""
.. _cpymadtools-plotters-utils:

Plotting Utility Functions
--------------------------

Module with functions to used throught the different `~pyhdtoolkit.cpymadtools.plotters` modules.
"""
from typing import Dict, Tuple

import matplotlib
import matplotlib.axes
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

# ------ Utilities ----- #


def maybe_get_ax(**kwargs):
    """
    .. versionadded:: 1.0.0

    Convenience function to get the axis, regardless of whether or not it is provided
    to the plotting function itself. It used to be that the first argument of plotting
    functions in this package had to be the 'axis' object, but that's no longer the case.

    Args:
        *args: the arguments passed to the plotting function.
        **kwargs: the keyword arguments passed to the plotting function.

    Returns:
        The `~matplotlib.axes.Axes` object to plot on, the args and the kwargs (without the
        'ax' argument if it initially was present). If no axis was provided, then it will be
        created with a call to `~matplotlib.pyplot.gca`.

    Examples:
        This is to be called at the beginning of your plotting functions:

        .. code-block:: python

            >>> def my_plotting_function(*args, **kwargs):
            ...     ax, kwargs = maybe_get_ax(**kwargs)
            ...     # do stuff with ax
            ...     ax.plot(*args, **kwargs)
            ... )
    """
    logger.debug("Looking for axis object to plot on")
    if "ax" in kwargs:
        logger.debug("Using the provided kwargs 'ax' as the axis to plot one")
        ax = kwargs.pop("ax")
    elif "axis" in kwargs:
        logger.debug("Using the provided kwargs 'axis' as the axis to plot on")
        ax = kwargs.pop("axis")
    else:
        logger.debug("No axis provided, using `plt.gca()`")
        ax = plt.gca()
    return ax, dict(kwargs)


# ----- Utility plotters ----- #


def plot_machine_layout(
    madx: Madx,
    axis: matplotlib.axes.Axes,
    title: str,
    xoffset: float = 0,
    xlimits: Tuple[float, float] = None,
    plot_dipoles: bool = True,
    plot_dipole_k1: bool = False,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    k0l_lim: Tuple[float, float] = None,
    k1l_lim: Tuple[float, float] = None,
    k2l_lim: Tuple[float, float] = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Draws patches elements representing the lattice layout on the given *axis*. This is the function that
    takes care of the machine layout axis in `~.plotters.LatticePlotter.plot_latwiss`.

    .. note::
        This current implementation can plot dipoles, quadrupoles, sextupoles and BPMs.

    .. important::
        At the moment, it is important to give this function symmetric limits for the ``k0l_lim``, ``k1l_lim``
        and ``k2l_lim`` arguments. Otherwise the element patches will show up vertically displaced from the
        axis' center line.

    .. warning::
        Currently the function tries to plot legends for the different layout patches. The position of the
        different legends has been hardcoded in corners of the `~matplotlib.axes.Axes` and might require users
        to tweak the axis limits (through ``k0l_lim``, ``k1l_lim`` and ``k2l_lim``) to ensure legend labels and
        plotted elements don't overlap.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        axis (matplotlib.axes.Axes): the `~matplotlib.axes.Axes` axis on draw the elements. By definition,
            the quadrupole elements will be drawn, and for each new element type a call to `~matplotlib.axes.Axes.twinx`
            is made and the new elements will be drawn on the newly created twin `~matplotlib.axes.Axes`.
            title (Optional[str]): title of the `~matplotlib.axes.Axes`.
        xoffset (float): An offset applied to the ``S`` coordinate before plotting. This is useful if
            you want to center a plot around a specific point or element, which would then become located
            at :math:`s = 0`. Beware this offset is applied before applying the *xlimits*. Defaults to 0.
        xlimits (Tuple[float, float]): will implement xlim (for the ``s`` coordinate) if this is
            not ``None``, using the tuple passed.
        plot_dipoles (bool): if `True`, dipole patches will be plotted on the layout subplot of
            the figure. Defaults to `True`. Dipoles are plotted in blue.
        plot_dipole_k1 (bool): if `True`, dipole elements with a quadrupolar gradient will have this
            gradient plotted as a quadrupole patch. Defaults to `False`.
        plot_quadrupoles (bool): if `True`, quadrupole patches will be plotted on the layout
            subplot of the figure. Defaults to `True`. Quadrupoles are plotted in red.
        plot_bpms (bool): if `True`, additional patches will be plotted on the layout subplot to
            represent Beam Position Monitors. BPMs are plotted in dark grey.
        disp_ylim (Tuple[float, float]): vertical axis limits for the dispersion values.
            Defaults to (-10, 125).
        beta_ylim (Tuple[float, float]): vertical axis limits for the betatron function values.
            Defaults to None, to be determined by matplotlib based on the provided beta values.
        k0l_lim (Tuple[float, float]): vertical axis limits for the ``k0l`` values used for the
            height of dipole patches.
        k1l_lim (Tuple[float, float]): vertical axis limits for the ``k1l`` values used for the
            height of quadrupole patches.
        k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
            the figure, and the provided values act as vertical axis limits for the k2l values used for the
            height of sextupole patches.
        **kwargs: any keyword argument will be transmitted to `~.plotters._plot_lattice_series`, and then
        `~matplotlib.patches.Rectangle`, such as ``lw`` etc.
    """
    # pylint: disable=too-many-arguments
    twiss_df = _get_twiss_table_with_offsets_and_limits(madx, xoffset, xlimits)

    logger.trace("Extracting element-specific dataframes")
    element_dfs = make_elements_groups(madx, xoffset, xlimits)
    dipoles_df = element_dfs["dipoles"]
    quadrupoles_df = element_dfs["quadrupoles"]
    sextupoles_df = element_dfs["sextupoles"]
    bpms_df = element_dfs["bpms"]

    logger.debug("Plotting machine layout")
    logger.trace(f"Plotting from axis '{axis}'")
    axis.set_ylabel("$1/f=K_{1}L$ $[m^{-1}]$", color="red")  # quadrupole in red
    axis.tick_params(axis="y", labelcolor="red")
    axis.set_ylim(k1l_lim)
    axis.set_xlim(xlimits)
    axis.set_title(title)
    axis.plot(twiss_df.s, 0 * twiss_df.s, "k")  # 0-level line
    axis.grid(False)

    dipole_patches_axis = axis.twinx()
    dipole_patches_axis.set_ylabel("$\\theta=K_{0}L$ $[rad]$", color="royalblue")  # dipoles in blue
    dipole_patches_axis.tick_params(axis="y", labelcolor="royalblue")
    dipole_patches_axis.set_ylim(k0l_lim)
    dipole_patches_axis.grid(False)

    if plot_dipoles:  # beware 'sbend' and 'rbend' have an 'angle' value and not a 'k0l'
        logger.trace("Plotting dipole patches")
        plotted_elements = 0  # will help us not declare a label for legend at every patch
        for dipole_name, dipole in dipoles_df.iterrows():
            logger.trace(f"Plotting dipole element '{dipole_name}'")
            bend_value = dipole.k0l if dipole.k0l != 0 else dipole.angle
            _plot_lattice_series(
                dipole_patches_axis,
                dipole,
                height=bend_value,
                v_offset=bend_value / 2,
                color="royalblue",
                label="MB" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            if dipole.k1l != 0 and plot_dipole_k1:  # plot dipole quadrupolar gradient (with reduced alpha)
                logger.trace(f"Plotting quadrupolar gradient of dipole element '{dipole_name}'")
                _plot_lattice_series(
                    axis,
                    dipole,
                    height=dipole.k1l,
                    v_offset=dipole.k1l / 2,
                    color="r",
                    **kwargs,
                )
            plotted_elements += 1
        dipole_patches_axis.legend(loc=1)

    if plot_quadrupoles:
        logger.trace("Plotting quadrupole patches")
        plotted_elements = 0
        for quadrupole_name, quadrupole in quadrupoles_df.iterrows():
            logger.trace(f"Plotting quadrupole element '{quadrupole_name}'")
            _plot_lattice_series(
                axis,
                quadrupole,
                height=quadrupole.k1l,
                v_offset=quadrupole.k1l / 2,
                color="r",
                label="MQ" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            plotted_elements += 1
        axis.legend(loc=2)

    if k2l_lim:
        logger.trace("Plotting sextupole patches")
        sextupoles_patches_axis = axis.twinx()
        sextupoles_patches_axis.set_ylabel("$K_{2}L$ $[m^{-2}]$", color="darkgoldenrod")
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
                label="MS" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            plotted_elements += 1
        sextupoles_patches_axis.legend(loc=3)
        sextupoles_patches_axis.grid(False)

    if plot_bpms:
        logger.trace("Plotting BPM patches")
        bpm_patches_axis = axis.twinx()
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
                label="BPM" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            plotted_elements += 1
        bpm_patches_axis.legend(loc=4)
        bpm_patches_axis.grid(False)


def make_elements_groups(
    madx: Madx, xoffset: float = 0, xlimits: Tuple[float, float] = None
) -> Dict[str, pd.DataFrame]:
    """
    .. versionadded:: 1.0.0

    Provided with an active `cpymad` instance after having ran a script, will returns different portions of
    the twiss table's dataframe for different magnetic elements.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        xoffset (float): An offset applied to the S coordinate before plotting. This is useful is you want
            to center a plot around a specific point or element, which would then become located at s = 0.
        xlimits (Tuple[float, float]): will only consider elements within xlim (for the s coordinate) if this
            is not None, using the tuple passed.

    Returns:
        A `dict` containing a `pd.DataFrame` for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.
    """
    twiss_df = _get_twiss_table_with_offsets_and_limits(madx, xoffset, xlimits)

    logger.debug("Getting different element groups dframes from MAD-X twiss table")
    # Elements are detected by their keyword being either 'multipole' or their specific element type,
    # and having a non-zero component (knl / knsl) in their given order (or 'angle' for dipoles)
    return {
        "dipoles": twiss_df[twiss_df.keyword.isin(["multipole", "rbend", "sbend"])].query(
            "k0l != 0 or k0sl != 0 or angle != 0"
        ),
        "quadrupoles": twiss_df[twiss_df.keyword.isin(["multipole", "quadrupole"])].query("k1l != 0 or k1sl != 0"),
        "sextupoles": twiss_df[twiss_df.keyword.isin(["multipole", "sextupole"])].query("k2l != 0 or k2sl " "!= 0"),
        "octupoles": twiss_df[twiss_df.keyword.isin(["multipole", "octupole"])].query("k3l != 0 or k3sl != " "0"),
        "bpms": twiss_df[(twiss_df.keyword.isin(["monitor"])) & (twiss_df.name.str.contains("BPM", case=False))],
    }


def make_survey_groups(madx: Madx) -> Dict[str, pd.DataFrame]:
    """
    .. versionadded:: 1.0.0

    Provided with an active `cpymad` instance after having ran a script, will returns different portions of
    the survey table's dataframe for different magnetic elements.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A `dict` containing a `pd.DataFrame` for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.
    """
    element_dfs = make_elements_groups(madx)
    quadrupoles_focusing_df = element_dfs["quadrupoles"].query("k1l > 0")
    quadrupoles_defocusing_df = element_dfs["quadrupoles"].query("k1l < 0")

    logger.debug("Getting different element groups dframes from MAD-X survey")
    madx.command.survey()

    survey_df = madx.table.survey.dframe().copy()
    return {
        "dipoles": survey_df[survey_df.index.isin(element_dfs["dipoles"].index.tolist())],
        "quad_foc": survey_df[survey_df.index.isin(quadrupoles_focusing_df.index.tolist())],
        "quad_defoc": survey_df[survey_df.index.isin(quadrupoles_defocusing_df.index.tolist())],
        "sextupoles": survey_df[survey_df.index.isin(element_dfs["sextupoles"].index.tolist())],
        "octupoles": survey_df[survey_df.index.isin(element_dfs["octupoles"].index.tolist())],
    }


# ----- Helpers ----- #


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
    .. versionadded:: 1.0.0

    Plots a `~matplotlib.patches.Rectangle` element on the provided `~matplotlib.axes.Axes` to
    represent an element of the machine. Original code from :user:`Guido Sterbini <sterbini>`.

    Args:
        ax (matplotlib.axes.Axes): an existing  `~matplotlib.axes.Axes` object to draw on.
        series (pd.DataFrame): a `pandas.DataFrame` with the elements' data.
        height (float): value to reach for the patch on the y axis.
        v_offset (float): vertical offset for the patch.
        color (str): color kwarg to transmit to `~matplotlib.pyplot`.
        alpha (float): alpha kwarg to transmit to `~matplotlib.pyplot`.
        **kwargs: any keyword argument will be transmitted to `~matplotlib.patches.Rectangle`,
            for instance ``lw`` for the edge line width.
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


def _get_twiss_table_with_offsets_and_limits(
    madx: Madx, xoffset: float = 0, xlimits: Tuple[float, float] = None
) -> pd.DataFrame:
    """
    .. versionadded:: 1.0.0

    Get the twiss dataframe from madx, only within the provided `xlimits` and with the s axis shifted by
    the given `xoffset`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        xoffset (float): An offset applied to the S coordinate in the dataframe.
        xlimits (Tuple[float, float]): will only consider elements within xlimits (for the s coordinate) if
            this is not `None`, using the tuple passed.

    Returns:
        The ``TWISS`` dataframe from ``MAD-X``, with the limits and offset applied, if any.
    """
    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    logger.trace("Getting TWISS table from MAD-X")
    madx.command.twiss()
    twiss_df = madx.table.twiss.dframe().copy()
    twiss_df.s = twiss_df.s - xoffset
    twiss_df = twiss_df[twiss_df.s.between(*xlimits)] if xlimits else twiss_df
    return twiss_df