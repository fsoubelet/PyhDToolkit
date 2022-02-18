"""
=============================
Machine Survey Plotting Demo
=============================

This example shows how to use the `~pyhdtoolkit.cpymadtools.plotters.LatticePlotter.plot_machine_survey` function
to represent your machine geometry in a from-the-top view.
"""

import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.plotters import LatticePlotter
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")

###############################################################################
# Define some constants, generate a simple lattice and setup your simulation

circumference: float = 1000.0
n_cells: int = 24
base_lattice = LatticeGenerator.generate_base_cas_lattice()

###############################################################################
# Input the lattice into ``MAD-X``, no more needed here
madx = Madx(stdout=False)
madx.input(base_lattice)

###############################################################################
# Plot the machine survey, as simplistic as possible

LatticePlotter.plot_machine_survey(madx)
plt.show()

###############################################################################
# Plot the machine survey, differenciating elements and showing high order magnets

LatticePlotter.plot_machine_survey(madx, show_elements=True, high_orders=True)
plt.show()

###############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``

madx.exit()
