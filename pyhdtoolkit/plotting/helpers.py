"""
.. _plotting-helpers:

Plotting Helpers
----------------

A collection of utility functions for more descriptive plots.
"""
from typing import Tuple

import matplotlib.axes


class AnnotationsPlotter:
    """A class to encapsulate all useful plotting additional tidbits."""

    @staticmethod
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

                >>> AnnotationsPlotter.set_arrow_label(
                ...     axis=ax,
                ...     label="Your label",
                ...     arrow_position=(1, 2),
                ...     label_position=(1.1 * some_value, 0.75 * another_value),
                ...     color="indianred",
                ...     arrow_arc_rad=0.3,
                ...     fontsize=25,
                ... )
        """
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
            arrowprops=dict(
                arrowstyle="-|>", connectionstyle="arc3,rad=" + str(arrow_arc_rad), fc="w", color=color, lw=2
            ),
            **kwargs,
        )
