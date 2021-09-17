import pathlib

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.plotters import (
    DynamicAperturePlotter,
    EnvelopePlotter,
    PhaseSpacePlotter,
    TuneDiagramPlotter,
)
from pyhdtoolkit.optics.beam import compute_beam_parameters

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
GUIDO_LATTICE = INPUTS_DIR / "guido_lattice.madx"
BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


class TestDynamicAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_dynamic_aperture(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_aperture"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "dynamic_aperture.png"

        n_particles = 100
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, y_coords_stable, _, _ = _perform_tracking_for_coordinates(madx)
        x_coords_stable = np.array(x_coords_stable)
        y_coords_stable = np.array(y_coords_stable)
        figure = DynamicAperturePlotter.plot_dynamic_aperture(
            x_coords_stable, y_coords_stable, n_particles=n_particles, savefig=saved_fig
        )
        assert saved_fig.is_file()
        return figure


class TestEnvelopePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_envelope(self, tmp_path):
        savefig_dir = tmp_path / "test_plot_envelope"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "envelope.png"

        beam_fb = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
        madx = Madx(stdout=False)
        madx.call(str(GUIDO_LATTICE))
        figure = EnvelopePlotter.plot_envelope(madx, beam_fb, xlimits=(0, 20), savefig=saved_fig)
        assert saved_fig.is_file()
        return figure


class TestPhaseSpacePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_horizontal_courant_snyder_phase_space(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "phase_space.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space(
            madx, x_coords_stable, px_coords_stable, plane="Horizontal", savefig=saved_fig
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_vertical_courant_snyder_phase_space(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space(
            madx, x_coords_stable, px_coords_stable, plane="Vertical"
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        return figure

    def test_plot_courant_snyder_phase_space_wrong_plane_input(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, px_coords_stable = np.array([]), np.array([])  # no need for tracking
        with pytest.raises(ValueError):
            _ = PhaseSpacePlotter.plot_courant_snyder_phase_space(
                madx, x_coords_stable, px_coords_stable, plane="invalid_plane"
            )

    @pytest.mark.mpl_image_compare(tolerance=20, savefig_kwargs={"dpi": 200})
    def test_plot_horizontal_courant_snyder_phase_space_colored(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "colored_phase_space.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
            madx, x_coords_stable, px_coords_stable, plane="Horizontal", savefig=saved_fig
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, savefig_kwargs={"dpi": 200})
    def test_plot_vertical_courant_snyder_phase_space_colored(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
            madx, x_coords_stable, px_coords_stable, plane="Vertical"
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        return figure

    def test_plot_courant_snyder_phase_space_colored_wrong_plane_input(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, px_coords_stable = np.array([]), np.array([])  # no need for tracking
        with pytest.raises(ValueError):
            _ = PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
                madx, x_coords_stable, px_coords_stable, plane="invalid_plane"
            )


class TestTuneDiagramPlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_blank_tune_diagram(self):
        """Does not need any input."""
        figure = TuneDiagramPlotter.plot_blank_tune_diagram()
        plt.xlim(0, 0.5)
        plt.ylim(0, 0.5)
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_tune_diagram(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "tune_diagram.png"

        n_particles = 100
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        x_coords_stable = np.array(x_coords_stable)
        qxs_stable, xgood_stable = [], []

        for particle in range(n_particles):
            if np.isnan(x_coords_stable[particle]).any():
                qxs_stable.append(0)
                xgood_stable.append(False)
            else:
                signal = x_coords_stable[particle]
                signal = np.array(signal)
                try:
                    qxs_stable.append(pnf.naff(signal, n_turns, 1, 0, False)[0][1])
                    xgood_stable.append(True)
                except:
                    qxs_stable.append(0)
                    xgood_stable.append(False)

        qxs_stable = np.array(qxs_stable)
        xgood_stable = np.array(xgood_stable)
        figure = TuneDiagramPlotter.plot_tune_diagram(madx, qxs_stable, xgood_stable, savefig=saved_fig)
        plt.xlim(0, 0.4)
        plt.ylim(0, 0.4)
        assert saved_fig.is_file()
        return figure


# ----- Fixtures ----- #


def _perform_tracking_for_coordinates(cpymad_instance) -> tuple:
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
    x_coords_stable, px_coords_stable, y_coords_stable, py_coords_stable = [], [], [], []

    for _, starting_x in enumerate(initial_x_coordinates):
        cpymad_instance.command.track()
        cpymad_instance.command.start(X=starting_x, PX=0, Y=0, PY=0, T=0, PT=0)
        cpymad_instance.command.run(turns=n_turns)
        cpymad_instance.command.endtrack()

        x_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["x"].to_numpy())
        y_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["y"].to_numpy())
        px_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["px"].to_numpy())
        py_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["py"].to_numpy())
    return x_coords_stable, y_coords_stable, px_coords_stable, py_coords_stable
