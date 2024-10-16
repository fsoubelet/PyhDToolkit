"""

.. _demo-rigid-waist-shift:

=====================
LHC Rigid Waist Shift
=====================

This example shows how to use the `~.lhc.apply_lhc_rigidity_waist_shift_knob`
function to force a waist shift at a given IP and break the symmetry of the
:math:`\\beta`-functions in the Interaction Region. This is done by
over-powering one triplet knob and under-powering the other, by the same
powering delta.

In :cite:t:`PRAB:Soubelet:Rigid_Waist_Shift_Method_Local_Coupling_Correction_LHC_IR`
(2023) one can find out about studies and achievements at the LHC done with the Rigid
Waist Shift.

We will do a comparison of the interaction region situation before and after
applying a rigid waist shift, and look in more details at the waist shift
itself.

.. note::
    This is very specific to the LHC machine and the implementation in these
    functions would not work on other accelerators.

.. important::
    This example requires the `acc-models-lhc` repository to be cloned locally. One
    can get it by running the following command:

    .. code-block:: bash

        git clone -b 2022 https://gitlab.cern.ch/acc-models/acc-models-lhc.git --depth 1

    Here I set the 2022 branch for stability and reproducibility of the documentation
    builds, but you can use any branch you want.
"""

# sphinx_gallery_thumbnail_number = 3
from multiprocessing import cpu_count
from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
import tfs

from cpymad.madx import Madx
from joblib import Parallel, delayed

from pyhdtoolkit.cpymadtools import lhc, matching, twiss
from pyhdtoolkit.plotting.lattice import plot_latwiss
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.plotting.utils import draw_ip_locations, get_lhc_ips_positions
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Showcasing the Waist Shift
# --------------------------
# Let's start by setting up the LHC in ``MAD-X``, in this case at top energy.
# To understand the function below have a look at the :ref:`lhc setup example
# <demo-lhc-setup>`.

madx: Madx = lhc.prepare_lhc_run3(
    opticsfile="acc-models-lhc/operation/optics/R2022a_A30cmC30cmA10mL200cm.madx",
    stdout=False,
)

###############################################################################
# We will use the `~.plotting.lattice.plot_latwiss` function to have a zoomed-in look
# at the Interaction Region 1 by providing the *xlimits* parameter. Let's first
# get the IP postitions with `~.plotting.utils.get_lhc_ips_positions`:

nominal_df = twiss.get_twiss_tfs(madx)
ips = get_lhc_ips_positions(nominal_df)
ip1s = ips["IP1"]

###############################################################################
# Let's now have a look at the IR in normal conditions.

plt.figure(figsize=(18, 11))
plot_latwiss(
    madx,
    title="LHCB1 IR1 - No Rigid Waist Shift",
    disp_ylim=(-0.4, 1.9),
    xoffset=ip1s,
    xlimits=(-200, 200),
    k0l_lim=2.25e-3,
    k1l_lim=6.1e-2,
    lw=1.5,
)
plt.gcf().axes[-2].set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
for axis in plt.gcf().axes:
    axis.axvline(x=0, color="grey", ls="--", lw=1.5, label="IP1")
plt.show()

###############################################################################
# Notice the (anti-)symmetry of the :math:`\beta_{x,y}` functions and triplet
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
waist_df = twiss.get_twiss_tfs(madx)

###############################################################################
# Let's again retrieve the ``TWISS`` table, then plot the new conditions in the
# Interaction Region.

plt.figure(figsize=(18, 11))
plot_latwiss(
    madx,
    title="LHCB1 IR1 - With Rigid Waist Shift",
    disp_ylim=(-0.4, 1.9),
    xoffset=ip1s,
    xlimits=(-200, 200),
    k0l_lim=2.25e-3,
    k1l_lim=6.1e-2,
    lw=1.5,
)
plt.gcf().axes[-2].set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
for axis in plt.gcf().axes:
    axis.axvline(x=0, color="grey", ls="--", lw=1.5, label="IP1")
plt.show()

###############################################################################
# Comparing to the previous plot, one can notice two things:
#  - The triplet quadrupoles powering has changed.
#  - The :math:`\beta_{x,y}` functions symmetry has been broken.
#
# One can compare the :math:`\beta_{x,y}` functions before and after the rigid
# waist shift with a simple plot:

fig, ax = plt.subplots(figsize=(16, 10))
ax.plot(nominal_df.S - ip1s, 1e-3 * nominal_df.BETX, "b-", label=r"$\beta_x^n$")
ax.plot(waist_df.S - ip1s, 1e-3 * waist_df.BETX, "b--", label=r"$\beta_x^w$")

ax.plot(nominal_df.S - ip1s, 1e-3 * nominal_df.BETY, "r-", label=r"$\beta_y^n$")
ax.plot(waist_df.S - ip1s, 1e-3 * waist_df.BETY, "r--", label=r"$\beta_y^w$")

