"""

.. _demo-rigid-waist-shift:

=====================
LHC Rigid Waist Shift
=====================

This example shows how to use the `~.lhc.apply_lhc_rigidity_waist_shift_knob` 
function to force a waist shift at a given IP and break the symmetry of the 
:math:`\\beta`-functions in the Interaction Region. This is done by 
over-powering one triplet and under-powering the other, by the same powering
delta.

We will do a comparison of the interaction region situation before and after 
applying a rigid waist shift, and look in more details at the waist shift 
itself.

.. note::
    This is very specific to the LHC machine and the implementation would not 
    work on other accelerators.
"""
# sphinx_gallery_thumbnail_number = 3
import matplotlib.pyplot as plt
import numpy as np

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc, matching
from pyhdtoolkit.plotting.lattice import plot_latwiss
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Showcasing the Waist Shift
# --------------------------
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
# We will use the `~.plotting.lattice.plot_latwiss` function to have a zoomed-in look
# at the Interaction Region 1 by providing the *xlimits* parameter. Let's first
# determine the position of points of interest through the ``TWISS`` table:

madx.command.twiss()
twiss_df = madx.table.twiss.dframe()
twiss_df.name = twiss_df.name.apply(lambda x: x[:-2])
ip1s = twiss_df.s["ip1"]

###############################################################################
# Let's now have a look at the IR in normal conditions.

plt.figure(figsize=(18, 11))
plot_latwiss(
    madx,
    title="LHCB1 IR1 - No Rigid Waist Shift",
    disp_ylim=(-1.5, 3),
    xoffset=ip1s,
    xlimits=(-200, 200),
    k0l_lim=(-2e-3, 2e-3),
    k1l_lim=(-6.1e-2, 6.1e-2),
    lw=1.5,
)
plt.gcf().axes[-2].set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
for axis in plt.gcf().axes:
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
#
# .. hint::
#    A waist shift knob setting of 1 will result in a 0.5% change in the triplets
#    knob powering. The individual triplet magnets trims are not affected. Here we
#    will use a setting of 1.5 to make the effect easily noticeable.

lhc.apply_lhc_rigidity_waist_shift_knob(madx, rigidty_waist_shift_value=1.5, ir=1)
matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)

###############################################################################
# Let's again retrieve the ``TWISS`` table, then plot the new conditions in the
# Interaction Region.

twiss_df_waist = madx.table.twiss.dframe()
twiss_df_waist.name = twiss_df.name.apply(lambda x: x[:-2])
ip1s = twiss_df_waist.s["ip1"]


plt.figure(figsize=(18, 11))
plot_latwiss(
    madx,
    title="LHCB1 IR1 - With Rigid Waist Shift",
    disp_ylim=(-1.5, 3),
    xoffset=ip1s,
    xlimits=(-200, 200),
    k0l_lim=(-2e-3, 2e-3),
    k1l_lim=(-6.1e-2, 6.1e-2),
    lw=1.5,
)
plt.gcf().axes[-2].set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
for axis in plt.gcf().axes:
    axis.axvline(x=0, color="grey", ls="--", lw=1.5, label="IP1")
plt.show()

###############################################################################
# Comparing to the previous plot, one can notice two things:
#  - The triplet quadrupoles powering has changed and is not (anti-)symmetric anymore.
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
plt.show()

###############################################################################
# Here the subscript **n** stands for nominal, and **w** for the waist shift.
#
# .. tip::
#   The differences observed will vary depending on the strength of the knob,
#   which we choose with the *rigidty_waist_shift_value* parameter.
#
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()

###############################################################################
# Determining the Waist Shift
# ---------------------------
# Let's now determine the value of the waist, aka the amount by which we have
# shifted the waist compared to the IP point location. To do so, we will use
# both an analytical approach and a more brute force one through simulations.
#
# Let's set up a rigid waist shift, with the addition of many *marker* elements
# in the close vicinity of the IP in order to get better resolution when looking
# at the :math:`\beta_{x,y}` functions.
#
# Let's do so for the LHC 2022 optics, with pre-calculated knobs use in the LHC
# 2022 commissioning to speed up this file's execution time.

b1_knobs = ["knobs/quadrupoles.madx", "knobs/triplets.madx", "knobs/working_point.madx"]

with Madx(stdout=False) as madx:
    madx.option(echo=False, warn=False)
    madx.call("acc-models-lhc/lhc.seq")
    lhc.make_lhc_beams(madx, energy=6800)
    madx.call("acc-models-lhc/operation/optics/R2022a_A30cmC30cmA10mL200cm.madx")
    madx.command.use(sequence=f"lhcb1")

    lhc.re_cycle_sequence(madx, sequence=f"lhcb1", start=f"MSIA.EXIT.B1")
    madx.command.use(sequence=f"lhcb1")
    lhc.make_lhc_thin(madx, sequence=f"lhcb1", slicefactor=4)
    lhc.add_markers_around_lhc_ip(madx, sequence=f"lhcb1", ip=1, n_markers=1000, interval=0.001)
    madx.command.twiss()
    initial_twiss = madx.table.twiss.dframe()

    # Calling pre-calculated and re-matched waist shift knobs
    for knobfile in b1_knobs:
        madx.call(knobfile)

    matching.match_tunes(madx, "lhc", f"lhcb1", 62.31, 60.32)
    matching.match_chromaticities(madx, "lhc", f"lhcb1", 2.0, 2.0)
    matching.match_tunes_and_chromaticities(madx, "lhc", f"lhcb1", 62.31, 60.32, 2.0, 2.0)

    madx.command.twiss()
    twiss_df = madx.table.twiss.dframe()

