"""
Module plotting.helpers
-----------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for more descriptive plots.
"""
from typing import Tuple

import matplotlib.axes


class AnnotationsPlotter:
    """
    A class to encapsulate all useful plotting additional tidbits.
    """

    @staticmethod
    def set_arrow_label(
        axis: matplotlib.axes.Axes,
        label: str,
        arrow_position: Tuple[float, float],
        label_position: Tuple[float, float],
        color: str = "k",
        arrow_arc_rad: float = -0.2,
        fontsize: int = 20,
    ) -> matplotlib.text.Annotation:
        """
        Add a label box with text and an arrow from the box to a specified position to an existing
        provided matplotlib.axes `Axes` instance. Original code from Guido Sterbini.

        Args:
            axis (matplotlib.axes.Axes): a matplotlib axis to plot on.
            label (str): label text to print on the axis.
            arrow_position (Tuple[float, float]): where on the plot to point the tip of the arrow.
            label_position (Tuple[float, float]): where on the plot the text label (and thus start
                of the arrow) is.
            color (str): color parameter for your arrow and label. Defaults to 'k'.
            arrow_arc_rad (float): angle value defining the upwards / downwards shape of and
                bending of the arrow.
            fontsize (int): text size in the box

        Returns:
            A matploblit text annotation object.
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
                arrowstyle="-|>", connectionstyle="arc3,rad=" + str(arrow_arc_rad), fc="w", color=color, lw=2,
            ),
        )