ax.set_xlabel(r"$\mathrm{Distance\ to\ IP1\ [m]}$")
ax.set_ylabel(r"$\beta_{x,y}\ \mathrm{[km]}$")
ax.set_xlim(-215, 215)
ax.set_ylim(-0.7, 9.3)

ax.xaxis.set_major_locator(plt.MaxNLocator(5))
ax.yaxis.set_major_locator(plt.MaxNLocator(5))
draw_ip_locations({"IP1": 0}, location="inside")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1), ncols=4)

plt.tight_layout()
plt.show()

###############################################################################
# Here the subscript **n** stands for the nominal scenario, and **w** for the
# rigid waist shift scenario.
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
# shifted the waist compared to the IP point location. To this end, we will use
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
    madx.command.use(sequence="lhcb1")

    lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
    madx.command.use(sequence="lhcb1")
    lhc.make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
    lhc.add_markers_around_lhc_ip(madx, sequence="lhcb1", ip=1, n_markers=1000, interval=0.001)
    madx.command.twiss()
    initial_twiss = madx.table.twiss.dframe()

    # Calling pre-calculated and re-matched waist shift knobs
    for knobfile in b1_knobs:
        madx.call(knobfile)

    matching.match_tunes(madx, "lhc", "lhcb1", 62.31, 60.32)
    matching.match_chromaticities(madx, "lhc", "lhcb1", 2.0, 2.0)
    matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)

    madx.command.twiss()
    nominal_df = madx.table.twiss.dframe()

###############################################################################
# We will use all our added markers to determine the location of the waist,
# by simply finding with good resolution the minima of the :math:`\beta_{x,y}`
# functions.

initial_twiss.name = initial_twiss.name.apply(lambda x: x[:-2])
nominal_df.name = nominal_df.name.apply(lambda x: x[:-2])
ip_s = nominal_df.s["ip1"]
slimits = (ip_s - 10, ip_s + 10)

around_ip = nominal_df[nominal_df.s.between(*slimits)]
initial_twiss = initial_twiss[initial_twiss.s.between(*slimits)]
waist_location = around_ip.s[around_ip.betx == around_ip.betx.min()].iloc[0]

###############################################################################
# We can also plot the :math:`\beta_{x,y}` functions before and after the
# application of the rigid waist shift. Here one can clearly see the shift of
# the waist between the two configurations.

fig, axis = plt.subplots(figsize=(16, 10))

axis.plot(
    around_ip.s - ip_s,
    around_ip.betx,
    ls="-",
    color="blue",
    marker=".",
    label=r"$\beta_x^w$",
)
axis.plot(
    around_ip.s - ip_s,
    around_ip.bety,
    ls="-",
    color="orange",
    marker=".",
    label=r"$\beta_y^w$",
)

axis.axvline(0, color="purple", ls="--", lw=1.5, label="IP1")
axis.axvline(waist_location - ip_s, color="green", ls="--", lw=1.5, label="Waist")
axis.axvspan(waist_location - ip_s, 0, color="red", alpha=0.1)

