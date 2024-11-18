"""
.. _plotting-layout:

Layout Plotters
---------------

Module with functions used to represent a machine's
elements in an `~matplotlib.axes.Axes` object, mostly
used in different `~pyhdtoolkit.plotting` modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from loguru import logger
from matplotlib import patches

from pyhdtoolkit.plotting.utils import (
    _get_twiss_table_with_offsets_and_limits,
    make_elements_groups,
    maybe_get_ax,
)

if TYPE_CHECKING:
    from cpymad.madx import Madx
    from matplotlib.axes import Axes
    from pandas import DataFrame


def plot_machine_layout(
    madx: Madx,
    /,
    title: str | None = None,
    xoffset: float = 0,
    xlimits: tuple[float, float] | None = None,
    plot_dipoles: bool = True,
    plot_dipole_k1: bool = False,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    k0l_lim: tuple[float, float] | float | None = None,
    k1l_lim: tuple[float, float] | float | None = None,
    k2l_lim: tuple[float, float] | float | None = None,
    k3l_lim: tuple[float, float] | float | None = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Draws patches elements representing the lattice layout on the
    given *axis*. This is the function that takes care of the machine
    layout axis in `~.plotting.lattice.plot_latwiss` and
    `~.plotting.aperture.plot_aperture`. Its results can be seen in
    the :ref:`machine lattice <demo-accelerator-lattice>` and
    :ref:`machine aperture <demo-accelerator-aperture>` example
    galleries.

    Note
    ----
        This current implementation can plot dipoles, quadrupoles,
        sextupoles, octupoles and BPMs.

    Important
    ---------
        If not provided, the limits for the ``k0l_lim``, ``k1l_lim`` will
        be auto-determined, which might not be the perfect choice for the
        plot. When providing these limits (also for ``k2l_lim``), make sure
        to provide symmetric values around 0 (so [-x, x]) otherwise the element
        patches will show up vertically displaced from the axis' center line.

    Warning
    -------
        Currently the function tries to plot legends for the different layout
        patches. The position of the different legends has been hardcoded in
        corners of the `~matplotlib.axes.Axes` and might require users to tweak
        the axis limits (through ``k0l_lim``, ``k1l_lim`` and ``k2l_lim``) to
        ensure legend labels and plotted elements don't overlap.


    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    title : str, optional
        If provided, is set as title of the plot.
    xoffset : float
        An offset applied to the ``S`` coordinate before plotting. This
        is useful if you want to center a plot around a specific point
        or element, which would then become located at :math:`s = 0`.
        Beware this offset is applied before applying the *xlimits*.
        Defaults to 0.
    xlimits : tuple[float, float], optional
        If given, will be used for the xlim (for the ``s`` coordinate),
        using the tuple passed.
    plot_dipoles : bool
        If `True`, dipole patches will be plotted on the layout subplot
        of the figure. Defaults to `True`. Dipoles are plotted in blue.
    plot_dipole_k1 : bool
        If `True`, dipole elements with a quadrupolar gradient will have
        this gradient plotted as a quadrupole patch. Defaults to `False`.
    plot_quadrupoles : bool
        If `True`, quadrupole patches will be plotted on the layout subplot
        of the figure. Defaults to `True`. Quadrupoles are plotted in red.
    plot_bpms : bool
        If `True`, additional patches will be plotted on the layout subplot
        to represent Beam Position Monitors. BPMs are plotted in dark grey.
        Defaults to `False`.
    k0l_lim : tuple[float, float] | float, optional
        If given, will be used as vertical axis limits for the ``k0l``
        values used for the height of dipole patches. Can be given as a
        single value (float, int) or a tuple (in which case it should be
        symmetric). If `None` is given, then the limits will be determined
        automatically based on the ``k0l`` values of the dipoles.
    k1l_lim : tuple[float, float] | float, optional
        If given, will be used as vertical axis limits for the ``k1l``
        values used for the height of quadrupole patches. Can be given as
        a single value (float, int) or a tuple (in which case it should be
        symmetric). If `None` is given, then the limits will be determined
        automatically based on the ``k1l`` values of the quadrupoles.
    k2l_lim : tuple[float, float] | float, optional
        If given, will be used as vertical axis limits for the ``k2l``
        values used for the height of sextupole patches. Can be given as
        a single value (float, int) or a tuple (in which case it should be
        symmetric). If `None` is given, then the limits will be determined
        automatically based on the ``k2l`` values of the sextupoles.
    k3l_lim : tuple[float, float] | float, optional
        If given, will be used as vertical axis limits for the ``k3l``
        values used for the height of octupole patches. Can be given as
        a single value (float, int) or a tuple (in which case it should be
        symmetric). If `None` is given, then the limits will be determined
        automatically based on the ``k3l`` values of the octupoles.
    **kwargs
        Any keyword argument will be transmitted to
        `~.plotting.utils._plot_lattice_series`, and then
        `~matplotlib.patches.Rectangle`, such as ``lw`` etc. If either
        `ax` or `axis` is found in the kwargs, the corresponding value
        is used as the axis object to plot on. By definition, the
        quadrupole elements will be drawn on said axis, and for each
        new element type to plot a call to `~matplotlib.axes.Axes.twinx`
        is made and the new elements will be drawn on the newly created
        twin `~matplotlib.axes.Axes`. If ``bpms_legend`` is given as
        `False` and BPMs are plotted, the BPM legend will not be plotted
        on the layout axis.

    Example
    -------
        .. code-block:: python

            fig, ax = plt.subplots(figsize=(6, 2))
            plot_machine_layout(madx, title="Machine Elements", lw=3)
    """
    # pylint: disable=too-many-arguments
    axis, kwargs = maybe_get_ax(**kwargs)
    bpms_legend = kwargs.pop("bpms_legend", True)
    twiss_df = _get_twiss_table_with_offsets_and_limits(madx, xoffset, xlimits)

    logger.trace("Extracting element-specific dataframes")
    element_dfs = make_elements_groups(madx, xoffset, xlimits)
    dipoles_df = element_dfs["dipoles"]
    quadrupoles_df = element_dfs["quadrupoles"]
    sextupoles_df = element_dfs["sextupoles"]
    octupoles_df = element_dfs["octupoles"]
    bpms_df = element_dfs["bpms"]

    logger.trace("Determining the ylimits for k0l and k1l patches")
    # Assume lattice doesnt mix 'k0l' and 'angle' for dipoles powering
    dipoles_power_column = "k0l" if dipoles_df.k0l.any() else "angle"
    k0l_lim = (
        _ylim_from_input(k0l_lim, "k0l_lim")
        if k0l_lim is not None
        else _determine_default_knl_lim(dipoles_df, col=dipoles_power_column, coeff=2)
    )
    k1l_lim = (
        _ylim_from_input(k1l_lim, "k1l_lim")
        if k1l_lim is not None
        else _determine_default_knl_lim(quadrupoles_df, col="k1l", coeff=1.3)
    )

    logger.debug("Plotting machine layout")
    logger.trace(f"Plotting from axis '{axis}'")
    axis.set_ylabel("$1/f=K_{1}L$ $[m^{-1}]$", color="red")  # quadrupole in red
    axis.tick_params(axis="y", labelcolor="red")
    axis.set_ylim(k1l_lim)
    if xlimits is not None:
        axis.set_xlim(xlimits)
    axis.set_title(title)
    axis.plot(twiss_df.s, 0 * twiss_df.s, "k")  # 0-level line
    axis.grid(False)

    dipole_patches_axis = axis.twinx()
    dipole_patches_axis.set_ylabel("$\\theta=K_{0}L$ $[rad]$", color="royalblue")  # dipoles in blue
    dipole_patches_axis.tick_params(axis="y", labelcolor="royalblue")
    if np.nan not in k0l_lim:
        dipole_patches_axis.set_ylim(k0l_lim)
    dipole_patches_axis.grid(False)

    if plot_dipoles:  # beware 'sbend' and 'rbend' have an 'angle' value and not a 'k0l'
        logger.trace("Plotting dipole patches")
        plotted_elements = 0  # will help us not declare a label for legend at every patch
        for dipole_name, dipole in dipoles_df.iterrows():
            logger.trace(f"Plotting dipole element '{dipole_name}'")
            bend_value = dipole.k0l if dipole.k0l != 0 else dipole.angle  # check for each element
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
        logger.debug(f"Plotted {plotted_elements} dipole elements")
        if plotted_elements > 0:  # If we plotted at least one dipole, we need to plot the legend
            dipole_patches_axis.legend(loc=1)

    if plot_quadrupoles:
        logger.trace("Plotting quadrupole patches")
        plotted_elements = 0
        for quadrupole_name, quadrupole in quadrupoles_df.iterrows():
            logger.trace(f"Plotting quadrupole element '{quadrupole_name}'")
            element_k = quadrupole.k1l if quadrupole.k1l != 0 else quadrupole.k1sl  # can be skew quadrupole
            _plot_lattice_series(
                axis,
                quadrupole,
                height=element_k,
                v_offset=element_k / 2,
                color="r",
                hatch=None if quadrupole.k1l != 0 else "///",  # hatch skew quadrupoles
                label="MQ" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            plotted_elements += 1
        logger.debug(f"Plotted {plotted_elements} quadrupole elements")
        if plotted_elements > 0:  # If we plotted at least one quadrupole, we need to plot the legend
            axis.legend(loc=2)

    if k2l_lim:
        logger.trace("Plotting sextupole patches")
        sextupoles_patches_axis = axis.twinx()
        sextupoles_patches_axis.set_ylabel("$K_{2}L$ $[m^{-2}]$", color="darkgoldenrod")
        sextupoles_patches_axis.tick_params(axis="y", labelcolor="darkgoldenrod")
        sextupoles_patches_axis.spines["right"].set_position(("axes", 1.12))
        k2l_lim = _ylim_from_input(k2l_lim, "k2l_lim")
        sextupoles_patches_axis.set_ylim(k2l_lim)
        plotted_elements = 0
        for sextupole_name, sextupole in sextupoles_df.iterrows():
            logger.trace(f"Plotting sextupole element '{sextupole_name}'")
            element_k = sextupole.k2l if sextupole.k2l != 0 else sextupole.k2sl  # can be skew sextupole
            _plot_lattice_series(
                sextupoles_patches_axis,
                sextupole,
                height=element_k,
                v_offset=element_k / 2,
                color="goldenrod",
                hatch=None if sextupole.k2l != 0 else "\\\\\\",  # hatch skew sextupoles
                label="MS" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            plotted_elements += 1
        logger.debug(f"Plotted {plotted_elements} sextupole elements")
        sextupoles_patches_axis.grid(False)
        if plotted_elements > 0:  # If we plotted at least one sextupole, we need to plot the legend
            sextupoles_patches_axis.legend(loc=3)

    if k3l_lim:
        logger.trace("Plotting octupole patches")
        octupoles_patches_axis = axis.twinx()
        octupoles_patches_axis.set_ylabel("$K_{3}L$ $[m^{-3}]$", color="forestgreen")
        octupoles_patches_axis.tick_params(axis="y", labelcolor="forestgreen")
        octupoles_patches_axis.yaxis.set_label_position("left")
        octupoles_patches_axis.yaxis.tick_left()
        octupoles_patches_axis.spines["left"].set_position(("axes", -0.14))
        k3l_lim = _ylim_from_input(k3l_lim, "k3l_lim")
        octupoles_patches_axis.set_ylim(k3l_lim)
        plotted_elements = 0
        for octupole_name, octupole in octupoles_df.iterrows():
            logger.trace(f"Plotting octupole element '{octupole_name}'")
            element_k = octupole.k3l if octupole.k3l else octupole.k3sl  # can be skew octupole
            _plot_lattice_series(
                octupoles_patches_axis,
                octupole,
                height=octupole.k3l,
                v_offset=octupole.k3l / 2,
                color="forestgreen",
                hatch=None if octupole.k3l != 0 else "xxx",  # hatch skew octupoles
                label="MO" if plotted_elements == 0 else None,  # avoid duplicating legend labels
                **kwargs,
            )
            plotted_elements += 1
        logger.debug(f"Plotted {plotted_elements} octupole elements")
        octupoles_patches_axis.grid(False)
        if plotted_elements > 0:  # If we plotted at least one octupole, we need to plot the legend
            octupoles_patches_axis.legend(loc=4)

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
        logger.debug(f"Plotted {plotted_elements} BPMs")
        logger.trace("Determining BPM legend location")
        if bpms_legend is True:
            if k2l_lim is not None and k3l_lim is not None:
                bpm_legend_loc = 8  # all corners are taken, we go bottom center
            elif k2l_lim is not None:
                bpm_legend_loc = 4  # sextupoles are here but not octupoles, we go bottom left
            elif k3l_lim is not None:  # pragma: no cover
                bpm_legend_loc = 3  # octupoles are here but not sextupoles, we go bottom right
            else:
                bpm_legend_loc = "best"  # can't easily determine the best position, go automatic and leave to the user
            if plotted_elements > 0:  # If we plotted at least one BPM, we need to plot the legend
                bpm_patches_axis.legend(loc=bpm_legend_loc)
        bpm_patches_axis.grid(False)


def scale_patches(scale: float, ylabel: str, **kwargs) -> None:
    """
    .. versionadded:: 1.3.0

    This is a convenience function to update the scale of the
    elements layout patches as well as the corresponding y-axis
    label.

    Parameters
    ----------
    scale : float
        The scale factor to apply to the patches. The new height
        of the patches will be ``scale * original_height``.
    ylabel : str
        The new label for the y-axis.
    **kwargs
        If either `ax` or `axis` is found in the kwargs, the
        corresponding value is used as the axis object to plot on,
        otherwise the current axis is used.

    Example
    -------
        .. code-block:: python

            fig, ax = plt.subplots(figsize=(6, 2))
            plot_machine_layout(madx, title="Machine Elements", lw=3)
            scale_patches(ax=fig.axes[0], scale=100, ylabel=r"$K_{1}L$ $[10^{-2} m^{-1}]$")
    """
    axis, kwargs = maybe_get_ax(**kwargs)
    axis.set_ylabel(ylabel)
    for patch in axis.patches:
        h = patch.get_height()
        patch.set_height(scale * h)


# ----- Helpers ----- #


def _plot_lattice_series(
    ax: Axes,
    series: DataFrame,
    height: float = 1.0,
    v_offset: float = 0.0,
    color: str = "r",
    alpha: float = 0.5,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Plots a `~matplotlib.patches.Rectangle` element on the provided
    `~matplotlib.axes.Axes` to represent an element of the machine.
    Original code from :user:`Guido Sterbini <sterbini>`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        An existing `~matplotlib.axes.Axes` object to draw on.
    series : pd.DataFrame
        A `pandas.DataFrame` with the elements' data.
    height : float
        Value to reach for the patch on the y axis. Defaults to 1.
    v_offset : float
        Vertical offset for the patch. Defaults to 0. Should not
        be used unless you know exactly what you're doing.
    color : str
        Color kwarg to transmit to `~matplotlib.pyplot`. Defaults
        to 'r', for red.
    alpha : float
        Alpha kwarg to transmit to `~matplotlib.pyplot`. Defaults
        to 0.5.
    **kwargs
        Any keyword argument will be transmitted to
        `~matplotlib.patches.Rectangle`, for instance ``lw`` for
        the edge line width.
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


def _ylim_from_input(ylim: tuple[float, float] | float | int, name_for_error: str = "knl_lim") -> tuple[float, float]:
    """
    .. versionadded:: 1.2.0

    Determines the ylimits for a given axis from the input provided
    by the user. This is used in `~.plotting.utils.plot_machine_layout`
    and handles different inputs from the user, such as a tuple, a float
    and an int.

    Parameters
    ----------
    ylim : tuple[float, float] | float | int
        The input provided by the user.
    name_for_error : str
        The name of the variable to use in the error message.

    Returns
    -------
    tuple[float, float]
        A `tuple` for the ylimits from the input.

    Raises
    ------
    TypeError
        If the input is not a `tuple`, a `float` or an `int`.
    """
    if not isinstance(ylim, tuple | float | int):
        msg = f"Invalid type for '{name_for_error}': {type(ylim)}. "
        raise TypeError(msg)

    if isinstance(ylim, tuple):
        return ylim

    # otherwise we have float | int
    if ylim >= 0:
        return (-ylim, ylim)
    return (ylim, -ylim)


def _determine_default_knl_lim(df: DataFrame, col: str, coeff: float) -> tuple[float, float]:
    """
    .. versionadded:: 1.0.0

    Determine the default limits for the ``knl`` axis, when plotting
    machine layout. This is in case `None` are provided by the user,
    to make sure the plot still looks coherent and symmetric in
    `~.plotting.utils.plot_machine_layout`.

    The limits are determined symmetric, using the maximum absolute
    value of the knl column in the provided dataframe and a 1.25
    scaling factor.

    Parameters
    ----------
    df : pandas.DataFrame
        A `pandas.DataFrame` with the multipoles' data. The ``knl``
        column is used to determine the limits.
    col : str
        The 'knl' column to query in the dataframe.
    coeff : float
        A scaling factor to apply to the max absolute value when
        determining the limits.

    Returns
    -------
    tuple[float, float]
        A `tuple` with the ylimits for the knl axis.
    """
    logger.debug(f"Determining '{col}_lim' based on plotted data")
    max_val = df[col].abs().max()
    max_val_scaled = coeff * max_val
    logger.debug(f"Determined '{col}_lim' are: (-{max_val_scaled}, {max_val_scaled})")
    return (-max_val_scaled, max_val_scaled)
