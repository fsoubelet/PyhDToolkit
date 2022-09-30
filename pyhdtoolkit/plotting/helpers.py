"""
.. _plotting-helpers:

Plotting Helpers
----------------

A collection of utility functions for more descriptive plots.
"""
from typing import Tuple

import matplotlib.axes
import matplotlib.pyplot as plt

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


# ------ Plotting Utilities ----- #


def set_arrow_label(
    axis: matplotlib.axes.Axes,
    label: str,
    arrow_position: Tuple[float, float],
    label_position: Tuple[float, float],
    color: str = "k",
    arrow_arc_rad: float = -0.2,
    fontsize: int = 20,
    **kwargs,
) -> matplotlib.text.Annotation:
    """
    .. versionadded:: 0.6.0

    Adds on the provided `matplotlib.axes.Axes` a label box with text and an arrow from the box to a specified position.
    Original code from :user:`Guido Sterbini <sterbini>`.

    Args:
        axis (matplotlib.axes.Axes): a `matplotlib.axes.Axes` to plot on.
        label (str): label text to print on the axis.
        arrow_position (Tuple[float, float]): where on the plot to point the tip of the arrow.
        label_position (Tuple[float, float]): where on the plot the text label (and thus start
            of the arrow) is.
        color (str): color parameter for your arrow and label. Defaults to "k".
        arrow_arc_rad (float): angle value defining the upwards / downwards shape of and
            bending of the arrow.
        fontsize (int): text size in the box.

    Returns:
        A `matploblit.text.Annotation` of the created annotation.

    Example:
        .. code-block:: python

            >>> set_arrow_label(
            ...     axis=ax,
            ...     label="Your label",
            ...     arrow_position=(1, 2),
            ...     label_position=(1.1 * some_value, 0.75 * another_value),
            ...     color="indianred",
            ...     arrow_arc_rad=0.3,
            ...     fontsize=25,
            ... )
    """
    # TODO: use maybe_get_ax
    return axis.annotate(
        label,
        xy=arrow_position,
        xycoords="data",
        xytext=label_position,
        textcoords="data",
        size=fontsize,
        color=color,
        va="center",
        ha="center",
        bbox=dict(boxstyle="round4", fc="w", color=color, lw=2),
        arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=" + str(arrow_arc_rad), fc="w", color=color, lw=2),
        **kwargs,
    )
