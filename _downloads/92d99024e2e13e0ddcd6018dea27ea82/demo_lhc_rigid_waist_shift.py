"""

.. _demo-rigid-waist-shift:

=====================
LHC Rigid Waist Shift
=====================

This example shows how to use the `~.lhc.apply_lhc_rigidity_waist_shift_knob` 
function to force a waist shift at a given IP and break the symmetry of the 
:math:`\\beta`-functions in the Interaction Region.

We will do a comparison of the interaction region situation before and after 
applying a rigid waist shift.

.. note::
    This is very specific to the LHC machine and the implementation would not 
    work on other accelerators.
"""
# sphinx_gallery_thumbnail_number = -1
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc, matching
from pyhdtoolkit.cpymadtools.plotters import LatticePlotter
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Let's start by setting up the LHC in ``MAD-X``, in this case at top energy:

madx = Madx(stdout=False)
madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collision optics

###############################################################################
# Let's re-cycle the sequences to avoid having IR1 split at beginning and end of lattice,
# as is the default in the LHC sequence:

lhc.re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
lhc.make_lhc_beams(madx, energy=7000)
madx.command.use(sequence="lhcb1")

###############################################################################
# We will use the `~.plotters.LatticePlotter.plot_latwiss` function to have zoomed-in
# look at the Interaction Region 1 by providing the *xlimits* parameter. Let's first
# determine the position of points of interest through the ``TWISS`` table:

madx.command.twiss()
twiss_df = madx.table.twiss.dframe().copy()
twiss_df.name = twiss_df.name.apply(lambda x: x[:-2])
ip1s = twiss_df.s["ip1"]

###############################################################################
# Let's now have a look at the IR in normal conditions.

IR1_fig = LatticePlotter.plot_latwiss(
    madx,
    figsize=(18, 11),
    title="LHCB1 IR1 - No Rigid Waist Shift",
    disp_ylim=(-1.5, 3),
    xoffset=ip1s,
    xlimits=(-200, 200),
    k0l_lim=(-2e-3, 2e-3),
    k1l_lim=(-6.1e-2, 6.1e-2),
    lw=1.5,
)
IR1_fig.axes[-2].set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
for axis in IR1_fig.axes:
    axis.axvline(x=0, color="grey", ls="--", lw=1.5, label="IP1")
plt.show()

###############################################################################
# Notice the (anti)symmetry of the :math:`\beta_{x,y}` functions and triplet
# quadrupoles powering on the right and left-hand side of the IP. Let's now apply
# a rigid waist shift - meaning all four betatron waists moving simultaneously - by
# changing the triplets powering. This is handled by the convenient function
# `~.lhc.apply_lhc_rigidity_waist_shift_knob`.
#
# It is possible to choose the knob's strength, in which IR to apply it, and on
# which side of the IP to shift the beam waist. See the function documentation
# for more details. After applying the knob, we will re-match to our working point
# to make sure we do not deviate.

lhc.apply_lhc_rigidity_waist_shift_knob(madx, rigidty_waist_shift_value=1.5, ir=1)
matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)

###############################################################################
# Let's again retrieve the ``TWISS`` table, then plot the new conditions in the
# Interaction Region.

twiss_df_waist = madx.table.twiss.dframe().copy()
twiss_df_waist.name = twiss_df.name.apply(lambda x: x[:-2])
ip1s = twiss_df_waist.s["ip1"]

IR1_waist_shift = LatticePlotter.plot_latwiss(
    madx,
    figsize=(16, 11),
    title="LHCB1 IR1 - No Rigid Waist Shift",
    disp_ylim=(-1.5, 3),
    xoffset=ip1s,
    xlimits=(-200, 200),
    k0l_lim=(-2e-3, 2e-3),
    k1l_lim=(-6.1e-2, 6.1e-2),
    lw=1.5,
)
IR1_waist_shift.axes[-2].set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
for axis in IR1_fig.axes:
    axis.axvline(x=0, color="grey", ls="--", lw=1.5, label="IP1")
plt.show()

###############################################################################
# Comparing to the previous plot, one can notice two things:
#  - The triplet quadrupoles powering has changed.
#  - The :math:`\beta_{x,y}` functions symmetry has been broken.
#
# One can compare the :math:`\beta_{x,y}` functions before and after the rigid
# waist shift with a simple plot:

plt.figure(figsize=(16, 10))
plt.plot(twiss_df.s - ip1s, twiss_df.betx * 1e-3, "b-", label=r"$\beta_{x}^{n}$")
plt.plot(twiss_df_waist.s - ip1s, twiss_df_waist.betx * 1e-3, "b--", label=r"$\beta_{x}^{w}$")

plt.plot(twiss_df.s - ip1s, twiss_df.bety * 1e-3, "r-", label=r"$\beta_{y}^{n}$")
plt.plot(twiss_df_waist.s - ip1s, twiss_df_waist.bety * 1e-3, "r--", label=r"$\beta_{y}^{w}$")

plt.xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
plt.ylabel(r"$\beta_{x,y}\ \mathrm{[km]}$")
plt.xlim(-200, 200)
plt.ylim(-5e-1, 9)
plt.legend()

###############################################################################
# Here the subscript **n** stands for nominal, and **w** for the waist shift.
#
# .. tip::
#   The differences observed will vary depending on the strength of the knob,
#   which we choose with the **rigidty_waist_shift_value** parameter.
#
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.lhc`: `~.lhc.make_lhc_beams`, `~.lhc.re_cycle_sequence`, `~.lhc.apply_lhc_rigidity_waist_shift_knob`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
#    - `~.cpymadtools.plotters`: `~.plotters.LatticePlotter`, `~.plotters.LatticePlotter.plot_latwiss`
