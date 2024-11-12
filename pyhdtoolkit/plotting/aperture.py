"""
.. _plotting-aperture:

Aperture Plotters
-----------------

Module with functions to create aperture plots
through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from loguru import logger

from pyhdtoolkit.plotting.layout import plot_machine_layout
from pyhdtoolkit.plotting.utils import maybe_get_ax

if TYPE_CHECKING:
    from cpymad.madx import Madx


def plot_aperture(
    madx: Madx,
    /,
    title: str | None = None,
    xoffset: float = 0,
    xlimits: tuple[float, float] | None = None,
    plot_dipoles: bool = True,
    plot_dipole_k1: bool = False,
    plot_quadrupoles: bool = True,
    plot_bpms: bool = False,
    aperture_ylim: tuple[float, float] | None = None,
    k0l_lim: tuple[float, float] | float | None = None,
    k1l_lim: tuple[float, float] | float | None = None,
    k2l_lim: tuple[float, float] | float | None = None,
    k3l_lim: tuple[float, float] | float | None = None,
    color: str | None = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing the lattice layout and the aperture
    tolerance across the machine. The tolerance is based on the ``n1``
    values in the aperture table. One can find an example use of this
    function in the :ref:`machine aperture <demo-accelerator-aperture>`
    example gallery.

    Important
    ---------
        This function assumes the user has previously made a call to the
        ``APERTURE`` command in ``MAD-X``, as it will query relevant values
        from the ``aperture`` table.

    Note
    ----
        This function has some heavy logic behind it, especially in how it
        needs to order several axes. The easiest way to go about using it is
        to manually create and empty figure with the desired properties (size,
        etc) then call this function. See the example below or the gallery for
        more details.

    Warning
    -------
        Currently the function tries to plot legends for the different layout
        patches. The position of the different legends has been hardcoded in
        corners and might require users to tweak the axis limits (through
        ``k0l_lim``, ``k1l_lim`` and ``k2l_lim``) to ensure legend labels and
        plotted elements don't overlap.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    title : str, optional
        Title of the figure.
    xoffset : float
        An offset applied to the ``S`` coordinate before plotting.
        This is useful if you want to center a plot around a specific
        point or element, which would then become located at exactly
        :math:`s = 0`. Beware this offset is applied before applying
        the *xlimits*. Defaults to 0.
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
    aperture_ylim : tuple[float, float], optional
        If given, will be used as vertical axis limits for the aperture
        values. Defaults to `None`, to be determined by matplotlib based
        on the provided values.
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
    color : str, optional
        The color argument given to the aperture lines. Defaults to `None`,
        in which case the first color found in your `rcParams`'s cycler will
        be used.
    **kwargs
        Any keyword argument will be transmitted to
        `~.plotting.utils.plot_machine_layout`, later on to
        `~.plotting.utils._plot_lattice_series`, and then
        `~matplotlib.patches.Rectangle`, such as ``lw`` etc.

    Example
    -------
        .. code-block:: python

            plt.figure(figsize=(16, 11))
            plot_aperture(
                madx,
                plot_bpms=True,
                aperture_ylim=(0, 20),
                k0l_lim=(-4e-4, 4e-4),
                k1l_lim=(-0.08, 0.08),
                color="darkslateblue",
            )
    """
    # pylint: disable=too-many-arguments
    logger.debug("Plotting aperture limits and machine layout")
    logger.debug("Getting Twiss dataframe from cpymad")
    madx.command.twiss(centre=True)
    twiss_df: pd.DataFrame = madx.table.twiss.dframe()
    aperture_df = pd.DataFrame.from_dict(dict(madx.table.aperture))  # slicing -> issues with .dframe()

    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    twiss_df.s = twiss_df.s - xoffset
    aperture_df.s = aperture_df.s - xoffset
    xlimits = (twiss_df.s.min(), twiss_df.s.max()) if xlimits is None else xlimits
    twiss_df = twiss_df[twiss_df.s.between(*xlimits)] if xlimits else twiss_df
    aperture_df = aperture_df[aperture_df.s.between(*xlimits)] if xlimits else aperture_df

    # Create a subplot for the lattice patches (takes a third of figure)
    # figure = plt.gcf()
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
        k3l_lim=k3l_lim,
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


