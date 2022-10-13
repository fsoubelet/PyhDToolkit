"""
.. _plotting-aperture:

Aperture Plotters
-----------------

Module with functions to create aperture plots through a `~cpymad.madx.Madx` object.
"""
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.plotting.layout import plot_machine_layout


def plot_aperture(
    madx: Madx,
    title: Optional[str] = None,
    xoffset: float = 0,
    xlimits: Tuple[float, float] = None,
    plot_dipoles: bool = True,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    aperture_ylim: Tuple[float, float] = None,
    k0l_lim: Tuple[float, float] = None,
    k1l_lim: Tuple[float, float] = None,
    k2l_lim: Tuple[float, float] = None,
    color: str = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing nicely the lattice layout and the aperture tolerance across the machine.
    One can find an example use of this function in the :ref:`machine aperture <demo-accelerator-aperture>`
    example gallery.

    .. important::
        This function assumes the user has previously made a call to the ``APERTURE`` command in ``MAD-X``,
        as it will query relevant values from the ``aperture`` table.

    .. note::
        This function has some heavy logic behind it, especially in how it needs to order several axes. The
        easiest way to go about using it is to manually create and empty figure with the desired properties
        (size, etc) then call this function. See the example below or the gallery for more details.

    .. warning::
        Currently the function tries to plot legends for the different layout patches. The position of the
        different legends has been hardcoded in corners and might require users to tweak the axis limits
        (through ``k0l_lim``, ``k1l_lim`` and ``k2l_lim``) to ensure legend labels and plotted elements don't
        overlap.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        title (Optional[str]): title of the figure.
        xoffset (float): An offset applied to the ``S`` coordinate before plotting. This is useful if
            you want to center a plot around a specific point or element, which would then become located
            at :math:`s = 0`. Beware this offset is applied before applying the *xlimits*. Defaults to 0.
        xlimits (Tuple[float, float]): will implement xlim (for the ``s`` coordinate) if this is
            not ``None``, using the tuple passed.
        plot_dipoles (bool): if `True`, dipole patches will be plotted on the layout subplot of
            the figure. Defaults to `True`. Dipoles are plotted in blue.
        plot_quadrupoles (bool): if `True`, quadrupole patches will be plotted on the layout
            subplot of the figure. Defaults to `True`. Quadrupoles are plotted in red.
        plot_bpms (bool): if `True`, additional patches will be plotted on the layout subplot to
            represent Beam Position Monitors. BPMs are plotted in dark grey.
        aperture_ylim (Tuple[float, float]): vertical axis limits for the aperture values. Defaults to
            `None`, to be determined by matplotlib based on the provided values.
        k0l_lim (Tuple[float, float]): vertical axis limits for the ``k0l`` values used for the
            height of dipole patches. Defaults to `None`.
        k1l_lim (Tuple[float, float]): vertical axis limits for the ``k1l`` values used for the
            height of quadrupole patches. Defaults to `None`.
        k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
            the figure, and the provided values act as vertical axis limits for the k2l values used for the
            height of sextupole patches.
        color (str): the color argument given to the aperture lines. Defaults to `None`, in which case
            the first color in your `rcParams`'s cycler will be used.
        **kwargs: any keyword argument will be transmitted to `~.plotting.utils.plot_machine_layout`, later on
            to `~.plotting.utils._plot_lattice_series`, and then `~matplotlib.patches.Rectangle`, such as ``lw`` etc.

    Example:
        .. code-block:: python

            >>> plt.figure(figsize=(16, 11))
            >>> plot_aperture(
            ...     madx, plot_bpms=True,
            ...     aperture_ylim=(0, 20),
            ...     k0l_lim=(-4e-4, 4e-4),
            ...     k1l_lim=(-0.08, 0.08),
            ...     color="darkslateblue",
            ... )
    """
    # pylint: disable=too-many-arguments
    logger.debug("Plotting aperture limits and machine layout")
    logger.debug("Getting Twiss dataframe from cpymad")
    madx.command.twiss(centre=True)
    twiss_df: pd.DataFrame = madx.table.twiss.dframe().copy()
    aperture_df = pd.DataFrame.from_dict(dict(madx.table.aperture))  # slicing -> issues with .dframe()

    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    twiss_df.s = twiss_df.s - xoffset
    aperture_df.s = aperture_df.s - xoffset
    xlimits = (twiss_df.s.min(), twiss_df.s.max()) if xlimits is None else xlimits
    twiss_df = twiss_df[twiss_df.s.between(*xlimits)] if xlimits else twiss_df
    aperture_df = aperture_df[aperture_df.s.between(*xlimits)] if xlimits else aperture_df

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
        plot_quadrupoles=plot_quadrupoles,
        plot_bpms=plot_bpms,
        k0l_lim=k0l_lim,
        k1l_lim=k1l_lim,
        k2l_lim=k2l_lim,
        **kwargs,
    )

    # Plotting aperture values on remaining two thirds of the figure
    logger.debug("Plotting aperture values")
    aperture_axis = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=quadrupole_patches_axis)
    aperture_axis.plot(aperture_df.s, aperture_df.n1, marker=".", ls="-", lw=0.8, color=color, label="Aperture Limits")
    aperture_axis.fill_between(aperture_df.s, aperture_df.n1, aperture_df.n1.max(), interpolate=True, color=color)
    aperture_axis.legend()
    aperture_axis.set_ylabel(r"$n_{1} \ [\sigma]$")
    aperture_axis.set_xlabel(r"$S \ [m]$")

    if aperture_ylim:
        logger.debug("Setting ylim for aperture plot")
        aperture_axis.set_ylim(aperture_ylim)

    if xlimits:
        logger.debug("Setting xlim for longitudinal coordinate")
        plt.xlim(xlimits)
