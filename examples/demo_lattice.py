"""

.. _demo-accelerator-lattice:

===================
Accelerator Lattice
===================

This example shows how to use the `~.plot.lattice.plot_latwiss` function
to represent your machine's layout and optics functions in a double-axis plot.

In this example, we will showcase the functionality on a simple lattice, and then demonstrate the use
of several parameters to control the plot on the example case of the LHC.
"""
import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc, matching, orbit
from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.plot.lattice import plot_latwiss
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Let's start by generating a simple lattice and setup your simulation:

n_cells: int = 24
base_lattice: str = LatticeGenerator.generate_base_cas_lattice()

madx = Madx(stdout=False)
madx.input(base_lattice)

matching.match_tunes_and_chromaticities(
    madx,
    None,
    "CAS3",
    q1_target=6.335,
    q2_target=6.29,
    dq1_target=100,
    dq2_target=100,
    varied_knobs=["kqf", "kqd", "ksf", "ksd"],
)

###############################################################################
# Plotting the combined machine layout and optics functions is done in a single call
# to the `~.plot.lattice.plot_latwiss` function. Here, we will also set the *k0l_lim*
# parameter to control the right-hand-side axis in the machine layout axis. The same
# can be done with the *k1_lim* parameter.

mu_x_cell = madx.table.summ.Q1[0] / n_cells
mu_y_cell = madx.table.summ.Q2[0] / n_cells
title = rf"Base Lattice, $\mu_{{x, cell}}={mu_x_cell:.3f}, \ \mu_{{y, cell}}={mu_y_cell:.3f}$"

plt.figure(figsize=(18, 11))
plot_latwiss(madx, title=title, k0l_lim=(-0.15, 0.15), k1l_lim=(-0.08, 0.08), disp_ylim=(-10, 125), lw=3)
plt.tight_layout()
plt.show()

madx.exit()

###############################################################################
# One can customise the plot more to their liking or needs thanks to the other
# function parameters. Let's showcase this with the LHC lattice, that we set up
# below:

lhc_madx = Madx(stdout=False)
lhc_madx.option(echo=False, warn=False)
lhc_madx.call("lhc/lhc_as-built.seq")
lhc_madx.call("lhc/opticsfile.22")  # collisions optics

###############################################################################
# Let's re-cycle the sequences to avoid having IR1 split at beginning and end of
# lattice, as is the default in the LHC sequence, and setup a flat orbit.

lhc.re_cycle_sequence(lhc_madx, sequence="lhcb1", start="IP3")
lhc.re_cycle_sequence(lhc_madx, sequence="lhcb2", start="IP3")
orbit_scheme = orbit.setup_lhc_orbit(lhc_madx, scheme="flat")

lhc.make_lhc_beams(lhc_madx, energy=7000)
lhc_madx.command.use(sequence="lhcb1")

###############################################################################
# The `~.plot.lattice.plot_latwiss` function gives the possibility to zoom on a
# region by providing the *xlimits* parameter. Let's first determine the position
# of points of interest through the ``TWISS`` table:

lhc_madx.command.twiss()
twiss_df = lhc_madx.table.twiss.dframe().copy()
twiss_df.name = twiss_df.name.apply(lambda x: x[:-2])
ip1s = twiss_df.s["ip1"]

###############################################################################
# We can now focus the plot in the Interaction Region 1 by providing the *xlimits*
# centered around the value we determined for *ip1s*.
#
# .. tip::
#     In order to zoom on a region, one might be tempted to call the plot and run ``plt.xlim(...)``.
#     However, when providing the *xlimits* parameter, `~.plot.lattice.plot_latwiss` makes a sub-selection
#     of the ``TWISS`` table before doing any plotting. This is provides a nice speedup to the plotting
#     process, as only elements within the limits are rendered on the layout axis, instead of all elements
#     (which can be a lot, and lengthy for big machines such as the LHC). It is therefore the recommended
#     way to zoom on a region.

plt.figure(figsize=(18, 11))
plot_latwiss(
    lhc_madx,
    title="Interaction Region 1, Flat LHCB1 Setup",
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
    title="IP1 Surroundings, Flat LHCB1 Setup",
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
    title="LHC Arc Cell, Flat LHCB1 Setup",
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
#    - `~.cpymadtools.lhc`: `~.lhc.make_lhc_beams`, `~.lhc.re_cycle_sequence`
#    - `~.cpymadtools.generators`: `~.generators.LatticeGenerator`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
#    - `~.cpymadtools.orbit`: `~.orbit.setup_lhc_orbit`
#    - `~.plot.lattice`: `~.lattice.plot_latwiss`
