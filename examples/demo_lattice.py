"""

.. _demo-accelerator-lattice:

===================
Accelerator Lattice
===================

This example shows how to use the `~.plotting.lattice.plot_latwiss` function
to represent your machine's layout and optics functions in a double-axis plot.

In this example, we will showcase the functionality on a simple lattice, and then demonstrate the use
of several parameters to control the plot on the example case of the LHC.
"""

import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc, matching
from pyhdtoolkit.cpymadtools._generators import LatticeGenerator
from pyhdtoolkit.plotting.lattice import plot_latwiss
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Let's start by generating a simple lattice and setup your simulation:

n_cells: int = 24
base_lattice: str = LatticeGenerator.generate_base_cas_lattice()

madx = Madx(stdout=False)
madx.input(base_lattice)

matching.match_tunes_and_chromaticities(
    madx,
    sequence="CAS3",
    q1_target=6.335,
    q2_target=6.29,
    dq1_target=100,
    dq2_target=100,
    varied_knobs=["kqf", "kqd", "ksf", "ksd"],
)

###############################################################################
# Plotting the combined machine layout and optics functions is done in a single call
# to the `~.plotting.lattice.plot_latwiss` function. Here, we will also set the *k0l_lim*
# parameter to control the right-hand-side axis in the machine layout axis. The same
# can be done with the *k1_lim* parameter.

mu_x_cell = madx.table.summ.Q1[0] / n_cells
mu_y_cell = madx.table.summ.Q2[0] / n_cells
title = rf"Base Lattice, $\mu_{{x, cell}}={mu_x_cell:.3f}, \ \mu_{{y, cell}}={mu_y_cell:.3f}$"

plt.figure(figsize=(18, 11))
plot_latwiss(
    madx, title=title, k0l_lim=(-0.15, 0.15), k1l_lim=(-0.08, 0.08), disp_ylim=(-10, 125), lw=3
)
plt.tight_layout()
plt.show()

madx.exit()

###############################################################################
# One can customise the plot more to their liking or needs thanks to the other
# function parameters. Let's showcase this with the LHC lattice, that we set up
# below.
#
# .. important::
#     This example requires the `acc-models-lhc` repository to be cloned locally. One
#     can get it by running the following command:
#
#     .. code-block:: bash
#
#         git clone -b 2022 https://gitlab.cern.ch/acc-models/acc-models-lhc.git --depth 1
#
#     Here I set the 2022 branch for stability and reproducibility of the documentation
#     builds, but you can use any branch you want.

lhc_madx: Madx = lhc.prepare_lhc_run3(
    opticsfile="acc-models-lhc/operation/optics/R2022a_A30cmC30cmA10mL200cm.madx", stdout=False
)

###############################################################################
# The `~.plotting.lattice.plot_latwiss` function gives the possibility to zoom on
# a region by providing the *xlimits* parameter. Let's first determine the position
# of points of interest through the ``TWISS`` table:

lhc_madx.command.twiss()
twiss_df = lhc_madx.table.twiss.dframe()
twiss_df.name = twiss_df.name.apply(lambda x: x[:-2])
ip1s = twiss_df.s["ip1"]

###############################################################################
# We can now focus the plot in the Interaction Region 1 by providing the *xlimits*
# centered around the value we determined for *ip1s*.
#
# .. tip::
#     In order to zoom on a region, one might be tempted to call the plot and run ``plt.xlim(...)``.
#     However, when providing the *xlimits* parameter, `~.plotting.lattice.plot_latwiss` makes a sub-selection
#     of the ``TWISS`` table before doing any plotting. This is provides a nice speedup to the plotting
#     process, as only elements within the limits are rendered on the layout axis, instead of all elements
#     (which can be a lot, and quite lengthy for big machines such as the LHC). It is therefore the recommended
#     way to zoom on a region.

plt.figure(figsize=(18, 11))
plot_latwiss(
    lhc_madx,
    title="Interaction Region 1",
    disp_ylim=(-0.5, 2.5),
    xlimits=(ip1s - 457, ip1s + 457),
    k0l_lim=(-1.3e-2, 1.3e-2),
    k1l_lim=(-6.1e-2, 6.1e-2),
    lw=1.5,
)
plt.axvline(x=ip1s, color="grey", ls="--", lw=1.5, label="IP1")
plt.tight_layout()
plt.show()

###############################################################################
# Using the *xoffset* parameter, one can shift the longitudinal coordinate to be
# centered on 0, with the horizontal axis showing relative position to the given
# *xoffset*. This is useful here to zoom closely on IP1 and see the elements'
# positions relative to the IP marker.

plt.figure(figsize=(18, 11))
plot_latwiss(
    lhc_madx,
    title="IP1 Surroundings",
    disp_ylim=(-3e-2, 3e-2),
    xoffset=ip1s,
    xlimits=(-85, 85),
    k0l_lim=(-4e-4, 4e-4),
    k1l_lim=(-6e-2, 6e-2),
    lw=1.5,
)
plt.axvline(x=0, color="grey", ls="--", lw=1.5, label="IP1")
plt.tight_layout()
plt.show()

###############################################################################
# When and only when the *k2l_lim* parameter is provided, the sextupolar elements
# are plotted on the lattice layout axis, and an additional scale is put to the right.
# This is useful to see sextupoles when zooming in, which you would not necessarily
# want to plot when looking at the big picture, to avoid overcrowding it. Similarly,
# providing the *plot_bpms* will add a small marker for BPM elements. Here it is
# showcased when looking at an LHC arc cell:

plt.rcParams.update({"axes.formatter.limits": (-2, 5)})  # convenience
plt.figure(figsize=(18, 11))
plot_latwiss(
    lhc_madx,
    title="LHC Arc Cell",
    plot_bpms=True,
    disp_ylim=(-0.5, 20),
    beta_ylim=(0, 200),
    k0l_lim=(-3e-2, 3e-2),
    k1l_lim=(-4e-2, 4e-2),
    k2l_lim=(-5e-2, 5e-2),
    lw=1.5,
    xlimits=(14_084.5, 14_191.3),
)
plt.tight_layout()
plt.show()

###############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``:

lhc_madx.exit()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.lhc`: `~.lhc._setup.prepare_lhc_run3`, `~.lhc._setup.setup_lhc_orbit`
#    - `~.cpymadtools.generators`: `~.generators.LatticeGenerator`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
#    - `~.plotting.lattice`: `~.plotting.lattice.plot_latwiss`
