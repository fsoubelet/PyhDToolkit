"""
.. _plotting-layout:

Layout Plotters
---------------

Module with functions used to represent a machine' elements in an `~matplotlib.axes.Axes`
object, mostly used in different `~pyhdtoolkit.plotting` modules.
"""
from cmath import log
from typing import Tuple

import matplotlib
import matplotlib.axes
import matplotlib.patches as patches
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.plotting.utils import (
    _get_twiss_table_with_offsets_and_limits,
    make_elements_groups,
    maybe_get_ax,
)


def plot_machine_layout(
    madx: Madx,
    title: str = None,
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

    Draws patches elements representing the lattice layout on the given *axis*. This is
    the function that takes care of the machine layout axis in `~.plotting.lattice.plot_latwiss`
    and `~.plotting.aperture.plot_aperture`. Its results can be seen in the
    :ref:`machine lattice <demo-accelerator-lattice>` and :ref:`machine aperture <demo-accelerator-aperture>`
    example galleries.

    .. note::
        This current implementation can plot dipoles, quadrupoles, sextupoles and BPMs.

    .. important::
        If not provided, the limits for the ``k0l_lim``, ``k1l_lim`` will be auto-determined, which might
        not be the perfect choice for you plot. When providing these limits (also for ``k2l_lim``), make
        sure to provide symmetric values around 0 (so [-x, x]) otherwise the element patches will show up
        vertically displaced from the axis' center line.

    .. warning::
        Currently the function tries to plot legends for the different layout patches. The position of the
        different legends has been hardcoded in corners of the `~matplotlib.axes.Axes` and might require users
        to tweak the axis limits (through ``k0l_lim``, ``k1l_lim`` and ``k2l_lim``) to ensure legend labels and
        plotted elements don't overlap.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        title (Optional[str]): if provided, is set as title of the plot. Defaults to `None`.
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
            height of dipole patches, should be symmetric. If `None` (default) is provided, then
            the limits will be auto-determined based on the ``k0l`` values of the dipoles in the
            plot.
        k1l_lim (Tuple[float, float]): vertical axis limits for the ``k1l`` values used for the
            height of quadrupole patches, should be symmetric. If `None` (default) is provided,
            then the limits will be auto-determined based on the ``k0l`` values of the dipoles
            in the plot.
        k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
            the figure, and the provided values act as vertical axis limits for the k2l values used for the
            height of sextupole patches.
        **kwargs: any keyword argument will be transmitted to `~.plotting.utils.plot_machine_layout`, later on
            to `~.plotting.utils._plot_lattice_series`, and then `~matplotlib.patches.Rectangle`, such as ``lw``
            etc. If either `ax` or `axis` is found in the kwargs, the corresponding value is used as the axis
            object to plot on. By definition, the quadrupole elements will be drawn on said axis, and for each
            new element type to plot a call to `~matplotlib.axes.Axes.twinx` is made and the new elements will
            be drawn on the newly created twin `~matplotlib.axes.Axes`.

    Example:
        .. code-block:: python

            >>> fig, ax = plt.subplots(figsize=(6, 2))
            >>> plot_machine_layout(madx, title="Machine Elements", lw=3)
    """
    # pylint: disable=too-many-arguments
    axis, kwargs = maybe_get_ax(**kwargs)
    twiss_df = _get_twiss_table_with_offsets_and_limits(madx, xoffset, xlimits)

    logger.trace("Extracting element-specific dataframes")
    element_dfs = make_elements_groups(madx, xoffset, xlimits)
    dipoles_df = element_dfs["dipoles"]
    quadrupoles_df = element_dfs["quadrupoles"]
    sextupoles_df = element_dfs["sextupoles"]
    bpms_df = element_dfs["bpms"]

    k0l_lim = k0l_lim or _determine_default_knl_lim(dipoles_df, col="k0l", coeff=2)
    k1l_lim = k1l_lim or _determine_default_knl_lim(quadrupoles_df, col="k1l", coeff=1.3)

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


def _determine_default_knl_lim(df: pd.DataFrame, col: str, coeff: float) -> Tuple[float, float]:
    """
    .. versionadded:: 1.0.0

    Determine the default limits for the ``knl`` axis, when plotting machine layout.
    This is in case `None` are provided by the user, to make sure the plot still
    looks coherent and symmetric in `~.plotting.utils.plot_machine_layout`.

    The limits are determined symmetric, using the maximum absolute value of the
    knl column in the provided dataframe and a 1.25 scaling factor.

    Args:
        df (pd.DataFrame): a `pandas.DataFrame` with the multipoles' data.
            The ``knl`` column is used to determine the limits.
        col (str): the 'knl' column to query in the dataframe.
        coeff (float): a scaling factor to apply to the max absolute value
            when determining the limits.

    Returns:
        A `tuple` with the ylimits for the knl axis.
    """
    logger.debug(f"Determining '{col}_lim' based on plotted data")
    max_val = df[col].abs().max()
    max_val_scaled = coeff * max_val
    logger.debug(f"Determined '{col}_lim' are: (-{max_val_scaled}, {max_val_scaled})")
    return (-max_val_scaled, max_val_scaled)