axis.plot(
    initial_twiss.s - ip_s,
    initial_twiss.betx,
    ls="-.",
    color="blue",
    alpha=0.5,
    label=r"$\beta_x^n$",
)
axis.plot(
    initial_twiss.s - ip_s,
    initial_twiss.bety,
    ls="-.",
    color="orange",
    alpha=0.5,
    label=r"$\beta_y^n$",
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
# function at the waist itself (found as the minimum of the :math:`\beta`-function
# in the region); :math:`L^{*}` is the distance from close end of quadrupole (Q1)
# to the IP point itself; and :math:`w` is the waist displacement we are looking
# to figure out.
#
# Manipulating the equation to determine the waist yields:
# :math:`w = L^{*} - \sqrt{\beta_0 \beta_w - \beta_w^2}`

# to calculate from the right Q1 then from the left Q1
q1_right_s = nominal_df[nominal_df.name.str.contains("mqxa.1r1")].s.iloc[0]
q1_left_s = nominal_df[nominal_df.name.str.contains("mqxa.1l1")].s.iloc[-1]

L_star = ip_s - q1_left_s  # say we calculate from left Q1
# beta0 = nominal_df[nominal_df.name.str.contains(f"mqxa.1r1")].betx.iloc[0]  # from the right
beta0 = nominal_df[nominal_df.name.str.contains("mqxa.1l1")].betx.iloc[-1]  # from the left
betaw = around_ip.betx.min()

###############################################################################
# The analytical result (sign will swap depending on if we calculate from left
# or right Q1) is then easily calculated. We can then compare this value to the
# one found with the markers we previously added, and they are fairly close.
waist = L_star - np.sqrt(beta0 * betaw - betaw**2)
print(f"Analytical: {waist}")
print(f"Markers: {shift}")

###############################################################################
# Seeing the effect through values of the knob
# --------------------------------------------
# We can use the above to determine these values for different knob settings.
# First, let's define some structures and functions.

Waist = NamedTuple("Waist", ["x", "y"])
BetasIP = NamedTuple("Betas", ["x", "y"])
Result = NamedTuple("Result", ["waists", "betas"])


def find_waists(current_twiss: tfs.TfsDataFrame, initial_twiss: tfs.TfsDataFrame) -> Waist:
    initial = initial_twiss.copy()
    ip_s = current_twiss.S["IP1"]
    slimits = (ip_s - 10, ip_s + 10)

    around_ip = current_twiss[current_twiss.S.between(*slimits)]
    initial = initial[initial.S.between(*slimits)].copy()
    hor_waist_location = around_ip.S[around_ip.BETX.min() == around_ip.BETX].iloc[0]
    ver_waist_location = around_ip.S[around_ip.BETY.min() == around_ip.BETY].iloc[0]
    initial = initial_twiss.copy()
    ip_s = current_twiss.S["IP1"]
    slimits = (ip_s - 10, ip_s + 10)

    around_ip = current_twiss[current_twiss.S.between(*slimits)]
    initial = initial[initial.S.between(*slimits)].copy()
    hor_waist_location = around_ip.S[around_ip.BETX.min() == around_ip.BETX].iloc[0]
    ver_waist_location = around_ip.S[around_ip.BETY.min() == around_ip.BETY].iloc[0]
    return Waist(ip_s - hor_waist_location, ip_s - ver_waist_location)


def find_betashifts(
    current_twiss: tfs.TfsDataFrame, initial_twiss: tfs.TfsDataFrame
) -> BetasIP:
    delta_betx = current_twiss.BETX["IP1"] - initial_twiss.BETX["IP1"]
    delta_bety = current_twiss.BETY["IP1"] - initial_twiss.BETY["IP1"]
    return BetasIP(delta_betx, delta_bety)


def simulation(knob_value: float) -> Result:
    with lhc.LHCSetup(
        run=3, opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", slicefactor=4, stdout=False
    ) as madx:
        lhc.add_markers_around_lhc_ip(
            madx, sequence="lhcb1", ip=1, n_markers=1000, interval=0.001
        )
        ref_twiss = twiss.get_twiss_tfs(madx)
        lhc.apply_lhc_rigidity_waist_shift_knob(madx, knob_value, ir=1)
        new_twiss = twiss.get_twiss_tfs(madx)
        reswaists = find_waists(new_twiss, ref_twiss)
        resbetas = find_betashifts(new_twiss, ref_twiss)
        return Result(reswaists, resbetas)


#############################################################################
# Let's now run the simulation for different knob values:

parameter_space = np.linspace(-1, 1, 50)
results: list[Result] = Parallel(n_jobs=cpu_count(), backend="threading", verbose=0)(
    delayed(simulation)(knob_value=knobval) for knobval in parameter_space
)

waist_x = np.array([res.waists.x for res in results])
waist_y = np.array([res.waists.y for res in results])

deltabetx = np.array([res.betas.x for res in results])
deltabety = np.array([res.betas.y for res in results])

#############################################################################
# We can now plot the results:

fig, axis = plt.subplots(figsize=(16, 10))

axis.plot(parameter_space, 1e2 * waist_x, "C0", marker="s", markersize=4)
axis.tick_params(axis="y", colors="C0")
axis.yaxis.label.set_color("C0")
axis.xaxis.set_major_locator(plt.MaxNLocator(5))

axis2 = axis.twinx()
axis2.yaxis.set_label_position("right")
axis2.yaxis.label.set_color("C1")
axis2.yaxis.tick_right()
axis2.tick_params(axis="y", colors="C1")
axis2.plot(
    parameter_space,
    1e2 * deltabetx,
    "C1",
    marker="o",
    ls="-",
    markersize=4,
    label="Horizontal",
)
axis2.plot(
    parameter_space,
    1e2 * deltabety,
    "C2",
    marker="o",
    ls="--",
    markersize=4,
    label="Vertical",
)
axis2.legend(loc="lower center", bbox_to_anchor=(0.5, 1), ncols=2)

axis.set_xlabel("Knob Setting")
axis.set_ylabel(r"$\mathrm{Waist_{X,Y}}$ Shift [cm]")
axis2.set_ylabel(r"$\Delta \beta^{\ast}$ [cm]")

plt.show()

#############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.lhc`: `~.lhc._setup.prepare_lhc_run3`, `~.lhc._setup.make_lhc_beams`, `~.lhc._setup.re_cycle_sequence`, `~.lhc._powering.apply_lhc_rigidity_waist_shift_knob`, `~.lhc._setup.make_lhc_thin`, `~.lhc._elements.add_markers_around_lhc_ip`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes`, `~.matching.match_chromaticities`, `~.matching.match_tunes_and_chromaticities`
#    - `~.cpymadtools.twiss`: `~.twiss.get_twiss_tfs`
#    - `~.plotting.lattice`: `~.plotting.lattice.plot_latwiss`
#    - `~.plotting.utils`: `~.plotting.utils.draw_ip_locations`, `~.plotting.utils.get_lhc_ips_positions`