###############################################################################
# We will use all our added markers to determine the location of the waist,
# by simply finding with good resolution the minima of the :math:`\beta_{x,y}`
# functions.

initial_twiss.name = initial_twiss.name.apply(lambda x: x[:-2])
twiss_df.name = twiss_df.name.apply(lambda x: x[:-2])
ip_s = twiss_df.s[f"ip1"]
slimits = (ip_s - 10, ip_s + 10)

around_ip = twiss_df[twiss_df.s.between(*slimits)]
initial_twiss = initial_twiss[initial_twiss.s.between(*slimits)]
waist_location = around_ip.s[around_ip.betx == around_ip.betx.min()][0]

###############################################################################
# We can also plot the :math:`\beta_{x,y}` functions before and after the
# application of the rigid waist shift. Here one can clearly see the shift of
# the waist between the two configurations

fig, axis = plt.subplots(figsize=(15, 10))

axis.plot(
    around_ip.s - ip_s,
    around_ip.betx,
    ls="-",
    color="blue",
    marker=".",
    label=r"$\beta_x^{\mathrm{waist}}$",
)
axis.plot(
    around_ip.s - ip_s,
    around_ip.bety,
    ls="-",
    color="orange",
    marker=".",
    label=r"$\beta_y^{\mathrm{waist}}$",
)

axis.axvline(0, color="purple", ls="--", lw=1.5, label=r"$\mathrm{IP1}$")
axis.axvline(waist_location - ip_s, color="green", ls="--", lw=1.5, label=r"$\mathrm{Waist}$")
axis.axvspan(waist_location - ip_s, 0, color="red", alpha=0.1)

axis.plot(
    initial_twiss.s - ip_s,
    initial_twiss.betx,
    ls="-.",
    color="blue",
    alpha=0.5,
    label=r"$\beta_x^{\mathrm{nominal}}$",
)
axis.plot(
    initial_twiss.s - ip_s,
    initial_twiss.bety,
    ls="-.",
    color="orange",
    alpha=0.5,
    label=r"$\beta_y^{\mathrm{nominal}}$",
)

plt.xlabel(r"$\mathrm{Distance \ to \ IP1 \ [m]}$")
plt.ylabel(r"$\beta_{x,y} \ \mathrm{[m]}$")
plt.legend(ncol=2)
plt.show()

###############################################################################
# The value of the waist is then simply the distance between the IP and the
# location of the found minima. Here is the value, in meters:

shift = ip_s - waist_location
print(shift)

###############################################################################
# Let's now determine this value using the Eq. 10 formula in
# :cite:t:`Carlier:AccuracyFeasibilityMeasurement2017`:
# :math:`\beta_0 = \beta_w + \frac{(L^{*} - w)^2}{\beta_w}`
#
# where :math:`\beta_0` is the :math:`\beta` function at the end of the
# quadrupole (Q1, end closest to IP); :math:`\beta_w`` is the :math:`\beta`
# function at the waist itself (found as min of :math:`\beta` function in the
# region); :math:`L^{*}` is the distance from close end of quadrupole (Q1) to
# the IP point itself; and :math:`w` is the waist displacement we are looking
# to figure out.
#
# Manipulating the equation to determine the waist yields:
# :math:`w = L^{*} - \sqrt{\beta_0 \beta_w - \beta_w^2}`

q1_right_s = twiss_df[twiss_df.name.str.contains(f"mqxa.1r1")].s[0]  # to calculate from the right Q1
q1_left_s = twiss_df[twiss_df.name.str.contains(f"mqxa.1l1")].s[-1]  # to calculate from the left Q1

L_star = ip_s - q1_left_s  # we calculate from left Q1
# beta0 = twiss_df[twiss_df.name.str.contains(f"mqxa.1r1")].betx[0]  # to calculate from the right
beta0 = twiss_df[twiss_df.name.str.contains(f"mqxa.1l1")].betx[-1]  # to calculate from the left
betaw = around_ip.betx.min()

###############################################################################
# The analytical result (sign will swap depending on if we calculate from left
# or right Q1) is then easily calculated. We can then compare this value to the
# one found with the markers we previously added, and they are fairly close.
waist = L_star - np.sqrt(beta0 * betaw - betaw ** 2)
print(f"Analytical: {waist}")
print(f"Markers: {shift}")

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.lhc`: `~.lhc._setup.make_lhc_beams`, `~.lhc._setup.re_cycle_sequence`, `~.lhc._powering.apply_lhc_rigidity_waist_shift_knob`, `~.lhc._elements.add_markers_around_lhc_ip`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes`, `~.matching.match_chromaticities`, `~.matching.match_tunes_and_chromaticities`
#    - `~.plotting.lattice`: `~.plotting.lattice.plot_latwiss`
