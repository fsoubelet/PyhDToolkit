import pathlib

from typing import Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.plotters import (
    AperturePlotter,
    BeamEnvelopePlotter,
    CrossingSchemePlotter,
    DynamicAperturePlotter,
    LatticePlotter,
    PhaseSpacePlotter,
    TuneDiagramPlotter,
)
from pyhdtoolkit.cpymadtools.track import track_single_particle
from pyhdtoolkit.optics.beam import compute_beam_parameters

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
GUIDO_LATTICE = INPUTS_DIR / "madx" / "guido_lattice.madx"
BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()
ELETTRA_LATTICE = INPUTS_DIR / "madx" / "elettra2_v15_VADER_2.3T.madx"
ELETTRA_OPTICS = INPUTS_DIR / "madx" / "optics_elettra2_v15_VADER_2.3T.madx"


class TestAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_aperture_cell_injection(self, tmp_path, _injection_aperture_tolerances_lhc_madx):
        saved_fig = tmp_path / "aperture.png"

        madx = _injection_aperture_tolerances_lhc_madx
        madx.command.twiss(centre=True)
        twiss_df = madx.table.twiss.dframe().copy()
        figure = AperturePlotter.plot_aperture(
            madx,
            title="Arc 56 Cell, Injection Optics Aperture Tolerance",
            plot_bpms=True,
            xlimits=(14_084.5, 14_191.3),  # cell somewhere in arc 56
            aperture_ylim=(0, 25),
            k0l_lim=(-3e-2, 3e-2),
            k1l_lim=(-4e-2, 4e-2),
            k2l_lim=(-5e-2, 5e-2),
            color="brown",
            savefig=saved_fig,
        )

        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_aperture_ir5_collision(self, tmp_path, _collision_aperture_tolerances_lhc_madx):
        saved_fig = tmp_path / "aperture.png"

        madx = _collision_aperture_tolerances_lhc_madx
        madx.command.twiss(centre=True)
        twiss_df = madx.table.twiss.dframe().copy()
        ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

        figure = AperturePlotter.plot_aperture(
            madx,
            title="IR 5, Injection Optics Aperture Tolerance",
            plot_bpms=True,
            xlimits=(ip5s - 80, ip5s + 80),
            aperture_ylim=(0, 25),
            k0l_lim=(-4e-4, 4e-4),
            color="brown",
            savefig=saved_fig,
        )

        assert saved_fig.is_file()
        return figure


class TestBeamEnvelopePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_envelope(self, tmp_path):
        saved_fig = tmp_path / "envelope.png"
        beam_fb = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
        madx = Madx(stdout=False)
        madx.call(str(GUIDO_LATTICE))
        figure = BeamEnvelopePlotter.plot_envelope(madx, beam_fb, xlimits=(0, 20), savefig=saved_fig)
        assert saved_fig.is_file()
        return figure


class TestCrossingSchemePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_crossing_schemes(self, tmp_path, _cycled_lhc_sequences):
        saved_fig = tmp_path / "crossings.png"

        madx = _cycled_lhc_sequences
        figure = CrossingSchemePlotter.plot_two_lhc_ips_crossings(
            madx, first_ip=1, second_ip=5, figsize=(18, 11), ir_limit=250, savefig=saved_fig
        )

        assert saved_fig.is_file()
        return figure


class TestDynamicAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_dynamic_aperture(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        saved_fig = tmp_path / "dynamic_aperture.png"
        n_particles = 100
        with Madx(stdout=False) as madx:
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


class TestLatticePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        saved_fig = tmp_path / "latwiss.png"

        with Madx(stdout=False) as madx:
            madx.input(BASE_LATTICE)
            match_tunes_and_chromaticities(
                madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
            )
            figure = LatticePlotter.plot_latwiss(
                madx=madx,
                title="Project 3 Base Lattice",
                xlimits=(-50, 1_050),
                beta_ylim=(5, 75),
                k2l_lim=(-0.25, 0.25),
                plot_bpms=True,
                savefig=saved_fig,
            )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss_with_dipole_k1(self):
        """Using ELETTRA2.0 lattice provided by Axel."""
        elettra_parameters = {"ON_SEXT": 1, "ON_OCT": 1, "ON_RF": 1, "NRJ_GeV": 2.4, "DELTAP": 0.00095}

        with Madx(stdout=False) as madx:
            with madx.batch():
                madx.globals.update(elettra_parameters)
            madx.call(str(ELETTRA_LATTICE))
            madx.call(str(ELETTRA_OPTICS))
            madx.use(sequence="ring")
            madx.command.twiss(sequence="ring")
            init_twiss = madx.table.twiss.dframe().copy()
            x0 = init_twiss.s[init_twiss.name == "ll:1"][0]
            x1 = init_twiss.s[init_twiss.name == "ll:3"][0]
            figure = LatticePlotter.plot_latwiss(
                madx=madx,
                title="Elettra Cell",
                xlimits=(x0, x1),
                k0l_lim=(-7e-2, 7e-2),
                k1l_lim=(-1.5, 1.5),
                disp_ylim=(-madx.table.twiss.dx.max() * 2, madx.table.twiss.dx.max() * 2),
                plot_dipole_k1=True,
                lw=2,
            )
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_with_elements(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        saved_fig = tmp_path / "survey.png"
        with Madx(stdout=False) as madx:
            madx.input(BASE_LATTICE)
            figure = LatticePlotter.plot_machine_survey(
                madx=madx, show_elements=True, high_orders=True, figsize=(20, 15), savefig=saved_fig
            )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_without_elements(self):
        """Using my CAS 19 project's base lattice."""
        with Madx(stdout=False) as madx:
            madx.input(BASE_LATTICE)
            return LatticePlotter.plot_machine_survey(
                madx=madx, show_elements=False, high_orders=True, figsize=(20, 15)
            )


class TestPhaseSpacePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_horizontal_courant_snyder_phase_space(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        saved_fig = tmp_path / "phase_space.png"
        with Madx(stdout=False) as madx:
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
        with Madx(stdout=False) as madx:
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
        with Madx(stdout=False) as madx:
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
        saved_fig = tmp_path / "colored_phase_space.png"

        with Madx(stdout=False) as madx:
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
        with Madx(stdout=False) as madx:
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
        with Madx(stdout=False) as madx:
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
    @pytest.mark.parametrize("max_order", [0, 10, -5])
    def test_plot_tune_diagram_fails_on_too_high_order(self, max_order, caplog):
        with pytest.raises(ValueError):
            _ = TuneDiagramPlotter.plot_tune_diagram(max_order=max_order)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_tune_diagram(self):
        """Does not need any input."""
        return TuneDiagramPlotter.plot_tune_diagram()

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_tune_diagram_colored_by_resonance_order(self):
        return TuneDiagramPlotter.plot_tune_diagram(differentiate_orders=True)

    @pytest.mark.parametrize("figure_title", ["", "Tune Diagram"])
    @pytest.mark.parametrize("legend_title", ["Resonance Lines"])
    @pytest.mark.parametrize("max_order", [2, 3, 4, 5])
    @pytest.mark.parametrize("differentiate", [False, True])
    def test_plot_tune_diagram_arguments(self, figure_title, legend_title, max_order, differentiate):
        figure = TuneDiagramPlotter.plot_tune_diagram(
            title=figure_title,
            legend_title=legend_title,
            max_order=max_order,
            differentiate_orders=differentiate,
        )
        assert figure.axes[0].get_title() == figure_title
        assert isinstance(figure.axes[0].legend().get_title(), matplotlib.text.Text)


# ----- Fixtures ----- #


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
