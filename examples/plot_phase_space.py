"""
===========
Phase Space
===========

This example shows how to use the `~.plotters.PhaseSpacePlotter.plot_courant_snyder_phase_space` 
and `~.plotters.PhaseSpacePlotter.plot_courant_snyder_phase_space_colored` functions to visualise
the particles' trajectories in phase space for your machine.

In this example we will generate a dummy lattice, set its working point and track particles to plot their phase space coordinates.
"""
# sphinx_gallery_thumbnail_number = 2
import matplotlib.pyplot as plt
import numpy as np

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.plotters import PhaseSpacePlotter
from pyhdtoolkit.cpymadtools.track import track_single_particle
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")

###############################################################################
# Define some constants, generate a simple lattice and setup your simulation:

base_lattice: str = LatticeGenerator.generate_base_cas_lattice()

n_particles: int = 200
n_turns: int = 1000  # just enough to do a full revolution in phase space
initial_x_coordinates = np.linspace(1e-4, 0.05, n_particles)

x_coords, px_coords, y_coords, py_coords = [], [], [], []

###############################################################################
# Input the lattice into ``MAD-X``, and match to a desired working point:

madx = Madx(stdout=False)
madx.input(base_lattice)
match_tunes_and_chromaticities(
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

PhaseSpacePlotter.plot_courant_snyder_phase_space(
    madx, x_coords, px_coords, plane="Horizontal", figsize=(10, 9)
)
plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
plt.show()

###############################################################################
# Using the `~pyhdtoolkit.cpymadtools.plotters.PhaseSpacePlotter.plot_courant_snyder_phase_space_colored`
# function, one gets a plot in which each color corresponds to a given particle's trajectory:

PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
    madx, x_coords, px_coords, plane="Horizontal", figsize=(10, 9)
)
plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
plt.show()

###############################################################################
# We can see the phase space evolve as the machine's working conditions change.
# In our case, this dummy lattice is meant for classes and is very robust, so if
# one wants significant change, a solution is to excite a resonance!
#
# To do so, we will use a similar lattice equipped with a sextupole, which we will
# use to excite the resonance.

perturbed_lattice = LatticeGenerator.generate_onesext_cas_lattice()
madx.exit()  # close the previous rpc connection

madx = Madx(stdout=False)
madx.input(perturbed_lattice)
madx.input("ks1 = 0.1;")  # powering the sextupole

###############################################################################
# Let's get close to the third order resonance and track particles.

match_tunes_and_chromaticities(
    madx,
    None,
    "CAS3",
    q1_target=6.335,
    q2_target=6.29,
    dq1_target=100,
    dq2_target=100,
    varied_knobs=["kqf", "kqd", "ksf", "ksd"],
)

x_coords_sext, px_coords_sext, y_coords_sext, py_coords_sext = [], [], [], []

for starting_x in initial_x_coordinates:
    tracks_df = track_single_particle(
        madx, initial_coordinates=(starting_x, 0, 0, 0, 0, 0), nturns=n_turns
    )
    x_coords_sext.append(tracks_df["observation_point_1"].x.to_numpy())
    y_coords_sext.append(tracks_df["observation_point_1"].y.to_numpy())
    px_coords_sext.append(tracks_df["observation_point_1"].px.to_numpy())
    py_coords_sext.append(tracks_df["observation_point_1"].py.to_numpy())

###############################################################################
# Plotting the new phase space, we can clearly see the resonance's islands!

PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
    madx, x_coords_sext, px_coords_sext, plane="Horizontal", figsize=(10, 9)
)
plt.xlim(-0.015 * 1e3, 0.015 * 1e3)
plt.ylim(-0.015 * 1e3, 0.015 * 1e3)

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
#    - `~.cpymadtools.generators`: `~.generators.LatticeGenerator`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
#    - `~.cpymadtools.plotters`: `~.plotters.PhaseSpacePlotter`, `~.plotters.PhaseSpacePlotter.plot_courant_snyder_phase_space`, `~.plotters.PhaseSpacePlotter.plot_courant_snyder_phase_space_colored`
#    - `~.cpymadtools.track`: `~.track.track_single_particle`