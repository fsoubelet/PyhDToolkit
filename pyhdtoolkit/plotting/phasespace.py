"""
.. _plotting-phasespace:

Phase Space Plotters
--------------------

Module with functions to create phase space
plots through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from loguru import logger
from matplotlib import colors as mcolors

from pyhdtoolkit.optics.twiss import courant_snyder_transform
from pyhdtoolkit.plotting.utils import maybe_get_ax

if TYPE_CHECKING:
    from cpymad.madx import Madx
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

COLORS_DICT = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
BY_HSV = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name) for name, color in COLORS_DICT.items())
SORTED_COLORS = [name for hsv, name in BY_HSV]


def plot_courant_snyder_phase_space(
    madx: Madx,
    /,
    u_coordinates: np.ndarray,
    pu_coordinates: np.ndarray,
    plane: str = "Horizontal",
    title: str | None = None,
    **kwargs,
) -> Axes:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing the normalized Courant-Snyder phase
    space of a particle distribution when provided by position and
    momentum coordinates for a specific plane. One can find an example
    use of this function in the :ref:`phase space <demo-phase-space>`
    example gallery.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    u_coordinates : numpy.ndarray
        A `~numpy.ndarray` of particles' coordinates for the given plane.
        Here ``u_coordinates[0]`` should be the tracked coordinates for the
        first particle and so on.
    pu_coordinates : numpy.ndarray
        A `~numpy.ndarray` of particles' momentum coordinates for the given
        plane. Here ``pu_coordinates[0]`` should be the tracked momenta for
        the first particle and so on.
    plane : str
        The physical plane to plot, should be either ``horizontal`` or
        `vertical``, case insensitive. Defaults to ``horizontal``.
    title : str, optional
        If provided, is set as title of the plot.
    **kwargs
        If either `ax` or `axis` is found in the kwargs, the corresponding
        value is used as the axis object to plot on.

    Returns
    -------
    matplotlib.axes.Axes
            The `~matplotlib.axes.Axes` on which the phase space is drawn.

    Example
    -------
        .. code-block:: python

            fig, ax = plt.subplots(figsize=(10, 9))
            plot_courant_snyder_phase_space(madx, x_coords, px_coords, plane="Horizontal")
    """
    if plane.lower() not in ("horizontal", "vertical"):
        logger.error(f"Plane should be either Horizontal or Vertical but '{plane}' was given")
        msg = "Invalid 'plane' argument."
        raise ValueError(msg)

    logger.debug("Plotting phase space for normalized Courant-Snyder coordinates")
    axis, kwargs = maybe_get_ax(**kwargs)
    axis.set_title(title)

    # Getting the twiss parameters for the P matrix to compute Courant-Snyder coordinates
    logger.debug("Getting Twiss functions from MAD-X")
    alpha = madx.table.twiss.alfx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.alfy[0]
    beta = madx.table.twiss.betx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.bety[0]

    logger.debug(f"Plotting phase space for the {plane.lower()} plane")
    for index, _ in enumerate(u_coordinates):
        logger.trace(f"Getting and plotting Courant-Snyder coordinates for particle {index}")
        u = np.array([u_coordinates[index], pu_coordinates[index]])
        u_bar = courant_snyder_transform(u, alpha, beta)
        axis.scatter(u_bar[0, :], u_bar[1, :], s=0.1, c="k")
        if plane.upper() == "HORIZONTAL":
            axis.set_xlabel(r"$\bar{x} \ [m]$")
            axis.set_ylabel(r"$\bar{px} \ [rad]$")
        else:
            axis.set_xlabel(r"$\bar{y} \ [m]$")
            axis.set_ylabel(r"$\bar{py} \ [rad]$")

    return axis


def plot_courant_snyder_phase_space_colored(
    madx: Madx,
    /,
    u_coordinates: np.ndarray,
    pu_coordinates: np.ndarray,
    plane: str = "Horizontal",
    title: str | None = None,
    **kwargs,
) -> Figure:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing the normalized Courant-Snyder phase
    space of a particle distribution when provided by position and
    momentum coordinates for a specific plane. Each single particle
    trajectory has its own color on the plot, within the limit of
    `~matplotlib.pyplot`'s 156 named colors, after which the colors
    loop back to the first entry again. One can find an example use
    of this function in the :ref:`phase space <demo-phase-space>`
    example gallery.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    u_coordinates : numpy.ndarray
        A `~numpy.ndarray` of particles' coordinates for the given plane.
        Here ``u_coordinates[0]`` should be the tracked coordinates for the
        first particle and so on.
    pu_coordinates : numpy.ndarray
        A `~numpy.ndarray` of particles' momentum coordinates for the given
        plane. Here ``pu_coordinates[0]`` should be the tracked momenta for
        the first particle and so on.
    plane : str
        The physical plane to plot, should be either ``horizontal`` or
        `vertical``, case insensitive. Defaults to ``horizontal``.
    title : str, optional
        If provided, is set as title of the plot.
    **kwargs
        If either `ax` or `axis` is found in the kwargs, the corresponding
        value is used as the axis object to plot on.

    Returns
    -------
    matplotlib.axes.Axes
            The `~matplotlib.axes.Axes` on which the phase space is drawn.

    Example
    -------
        .. code-block:: python

            fig, ax = plt.subplots(figsize=(10, 9))
            plot_courant_snyder_phase_space_colored(
                madx, x_coords, px_coords, plane="Horizontal"
            )
    """
    if plane.upper() not in ("HORIZONTAL", "VERTICAL"):
        logger.error(f"Plane should be either horizontal or vertical but '{plane}' was given")
        msg = "Invalid 'plane' argument."
        raise ValueError(msg)

    # Getting a sufficiently long array of colors to use
    colors = int(np.floor(len(u_coordinates) / 100)) * SORTED_COLORS
    while len(colors) > len(u_coordinates):
        colors.pop()

    logger.debug("Plotting colored phase space for normalized Courant-Snyder coordinates")
    axis, kwargs = maybe_get_ax(**kwargs)
    axis.set_title(title)

    # Getting the twiss parameters for the P matrix to compute Courant-Snyder coordinates
    logger.debug("Getting Twiss functions from MAD-X")
    alpha = madx.table.twiss.alfx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.alfy[0]
    beta = madx.table.twiss.betx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.bety[0]

    logger.debug(f"Plotting colored phase space for the {plane.lower()} plane")
    for index, _ in enumerate(u_coordinates):
        logger.trace(f"Getting and plotting Courant-Snyder coordinates for particle {index}")
        u = np.array([u_coordinates[index], pu_coordinates[index]])
        u_bar = courant_snyder_transform(u, alpha, beta)
        axis.scatter(u_bar[0, :], u_bar[1, :], s=0.1, c=colors[index])
        if plane.upper() == "HORIZONTAL":
            axis.set_xlabel(r"$\bar{x} \ [m]$")
            axis.set_ylabel(r"$\bar{px} \ [rad]$")
        else:
            axis.set_xlabel(r"$\bar{y} \ [m]$")
            axis.set_ylabel(r"$\bar{py} \ [rad]$")

    return axis
