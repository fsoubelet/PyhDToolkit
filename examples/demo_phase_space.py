"""

.. _demo-phase-space:

===========
Phase Space
===========

This example shows how to use the `~.plotting.phasespace.plot_courant_snyder_phase_space`
and `~.plotting.phasespace.plot_courant_snyder_phase_space_colored` functions to visualise
the particles' normalized coordinates' phase space for your machine.

In this example we will generate a dummy lattice, set its working point and track particles.
The transformation to normalized, or Courant-Snyder, coordinates is handled by the plotting
functions.
"""
# sphinx_gallery_thumbnail_number = 2
import matplotlib.pyplot as plt
import numpy as np

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools._generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.track import track_single_particle
from pyhdtoolkit.plotting.phasespace import (
    plot_courant_snyder_phase_space,
    plot_courant_snyder_phase_space_colored,
)
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Define some constants, generate a simple lattice and setup your simulation:

base_lattice: str = LatticeGenerator.generate_base_cas_lattice()

n_particles: int = 150
n_turns: int = 1000  # will be just enough to do a full revolution in phase space
initial_x_coordinates = np.linspace(1e-4, 0.05, n_particles)

x_coords, px_coords, y_coords, py_coords = [], [], [], []

###############################################################################
# Input the lattice into ``MAD-X``, and match to a desired working point:

madx = Madx(stdout=False)
madx.input(base_lattice)
match_tunes_and_chromaticities(
    madx,
    sequence="CAS3",
    q1_target=6.335,
    q2_target=6.29,
    dq1_target=100,
    dq2_target=100,
    varied_knobs=["kqf", "kqd", "ksf", "ksd"],
)

###############################################################################
# We can then perform tracking on a range of particles. Here the **x_coords**, **px_coords**,
# **y_coords** and **py_coords** become lists of arrays, in which each element has the array of
# a particle's coordinates for each turn.

for starting_x in initial_x_coordinates:
    tracks_df = track_single_particle(
        madx, initial_coordinates=(starting_x, 0, 0, 0, 0, 0), nturns=n_turns
    )
    x_coords.append(tracks_df["observation_point_1"].x.to_numpy())
    y_coords.append(tracks_df["observation_point_1"].y.to_numpy())
    px_coords.append(tracks_df["observation_point_1"].px.to_numpy())
    py_coords.append(tracks_df["observation_point_1"].py.to_numpy())

###############################################################################
# Now we can plot these coordinates in phase space, here for the horizontal plane.
# Note that the function automatically calculates the normalized coordinates and
# plots these.

fig, ax = plt.subplots(figsize=(10, 10))
plot_courant_snyder_phase_space(
    madx, 1e3 * np.array(x_coords), 1e3 * np.array(px_coords), plane="Horizontal"
)
ax.set_xlabel(r"$\hat{x}$ [$10^{3}$]")
ax.set_ylabel(r"$\hat{p}_x$ [$10^{3}$]")
ax.set_xlim(-20, 18)
ax.set_ylim(-18, 22)
plt.show()

###############################################################################
# Using the `~.plotting.phasespace.plot_courant_snyder_phase_space_colored` function,
# one gets a plot in which each color corresponds to a given particle's trajectory:

fig, ax = plt.subplots(figsize=(10, 10))
plot_courant_snyder_phase_space_colored(
    madx, 1e3 * np.array(x_coords), 1e3 * np.array(px_coords), plane="Horizontal"
)
ax.set_xlabel(r"$\hat{x}$ [$10^{3}$]")
ax.set_ylabel(r"$\hat{p}_x$ [$10^{3}$]")
ax.set_xlim(-20, 18)
ax.set_ylim(-18, 22)
plt.show()

###############################################################################
# Let's close the rpc connection to ``MAD-X``:
madx.exit()

###############################################################################
# We can see the evolvution of particles through the normalized phase space during
# tracking: each point in a given line correspond to a given turn. In our case,
# this dummy lattice was created for lectures and is very robust. If one wants
# significant change, a good solution is to excite a resonance!
#
# To do so, we will use a similar lattice equipped with a sextupole, which we will
# use to excite a third order resonance.

perturbed_lattice = LatticeGenerator.generate_onesext_cas_lattice()

madx = Madx(stdout=False)
madx.input(perturbed_lattice)
madx.input("ks1 = 0.1;")  # powering the sextupole

###############################################################################
# Let's get close to the third order resonance and track particles.

match_tunes_and_chromaticities(
    madx,
    sequence="CAS3",
    q1_target=6.335,
    q2_target=6.29,
    dq1_target=100,
    dq2_target=100,
    varied_knobs=["kqf", "kqd", "ksf", "ksd"],
)

x_coords_sext, px_coords_sext, y_coords_sext, py_coords_sext = [], [], [], []

for starting_x in initial_x_coordinates:
    tracks_df = track_single_particle(madx, initial_coordinates=(starting_x, 0, 0, 0, 0, 0), nturns=n_turns)
    x_coords_sext.append(tracks_df["observation_point_1"].x.to_numpy())
    y_coords_sext.append(tracks_df["observation_point_1"].y.to_numpy())
    px_coords_sext.append(tracks_df["observation_point_1"].px.to_numpy())
    py_coords_sext.append(tracks_df["observation_point_1"].py.to_numpy())

###############################################################################
# Plotting the new phase space, we can clearly see the resonance's islands!

fig, ax = plt.subplots(figsize=(10, 10))
plot_courant_snyder_phase_space_colored(
    madx, 1e3 * np.array(x_coords_sext), 1e3 * np.array(px_coords_sext), plane="Horizontal"
)
ax.set_xlabel(r"$\hat{x}$ [$10^{3}$]")
ax.set_ylabel(r"$\hat{p}_x$ [$10^{3}$]")
ax.set_xlim(-15, 15)
ax.set_ylim(-15, 15)
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
#    - `~.cpymadtools._generators`: `~._generators.LatticeGenerator`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
#    - `~.plotting.phasespace`: `~.plotting.phasespace.plot_courant_snyder_phase_space`, `~.plotting.phasespace.plot_courant_snyder_phase_space_colored`
#    - `~.cpymadtools.track`: `~.track.track_single_particle`
