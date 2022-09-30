"""

.. _demo-machine-survey:

==============
Machine Survey
==============

This example shows how to use the `~.plotting.lattice.plot_machine_survey` function
to represent your machine geometry in a from-the-top view.
"""
# sphinx_gallery_thumbnail_number = 2
import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.plotting.lattice import plot_machine_survey
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Generate a simple lattice and setup your simulation:

base_lattice = LatticeGenerator.generate_base_cas_lattice()

###############################################################################
# Input the lattice into ``MAD-X``, no more needed here

madx = Madx(stdout=False)
madx.input(base_lattice)

###############################################################################
# Plot the machine survey, as simplistic as possible:

plt.figure(figsize=(16, 11))
plot_machine_survey(madx, title="Machine Layout")
plt.show()

###############################################################################
# Plot the machine survey, differenciating elements and showing high order magnets:

plt.figure(figsize=(16, 11))
plot_machine_survey(madx, title="Machine Layout", show_elements=True, high_orders=True)
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
#    - `~.plotting.lattice`: `~.plotting.lattice.plot_machine_survey`
