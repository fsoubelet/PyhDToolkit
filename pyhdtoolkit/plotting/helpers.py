"""
Module plotting.helpers
-----------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for more descriptive plots.
"""


class AnnotationsPlotter:
    """
    A class to encapsulate all useful plotting additional tidbits.
    """

    @staticmethod
    def set_arrow_label(
        axis,
        label: str,
        arrow_position: tuple = (0, 0),
        label_position: tuple = (0, 0),
        color: str = "k",
        arrow_arc_rad: float = -0.2,
        fontsize: int = 20,
    ):
        """
        Add a label box with text and an arrow from the box to a specified position to an existing
        provided matplotlib.axes `Axes` instance. Original code from Guido Sterbini.

        Args:
            axis: a matplotlib axis.
            label: label to give to your arrow.
            arrow_position: where the tip of the arrow points.
            label_position: where the text label (and thus start of the arrow) is.
            color: color of your arrow.
            arrow_arc_rad: angle value defining the upwards / downwards shape of the arrow.
            fontsize: text size in the box

        Returns:
            Nothing, plots on the given axis.
        """
        # pylint: disable=too-many-arguments
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
                arrowstyle="-|>",
                connectionstyle="arc3,rad=" + str(arrow_arc_rad),
                fc="w",
                color=color,
                lw=2,
            ),
        )
