from functools import partial
from typing import Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools._generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.track import track_single_particle
from pyhdtoolkit.plotting.phasespace import (
    plot_courant_snyder_phase_space,
    plot_courant_snyder_phase_space_colored,
)

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_horizontal_courant_snyder_phase_space():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_cas3(madx)
        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        figure, ax = plt.subplots(figsize=(10, 10))
        plot_courant_snyder_phase_space(madx, x_coords_stable, px_coords_stable, plane="horizontal")
        ax.set_xlim(-20e-3, 18e-3)
        ax.set_ylim(-18e-3, 22e-3)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_horizontal_courant_snyder_phase_space_colored():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_cas3(madx)
        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        figure, ax = plt.subplots(figsize=(10, 10))
        plot_courant_snyder_phase_space_colored(madx, x_coords_stable, px_coords_stable, plane="Horizontal")
        ax.set_xlim(-20e-3, 18e-3)
        ax.set_ylim(-18e-3, 22e-3)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_vertical_courant_snyder_phase_space():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_cas3(madx)
        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        figure, ax = plt.subplots(figsize=(10, 10))
        plot_courant_snyder_phase_space(madx, x_coords_stable, px_coords_stable, plane="vertical")
        ax.set_xlim(-35e-3, 35e-3)
        ax.set_ylim(-35e-3, 35e-3)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_vertical_courant_snyder_phase_space_colored():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_cas3(madx)
        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        figure, ax = plt.subplots(figsize=(10, 10))
        plot_courant_snyder_phase_space_colored(madx, x_coords_stable, px_coords_stable, plane="Vertical")
        ax.set_xlim(-35e-3, 35e-3)
        ax.set_ylim(-35e-3, 35e-3)
    return figure


def test_plot_courant_snyder_phase_space_wrong_plane_input():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_cas3(madx)
        x_coords_stable, px_coords_stable = np.array([]), np.array([])  # no need for tracking

        with pytest.raises(ValueError):
            fig, ax = plt.subplots()
            plot_courant_snyder_phase_space(madx, x_coords_stable, px_coords_stable, plane="invalid_plane")


def test_plot_courant_snyder_phase_space_colored_wrong_plane_input():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_cas3(madx)
        x_coords_stable, px_coords_stable = np.array([]), np.array([])  # no need for tracking
        with pytest.raises(ValueError):
            fig, ax = plt.subplots()
            plot_courant_snyder_phase_space_colored(madx, x_coords_stable, px_coords_stable, plane="invalid_plane")


# ----- Helpers and Fixtures ----- #

match_cas3 = partial(
    match_tunes_and_chromaticities,
    accelerator=None,
    sequence="CAS3",
    q1_target=6.335,
    q2_target=6.29,
    dq1_target=100,
    dq2_target=100,
    varied_knobs=["kqf", "kqd", "ksf", "ksd"],
)


def _perform_tracking_for_coordinates(madx: Madx) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Tracks 100 particles on 500 turns.
    This modifies inplace the state of the provided cpymad_instance.
    Args:
        cpymad_instance: an instantiated cpymad.madx.Madx object
    Returns:
        The x, y, px, py coordinates along the tracking.
    """
    # Toning the tracking down in particles / turns so it doesn't take too long (~20s?)
    n_particles = 100
    n_turns = 500
    initial_x_coordinates = np.linspace(1e-4, 0.05, n_particles)
    x_coords, px_coords, y_coords, py_coords = [], [], [], []

    for starting_x in initial_x_coordinates:
        tracks_df: dict = track_single_particle(
            madx, initial_coordinates=(starting_x, 0, 0, 0, 0, 0), nturns=n_turns, sequence="CAS3"
        )
        x_coords.append(tracks_df["observation_point_1"].x.to_numpy())
        y_coords.append(tracks_df["observation_point_1"].y.to_numpy())
        px_coords.append(tracks_df["observation_point_1"].px.to_numpy())
        py_coords.append(tracks_df["observation_point_1"].py.to_numpy())
    return x_coords, y_coords, px_coords, py_coords
