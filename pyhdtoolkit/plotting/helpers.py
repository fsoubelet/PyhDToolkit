"""
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
        axis, label="myLabel", arrow_position=(0, 0), label_position=(0, 0), color="k", arrow_arc_rad=-0.2
    ):
        """
        Add a label box with text and an arrow from the box to a specified position to an existing provided
        matplotlib.axes `Axes` instance. Original code from Guido Sterbini.
        :param axis: a matplotlib axis.
        :param label: label to give to your arrow.
        :param arrow_position: where the tip of the arrow points.
        :param label_position: where the text label (and thus start of the arrow) is.
        :param color: color of your arrow.
        :param arrow_arc_rad: angle value defining the upwards / downwards shape of the arrow.
        :return: nothing, will act on the existing plot.
        """
        # pylint: disable=too-many-arguments
        return axis.annotate(
            label,
            xy=arrow_position,
            xycoords="data",
            xytext=label_position,
            textcoords="data",
            size=15,
            color=color,
            va="center",
            ha="center",
            bbox=dict(boxstyle="round4", fc="w", color=color, lw=2),
            arrowprops=dict(
                arrowstyle="-|>", connectionstyle="arc3,rad=" + str(arrow_arc_rad), fc="w", color=color, lw=2
            ),
        )


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
