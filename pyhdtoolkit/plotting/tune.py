"""
.. _plotting-tune:

Tune Diagram Plotters
---------------------

Module with functions to create tune diagram plots.
These provide functionality to draw Farey sequences
up to a desired order.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from loguru import logger

from pyhdtoolkit.plotting.utils import maybe_get_ax

if TYPE_CHECKING:
    from matplotlib.axes import Axes


ORDER_TO_ALPHA: dict[int, float] = {1: 1, 2: 0.75, 3: 0.65, 4: 0.55, 5: 0.45, 6: 0.35}
ORDER_TO_RGB: dict[int, np.ndarray] = {
    1: np.array([152, 52, 48]) / 255,  # a brown
    2: np.array([57, 119, 175]) / 255,  # a blue
    3: np.array([239, 133, 54]) / 255,  # an orange
    4: np.array([82, 157, 62]) / 255,  # a green
    5: np.array([197, 57, 50]) / 255,  # a red
    6: np.array([141, 107, 184]) / 255,  # a purple
}
ORDER_TO_LINESTYLE: dict[int, str] = {
    1: "solid",
    2: "solid",
    3: "solid",
    4: "dashed",
    5: "dashed",
    6: "dashed",
}
ORDER_TO_LINEWIDTH: dict[int, float] = {1: 2, 2: 1.75, 3: 1.5, 4: 1.25, 5: 1, 6: 0.75}
ORDER_TO_LABEL: dict[int, str] = {
    1: "1st order",
    2: "2nd order",
    3: "3rd order",
    4: "4th order",
    5: "5th order",
    6: "6th order",
}


def farey_sequence(order: int) -> list[tuple[int, int]]:
    """
    .. versionadded:: 1.0.0

    Returns the n-th farey_sequence sequence, ascending, where
    n is the provided *order*. Original code from :user:`Rogelio
    Tomás <rogeliotomas>` (see Numerical Methods 2018 CAS
    proceedings, :cite:t:`Tomas:CASImperfections:2018`).

    Parameters
    ----------
    order : int
        The order up to which we want to calculate the sequence.

    Returns
    -------
    list[tuple[int, int]]
        The sequence as a `list` of plottable 2D points.
    """
    seq = [(0, 1)]
    a, b, c, d = 0, 1, 1, order
    while c <= order:
        k = int((order + b) / d)
        a, b, c, d = c, d, k * c - a, k * d - b
        seq.append((a, b))
    return seq


def plot_tune_diagram(
    title: str | None = None,
    legend_title: str | None = None,
    max_order: int = 6,
    differentiate_orders: bool = False,
    **kwargs,
) -> Axes:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing the tune diagram up to the given
    *max_order*. One can find an example use of this function in
    the :ref:`tune diagram <demo-tune-diagram>` example gallery.

    Note
    ----
        The first order lines make up the
        [(0, 0), (0, 1), (1, 1), (1, 0)] square and will only be
        seen when redefining the limits of the figure, which are
        by default [0, 1] on each axis.

    Parameters
    ----------
    title : str, optional
        If provided, is set as title of the plot.
    legend_title : str, optional
        If given, will be used as the title of the plot's legend.
    max_order : int
        The order up to which to plot resonance lines for. This
        parameter value should not exceed 6. Defaults to 6.
    differentiate_orders : bool
        If `True`, the lines for each order will be of a different
        color. When set to `False`, there is still differentation
        through ``alpha``, ``linewidth`` and ``linestyle``. Defaults
        to `False`.
    **kwargs
        Any keyword argument is given to `~matplotlib.pyplot.plot`.
        Be aware that ``alpha``, ``ls``, ``lw``, ``color`` and ``label``
        are already set by this function and providing them as kwargs
        might lead to errors. If either `ax` or `axis` is found in the
        kwargs, the corresponding value is used as the axis object to
        plot on.

    Returns
    -------
    matplotlib.axes.Axes
            The `~matplotlib.axes.Axes` on which the tune diagram is drawn.

    Raises
    ------
    ValueError
        If the *max_order* is not between 1 and 6, included.

    Example
    -------
        .. code-block:: python

            fig, ax = plt.subplots(figsize=(6, 6))
            plot_tune_diagram(ax=ax, max_order=4, differentiate_orders=True)
    """
    if max_order > 6 or max_order < 1:  # noqa: PLR2004
        logger.error("Plotting is not supported outside of 1st-6th order (and not recommended)")
        msg = "The 'max_order' argument should be between 1 and 6 included"
        raise ValueError(msg)

    logger.debug(f"Plotting resonance lines up to {ORDER_TO_LABEL[max_order]}")
    axis, kwargs = maybe_get_ax(**kwargs)

    for order in range(max_order, 0, -1):  # high -> low so most importants ones (low) are plotted on top
        alpha, ls, lw, rgb = (
            ORDER_TO_ALPHA[order],
            ORDER_TO_LINESTYLE[order],
            ORDER_TO_LINEWIDTH[order],
            ORDER_TO_RGB[order] if differentiate_orders is True else "blue",
        )
        plot_resonance_lines_for_order(order, axis, alpha=alpha, ls=ls, lw=lw, color=rgb, **kwargs)

    axis.set_title(title)
    axis.set_xlim([0, 1])
    axis.set_ylim([0, 1])
    axis.set_xlabel("$Q_{x}$")
    axis.set_ylabel("$Q_{y}$")

    if legend_title is not None:
        logger.debug("Adding legend with given title")
        axis.legend(title=legend_title)
    return axis


def plot_resonance_lines_for_order(order: int, axis: Axes, **kwargs) -> None:
    """
    .. versionadded:: 1.0.0

    Plot resonance lines from farey sequences of the given
    *order* on the provided `~matplotlib.axes.Axes`.

    Parameters
    ----------
    order : int
        The order of the resonance.
    axis : matplotlib.axes.Axes
        The `~matplotlib.axes.Axes` on which to plot the resonance
        lines.
    **kwargs
        Any keyword argument is given to `~matplotlib.axes.Axes.plot`.

    Example
    -------
        .. code-block:: python

            fig, ax = plt.subplots(figsize=(6, 6))
            plot_resonance_lines_for_order(order=3, axis=ax, color="blue")
    """
    order_label = ORDER_TO_LABEL[order]
    logger.debug(f"Plotting {order_label} resonance lines")
    axis.plot([], [], label=order_label, **kwargs)  # to avoid legend duplication in loops below

    x = np.linspace(0, 1, 1000)
    y = np.linspace(0, 1, 1000)
    farey_sequences = farey_sequence(order)
    clip = partial(np.clip, a_min=0, a_max=1)  # clip all values to plot to [0, 1]

    for node in farey_sequences:
        h, k = node  # Node h/k on the axes
        for sequence in farey_sequences:
            p, q = sequence
            a = float(k * p)  # Resonance line a*Qx + b*Qy = c (linked to p/q)
            if a > 0:
                b, c = float(q - k * p), float(p * h)
                axis.plot(x, clip(c / a - x * b / a), **kwargs)
                axis.plot(x, clip(c / a + x * b / a), **kwargs)
                axis.plot(clip(c / a - x * b / a), y, **kwargs)
                axis.plot(clip(c / a + x * b / a), y, **kwargs)
                axis.plot(clip(c / a - x * b / a), 1 - y, **kwargs)
                axis.plot(clip(c / a + x * b / a), 1 - y, **kwargs)
            if q == k and p == 1:  # FN elements below 1/k
                break
