"""
==============
Machine Survey
==============

This example shows how to use the `~pyhdtoolkit.cpymadtools.plotters.LatticePlotter.plot_machine_survey` function
to represent your machine geometry in a from-the-top view.
"""
# sphinx_gallery_thumbnail_number = 2
import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.plotters import LatticePlotter
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")

###############################################################################
# Generate a simple lattice and setup your simulation:

base_lattice = LatticeGenerator.generate_base_cas_lattice()

###############################################################################
# Input the lattice into ``MAD-X``, no more needed here

madx = Madx(stdout=False)
madx.input(base_lattice)

###############################################################################
# Plot the machine survey, as simplistic as possible:

LatticePlotter.plot_machine_survey(madx)
plt.show()

###############################################################################
# Plot the machine survey, differenciating elements and showing high order magnets:

LatticePlotter.plot_machine_survey(madx, show_elements=True, high_orders=True)
plt.show()

###############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.generators`: `~.generators.LatticeGenerator`, `~.lhc.re_cycle_sequence`
#    - `~.cpymadtools.plotters`: `~.plotters.LatticePlotter`, `~.plotters.LatticePlotter.plot_machine_survey`