def plot_physical_apertures(
    madx,
    /,
    plane: str,
    scale: float = 1,
    xoffset: float = 0,
    xlimits: tuple[float, float] | None = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.2.0

    Determine and plot the "real" physical apertures of elements in the
    sequence. A data point is extrapolated at the beginning and the end
    of each element, with values based on the ``aper_1`` and ``aper_2``
    columns in the ``TWISS`` table. One can find an example use of this
    function in the :ref:`machine aperture <demo-accelerator-aperture>`
    example gallery. Original code from :user:`Elias Waagaard <ewaagaard>`.

    Important
    ---------
        This function assumes the user has previously made a call to the
        ``APERTURE`` command in ``MAD-X``, as it will query relevant values
        from the ``aperture`` table.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    plane : str
        The physical plane to plot for, Accepted values are either `x`,
        `horizontal`, `y` or `vertical`. Case insensitive.
    scale : float
        A scaling factor to apply to the beam orbit and beam enveloppe,
        for the user to adjust to their wanted scale. Defaults to 1
        (meaning values are assumed in [m]).
    xoffset : float
        An offset applied to the ``S`` coordinate before plotting.
        This is useful if you want to center a plot around a specific
        point or element, which would then become located at exactly
        :math:`s = 0`. Beware this offset is applied before applying
        the *xlimits*. Defaults to 0.
    xlimits : tuple[float, float], optional
        If given, will be used for the xlim (for the ``s`` coordinate),
        using the tuple passed.
    **kwargs
        Any keyword argument that can be given to the ``MAD-X`` ``TWISS``
        command. If either `ax` or `axis` is found in the kwargs, the
        corresponding value is used as the axis object to plot on.

    Raises
    ------
    ValueError
        If the *plane* argument is not one of `x`, `horizontal`, `y` or
        `vertical`.

    Examples
    --------

        .. code-block:: python

            fig, ax = plt.subplots(figsize=(10, 9))
            plot_physical_apertures(madx, "x")
            plt.show()

        In order to do the same plot but have all values in millimeters:

        .. code-block:: python

            fig, ax = plt.subplots(figsize=(10, 9))
            plot_physical_apertures(madx, "x", scale=1e3)
            plt.setp(ax, xlabel="S [m]", ylabel="X [mm]")
            plt.show()
    """
    # pylint: disable=too-many-arguments
    if plane.lower() not in ("x", "y", "horizontal", "vertical"):
        logger.error(f"'plane' argument should be 'x', 'horizontal', 'y' or 'vertical' not '{plane}'")
        msg = "Invalid 'plane' argument."
        raise ValueError(msg)

    logger.debug("Plotting real element apertures")
    axis, kwargs = maybe_get_ax(**kwargs)

    positions, apertures = _get_positions_and_real_apertures(madx, plane, xlimits=xlimits, **kwargs)
    logger.trace(f"Applying scale ({scale}) and offset ({xoffset})")
    positions = positions - xoffset
    apertures = apertures * scale

    logger.trace("Plotting apertures")
    # previously drawstyle="steps", but do not use if entry and exit aperture offset differs
    axis.fill_between(positions, apertures, 0.2 * scale, color="black", alpha=0.4, label="_nolegend_")
    axis.fill_between(positions, -1 * apertures, -0.2 * scale, color="black", alpha=0.4, label="_nolegend_")
    axis.plot(positions, apertures, "k", label="_nolegend_")
    axis.plot(positions, -1 * apertures, "k", label="_nolegend_")

    if xlimits:
        logger.trace("Setting xlim for longitudinal coordinate")
        axis.set_xlim(xlimits)


# ----- Helpers ----- #


def _get_positions_and_real_apertures(
    madx, /, plane: str, xoffset: float = 0, xlimits: tuple[float, float] | None = None, **kwargs
) -> tuple[np.ndarray, np.ndarray]:
    """
    .. versionadded:: 1.2.0

    Determines the "real" physical apertures of elements in the sequence.
    This is done by extrapolating a data point at the beginning and the
    end of each element, with values based on the ``aper_1`` and the
    ``aper_2`` columns in the ``TWISS`` table. Original code from
    :user:`Elias Waagaard <ewaagaard>`.

    Important
    ---------
        This function assumes the user has previously made a call to
        the ``APERTURE`` command in ``MAD-X``, as it will query relevant
        values from the ``aperture`` table.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    plane : str
        The physical plane to plot for, Accepted values are either `x`,
        `horizontal`, `y` or `vertical`. Case insensitive.
    xoffset : float
        An offset applied to the ``S`` coordinate before plotting.
        This is useful if you want to center a plot around a specific
        point or element, which would then become located at exactly
        :math:`s = 0`. Beware this offset is applied before applying
        the *xlimits*. Defaults to 0.
    xlimits : tuple[float, float], optional
        If given, will be used for the xlim (for the ``s`` coordinate),
        using the tuple passed.
    **kwargs
        Any keyword argument that can be given to the ``MAD-X``
        ``TWISS`` command.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        A `~numpy.ndarray` of the longitudinal positions for the data
        points, and another `~numpy.ndarray` with the physical aperture
        values at these positions.
    """
    logger.debug("Getting Twiss dframe from MAD-X")
    madx.command.select(flag="twiss", column=["aper_1", "aper_2"])  # make sure we to get these two
    twiss_df = madx.twiss(**kwargs).dframe()
    madx.command.select(flag="twiss", clear=True)  # clean up
    twiss_df.s = twiss_df.s - xoffset

    logger.trace("Determining aperture column to use")
    plane_number = 1 if plane.lower() in ("x", "horizontal") else 2
    apercol = f"aper_{plane_number:d}"

    if xlimits is not None:
        twiss_df = twiss_df[twiss_df.s.between(*xlimits)]

    # Initiate arrays for new aperture and positions,
    # these need to be lists as we will insert elements
    new_aper = twiss_df[apercol].tolist()
    new_pos = twiss_df.s.tolist()
    indices = []

    logger.trace("Finding non-zero aperture elements")
    for i in range(len(twiss_df[apercol]) - 1, 0, -1):
        if twiss_df[apercol].iloc[i] != 0:
            new_aper.insert(i, twiss_df[apercol].iloc[i])
            indices.append(i)
    indices = list(reversed(indices))

    logger.trace("Extrapolating data at beginning of elements")
    # counter keeps track of exact position in new array with counter
    for counter, j in enumerate(indices):
        new_pos.insert(j + counter, (twiss_df.s.iloc[j] - twiss_df.l.iloc[j]))

    # Replace all zeros with Nan
    apertures = np.array(new_aper)
    apertures[apertures == 0] = np.nan
    positions = np.array(new_pos)
    return positions, apertures
