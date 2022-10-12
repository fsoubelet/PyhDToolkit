"""
.. _plotting-lattice:

Lattice Plotters
----------------

Module with functions to create lattice plots through a `~cpymad.madx.Madx` object.
"""
from typing import Optional, Tuple

import matplotlib
import matplotlib.axes
import matplotlib.pyplot as plt
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.plotting.layout import plot_machine_layout
from pyhdtoolkit.plotting.utils import (
    _get_twiss_table_with_offsets_and_limits,
    make_survey_groups,
    maybe_get_ax,
)


def plot_latwiss(
    madx: Madx,
    title: Optional[str] = None,
    xoffset: float = 0,
    xlimits: Tuple[float, float] = None,
    plot_dipoles: bool = True,
    plot_dipole_k1: bool = False,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    disp_ylim: Tuple[float, float] = None,
    beta_ylim: Tuple[float, float] = None,
    k0l_lim: Tuple[float, float] = None,
    k1l_lim: Tuple[float, float] = None,
    k2l_lim: Tuple[float, float] = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Creates a plot on the current figure (`~matplotlib.pyplot.gcf`) representing the lattice layout and
    the :math:`\\beta`-functions along with the horizontal dispertion function. This is a *very, very heavily
    refactored* version of an initial implementation by :user:`Guido Sterbini <sterbini>`. One can find
    example uses of this function in the :ref:`machine lattice <demo-accelerator-lattice>` example gallery.

    .. note::
        This function has some heavy logic behind it, especially in how it needs to order several axes. The
        easiest way to go about using it is to manually create and empty figure with the desired properties
        (size, etc) then call this function. See the example below or the gallery for more details.

    .. important::
        At the moment, it is important to give this function symmetric limits for the ``k0l_lim``, ``k1l_lim``
        and ``k2l_lim`` arguments. Otherwise the element patches will show up vertically displaced from the
        axis' center line.

    .. warning::
        Currently the function tries to plot legends for the different layout patches. The position of the
        different legends has been hardcoded in corners and might require users to tweak the axis limits
        (through ``k0l_lim``, ``k1l_lim`` and ``k2l_lim``) to ensure legend labels and plotted elements don't
        overlap.

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
            Defaults to `None`.
        beta_ylim (Tuple[float, float]): vertical axis limits for the betatron function values.
            Defaults to None, to be determined by matplotlib based on the provided beta values.
        k0l_lim (Tuple[float, float]): vertical axis limits for the ``k0l`` values used for the
            height of dipole patches. Defaults to `None`.
        k1l_lim (Tuple[float, float]): vertical axis limits for the ``k1l`` values used for the
            height of quadrupole patches. Defaults to `None`.
        k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
            the figure, and the provided values act as vertical axis limits for the k2l values used for the
            height of sextupole patches.
        **kwargs: any keyword argument will be transmitted to `~.plotting.utils.plot_machine_layout`, later on
            to `~.plotting.utils._plot_lattice_series`, and then `~matplotlib.patches.Rectangle`, such as ``lw`` etc.

    Example:
        .. code-block:: python

            >>> title = "Machine Layout"
            >>> plt.figure(figsize=(16, 11))
            >>> plot_latwiss(
            ...     madx,
                    title=title,
                    k0l_lim=(-0.15, 0.15),
                    k1l_lim=(-0.08, 0.08),
                    disp_ylim=(-10, 125),
                    lw=3,
            ... )
    """
    # pylint: disable=too-many-arguments
    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    logger.debug("Plotting optics functions and machine layout")
    twiss_df = _get_twiss_table_with_offsets_and_limits(madx, xoffset, xlimits)
    xlimits = (twiss_df.s.min(), twiss_df.s.max()) if xlimits is None else xlimits

    # Create a subplot for the lattice patches (takes a third of figure)
    figure = plt.gcf()
    quadrupole_patches_axis = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
    plot_machine_layout(
        madx,
        axis=quadrupole_patches_axis,
        title=title,
        xoffset=xoffset,
        xlimits=xlimits,
        plot_dipoles=plot_dipoles,
        plot_dipole_k1=plot_dipole_k1,
        plot_quadrupoles=plot_quadrupoles,
        plot_bpms=plot_bpms,
        k0l_lim=k0l_lim,
        k1l_lim=k1l_lim,
        k2l_lim=k2l_lim,
        **kwargs,
    )

    # Plotting beta functions on remaining two thirds of the figure
    logger.debug("Plotting beta functions")
    betatron_axis = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=quadrupole_patches_axis)
    betatron_axis.plot(twiss_df.s, twiss_df.betx, label="$\\beta_x$")
    betatron_axis.plot(twiss_df.s, twiss_df.bety, label="$\\beta_y$")
    betatron_axis.legend(loc=2)
    betatron_axis.set_ylabel("$\\beta_{x,y}$ $[m]$")
    betatron_axis.set_xlabel("$S$ $[m]$")

    logger.debug("Plotting dispersion functions")
    dispertion_axis = betatron_axis.twinx()
    dispertion_axis.plot(twiss_df.s, twiss_df.dx, color="brown", label="$D_x$")
    dispertion_axis.plot(twiss_df.s, twiss_df.dy, ls="-.", color="sienna", label="$D_y$")
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


def plot_machine_survey(
    madx: Madx,
    title: str = None,
    show_elements: bool = False,
    high_orders: bool = False,
    **kwargs,
) -> matplotlib.axes.Axes:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing the lattice layout and the machine geometry in 2D. This is a very,
    very heavily refactored version of an initial implementation by :user:`Guido Sterbini <sterbini>`.
    One can find an example use of this function in the :ref:`machine survey <demo-machine-survey>`
    example gallery.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        title (Optional[str]): if provided, is set as title of the plot. Defaults to `None`.
        show_elements (bool): if `True`, will try to plot by differentiating elements.
            Defaults to `False`.
        high_orders (bool): if `True`, plots sextupoles and octupoles if *show_elements* is `True`,
            otherwise only up to quadrupoles. Defaults to `False`.
        **kwargs: any keyword argument will be transmitted to `~matplotlib.pyplot.scatter` calls
            later on. If either `ax` or `axis` is found in the kwargs, the corresponding value is
            used as the axis object to plot on.

    Returns:
        The `~matplotlib.axes.Axes` on which the survey is drawn.

    Example:
        .. code-block:: python

            >>> fig, ax = plt.subplots(figsize=(6, 6))
            >>> plot_machine_survey(
            ...     madx, title="Machine Survey", show_elements=True, high_orders=True
            ... )
    """
    logger.debug("Plotting machine survey")
    logger.trace("Getting machine survey from cpymad")
    madx.command.survey()
    survey = madx.table.survey.dframe()

    axis, kwargs = maybe_get_ax(**kwargs)

    if show_elements:
        logger.debug("Plotting survey with elements differentiation")
        element_dfs = make_survey_groups(madx)
        plt.scatter(
            element_dfs["dipoles"].z,
            element_dfs["dipoles"].x,
            marker=".",
            c=element_dfs["dipoles"].s,
            label="Dipoles",
            **kwargs,
        )
        plt.scatter(element_dfs["quad_foc"].z, element_dfs["quad_foc"].x, marker="o", color="blue", label="QF")
        plt.scatter(element_dfs["quad_defoc"].z, element_dfs["quad_defoc"].x, marker="o", color="red", label="QD")

        if high_orders:
            logger.debug("Plotting high order magnetic elements (up to octupoles)")
            plt.scatter(element_dfs["sextupoles"].z, element_dfs["sextupoles"].x, marker=".", color="m", label="MS")
            plt.scatter(element_dfs["octupoles"].z, element_dfs["octupoles"].x, marker=".", color="cyan", label="MO")
        plt.legend(loc=2)

    else:
        logger.debug("Plotting survey without elements differentiation")
        plt.scatter(survey.z, survey.x, c=survey.s, marker=".", **kwargs)

    # Trying a trick to ensure the colorbar scales values properly up to the max S value and not 1
    logger.trace("Plotting trick invisible data to re-scale colorbar")
    plt.scatter(survey.z, survey.x, c=survey.s, marker="", **kwargs)
    plt.colorbar(label=r"$S \ [m]$")

    plt.axis("equal")
    axis.set_xlabel(r"$Z \ [m]$")
    axis.set_ylabel(r"$X \ [m]$")
    axis.set_title(title)

    return axis
