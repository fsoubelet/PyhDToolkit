import pathlib

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


class TestAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_aperture_cell_injection(self, tmp_path, _injection_aperture_tolerances_lhc_madx):
        savefig_dir = tmp_path / "test_plot_envelope"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "aperture.png"

        madx = _injection_aperture_tolerances_lhc_madx
        madx.command.twiss(centre=True)
        twiss_df = madx.table.twiss.dframe().copy()
        ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]
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
        savefig_dir = tmp_path / "test_plot_envelope"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "aperture.png"

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
        savefig_dir = tmp_path / "test_plot_envelope"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "envelope.png"

        beam_fb = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
        madx = Madx(stdout=False)
        madx.call(str(GUIDO_LATTICE))
        figure = BeamEnvelopePlotter.plot_envelope(madx, beam_fb, xlimits=(0, 20), savefig=saved_fig)
        assert saved_fig.is_file()
        return figure


class TestCrossingSchemePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_crossing_schemes(self, tmp_path, _cycled_lhc_sequences):
        savefig_dir = tmp_path / "test_plot_envelope"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "crossings.png"

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
    @pytest.mark.parametrize("max_order", [0, 10, -5])
    def test_plot_blank_tune_diagram_fails_on_too_high_order(self, max_order, caplog):
        with pytest.raises(ValueError):
            _ = TuneDiagramPlotter.plot_blank_tune_diagram(max_order=max_order)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_blank_tune_diagram(self):
        """Does not need any input."""
        return TuneDiagramPlotter.plot_blank_tune_diagram()

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_blank_tune_diagram_colored_by_resonance_order(self):
        return TuneDiagramPlotter.plot_blank_tune_diagram(differentiate_orders=True)

    @pytest.mark.parametrize("figure_title", ["", "Tune Diagram"])
    @pytest.mark.parametrize("legend_title", ["Resonance Lines"])
    @pytest.mark.parametrize("max_order", [2, 3, 4, 5])
    @pytest.mark.parametrize("differentiate", [False, True])
    def test_plot_blank_tune_diagram_arguments(self, figure_title, legend_title, max_order, differentiate):
        figure = TuneDiagramPlotter.plot_blank_tune_diagram(
            title=figure_title,
            legend_title=legend_title,
            max_order=max_order,
            differentiate_orders=differentiate,
        )
        assert figure.axes[0].get_title() == figure_title
        assert isinstance(figure.axes[0].legend().get_title(), matplotlib.text.Text)
