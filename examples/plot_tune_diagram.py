"""
============
Tune Diagram
============

This example shows how to use the `~.plotters.TuneDiagramPlotter.plot_tune_diagram` function 
to visualise resonance lines up to certain orders.
"""
# sphinx_gallery_thumbnail_number = -1
import matplotlib.pyplot as plt

from pyhdtoolkit.cpymadtools.plotters import TuneDiagramPlotter
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")

###############################################################################
# The tune diagram allows on to visualise resonance lines up to certain orders,
# and to know where the working point of the machine stands compared to these resonances
# By default, the `~pyhdtoolkit.cpymadtools.plotters.TuneDiagramPlotter.plot_tune_diagram`
# function will plot all resonance lines up to the specified order, with line thickness
# decreasing with the resonance order. The max order is set 6, as the graph becomes unreadable
# above this value.

TuneDiagramPlotter.plot_tune_diagram(max_order=5)
plt.show()

###############################################################################
# One can add their machine's working point onto the figure with a new matplotlib
# plotting command. The graph is limited to the ranges [0, 1] on each axis as the
# fractional part of the tunes is what determines stability.
#
# .. tip::
#     Remember that when thinking about tunes, only the fractional part is relevant
#     when determining the stability. As so, plot that value onto the graph, or it would
#     be way out of range

TuneDiagramPlotter.plot_tune_diagram(max_order=5)
plt.scatter(0.35, 0.29, marker="o", color="red")  # this is close to a third order resonance
plt.show()

###############################################################################
# On the previous plot, it is not obvious that our working point is close to a
# *third* order resonance. One may then want to differentiate the origin of each
# line, aka knowing which resonance order is responsible for each given line. This
# makes it easier to see the resonances near your working point.

TuneDiagramPlotter.plot_tune_diagram(
    max_order=6,
    differentiate_orders=True,  # different orders will have a different color and linestyle
    legend_title="Resonance Lines",  # if given, legend is added to figure
)
plt.scatter(0.35, 0.29, marker="o", color="red")  # this is close to a third order resonance
plt.xlim(0, 0.5)  # limit the x-axis to the range [0, 0.5] for visibility
plt.ylim(0, 0.5)  # limit the y-axis to the range [0, 0.5] for visibility
plt.show()

###############################################################################
# It is now much easier to identify the resonances lines near our working point :)

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.plotters.TuneDiagramPlotter`: `~.plotters.TuneDiagramPlotter.plot_tune_diagram`