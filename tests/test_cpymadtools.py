import math
import pathlib
import random
import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.constants import (
    CORRECTOR_LIMITS,
    FD_FAMILIES,
    LHC_CROSSING_SCHEMES,
    SPECIAL_FAMILIES,
    TWO_FAMILIES,
)
from pyhdtoolkit.cpymadtools.errors import switch_magnetic_errors
from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.latwiss import plot_latwiss, plot_machine_survey
from pyhdtoolkit.cpymadtools.matching import (
    get_closest_tune_approach,
    get_lhc_tune_and_chroma_knobs,
    match_tunes_and_chromaticities,
)
from pyhdtoolkit.cpymadtools.orbit import get_current_orbit_setup, lhc_orbit_variables, setup_lhc_orbit
from pyhdtoolkit.cpymadtools.parameters import beam_parameters
from pyhdtoolkit.cpymadtools.plotters import (
    AperturePlotter,
    DynamicAperturePlotter,
    PhaseSpacePlotter,
    TuneDiagramPlotter,
)
from pyhdtoolkit.cpymadtools.ptc import get_amplitude_detuning, get_rdts
from pyhdtoolkit.cpymadtools.special import (
    _all_lhc_arcs,
    _get_k_strings,
    apply_lhc_colinearity_knob,
    apply_lhc_coupling_knob,
    apply_lhc_rigidity_waist_shift_knob,
    deactivate_lhc_arc_sextupoles,
    make_sixtrack_output,
    power_landau_octupoles,
)

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()
GUIDO_LATTICE = INPUTS_DIR / "guido_lattice.madx"
LHC_SEQUENCE = INPUTS_DIR / "lhc_as-built.seq"
LHC_OPTICS = INPUTS_DIR / "opticsfile.22"


class TestAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_aperture(self, tmp_path):
        savefig_dir = tmp_path / "test_plot_aperture"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "aperture.png"

        beam_fb = beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3, verbose=True)
        madx = Madx(stdout=False)
        madx.call(str(GUIDO_LATTICE))
        figure = AperturePlotter.plot_aperture(madx, beam_fb, xlimits=(0, 20), savefig=saved_fig)
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


class TestErrors:
    pass


class TestLatticeGenerator:
    def test_base_cas_lattice_generation(self):
        base_cas_lattice = LatticeGenerator.generate_base_cas_lattice()
        assert isinstance(base_cas_lattice, str)
        assert len(base_cas_lattice) == 1493

    def test_onesext_cas_lattice(self):
        onesext_cas_lattice = LatticeGenerator.generate_onesext_cas_lattice()
        assert isinstance(onesext_cas_lattice, str)
        assert len(onesext_cas_lattice) == 2051

    def test_oneoct_cas_lattice(self):
        oneoct_cas_lattice = LatticeGenerator.generate_oneoct_cas_lattice()
        assert isinstance(oneoct_cas_lattice, str)
        assert len(oneoct_cas_lattice) == 2050

    def test_tripleterrors_study_reference(self):
        tripleterrors_study_reference = LatticeGenerator.generate_tripleterrors_study_reference()
        assert isinstance(tripleterrors_study_reference, str)
        assert len(tripleterrors_study_reference) == 1617

    @pytest.mark.parametrize(
        "randseed, tferror",
        [
            ("", ""),
            ("95", "195"),
            ("105038", "0.001"),
            (str(random.randint(0, 1e7)), str(random.randint(0, 1e7))),
            (random.randint(0, 1e7), random.randint(0, 1e7)),
        ],
    )
    def test_tripleterrors_study_tferror_job(self, randseed, tferror):
        tripleterrors_study_tferror_job = LatticeGenerator.generate_tripleterrors_study_tferror_job(
            rand_seed=randseed, tf_error=tferror,
        )
        assert isinstance(tripleterrors_study_tferror_job, str)
        assert len(tripleterrors_study_tferror_job) == 2521 + len(str(randseed)) + len(str(tferror))
        assert f"eoption, add, seed = {randseed};" in tripleterrors_study_tferror_job
        assert f"B2r = {tferror};" in tripleterrors_study_tferror_job

    @pytest.mark.parametrize(
        "randseed, mserror",
        [
            ("", ""),
            ("95", "195"),
            ("105038", "0.001"),
            (str(random.randint(0, 1e7)), str(random.randint(0, 1e7))),
            (random.randint(0, 1e7), random.randint(0, 1e7)),
        ],
    )
    def test_tripleterrors_study_mserror_job(self, randseed, mserror):
        tripleterrors_study_mserror_job = LatticeGenerator.generate_tripleterrors_study_mserror_job(
            rand_seed=randseed, ms_error=mserror,
        )
        assert isinstance(tripleterrors_study_mserror_job, str)
        assert len(tripleterrors_study_mserror_job) == 2384 + len(str(randseed)) + len(str(mserror))
        assert f"eoption, add, seed = {randseed};" in tripleterrors_study_mserror_job
        assert f"ealign, ds := {mserror} * 1E-3 * TGAUSS(GCUTR);" in tripleterrors_study_mserror_job


class TestLaTwiss:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )
        figure = plot_latwiss(
            cpymad_instance=madx,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_with_elements(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_survey"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "survey.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        figure = plot_machine_survey(
            cpymad_instance=madx, show_elements=True, high_orders=True, figsize=(20, 15), savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_without_elements(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        return plot_machine_survey(
            cpymad_instance=madx, show_elements=False, high_orders=True, figsize=(20, 15)
        )


class TestMatching:
    @pytest.mark.parametrize("beam", [1, 2, 3, 4])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_lhc_tune_and_chroma_knobs(self, beam, telescopic_squeeze):
        expected_beam = 2 if beam == 4 else beam
        expected_suffix = "_sq" if telescopic_squeeze else ""
        assert get_lhc_tune_and_chroma_knobs("LHC", beam, telescopic_squeeze) == (
            f"dQx.b{expected_beam}{expected_suffix}",
            f"dQy.b{expected_beam}{expected_suffix}",
            f"dQpx.b{expected_beam}{expected_suffix}",
            f"dQpy.b{expected_beam}{expected_suffix}",
        )

    @pytest.mark.parametrize("beam", [1, 2, 3, 4])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_hllhc_tune_and_chroma_knobs(self, beam, telescopic_squeeze):
        expected_beam = 2 if beam == 4 else beam
        expected_suffix = "_sq" if telescopic_squeeze else ""
        assert get_lhc_tune_and_chroma_knobs("HLLHC", beam, telescopic_squeeze) == (
            f"kqtf.b{expected_beam}{expected_suffix}",
            f"kqtd.b{expected_beam}{expected_suffix}",
            f"ksf.b{expected_beam}{expected_suffix}",
            f"ksd.b{expected_beam}{expected_suffix}",
        )

    def test_get_knobs_fails_on_unknown_accelerator(self, caplog):
        with pytest.raises(NotImplementedError):
            _ = get_lhc_tune_and_chroma_knobs("not_an_accelerator")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("q1_target, q2_target", [(6.335, 6.29), (6.34, 6.27), (6.38, 6.27)])
    @pytest.mark.parametrize("dq1_target, dq2_target", [(100, 100), (95, 95), (105, 105)])
    def test_tune_and_chroma_matching(self, q1_target, q2_target, dq1_target, dq2_target):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)

        assert madx.table.summ.q1[0] != q1_target
        assert madx.table.summ.q2[0] != q2_target
        assert madx.table.summ.dq1[0] != dq1_target
        assert madx.table.summ.dq2[0] != dq2_target

        match_tunes_and_chromaticities(
            cpymad_instance=madx,
            sequence="CAS3",
            q1_target=q1_target,
            q2_target=q2_target,
            dq1_target=dq1_target,
            dq2_target=dq2_target,
            varied_knobs=["kqf", "kqd", "ksf", "ksd"],
        )

        assert math.isclose(madx.table.summ.q1[0], q1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.q2[0], q2_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.dq1[0], dq1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.dq2[0], dq2_target, rel_tol=1e-3)

    def test_closest_tune_approach(self, _prepared_lhc_madx):
        """Using LHC lattice."""
        madx = _prepared_lhc_madx
        apply_lhc_coupling_knob(madx, 2e-3)
        match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)

        knobs = get_lhc_tune_and_chroma_knobs("lhc")
        knobs_before = {knob: madx.globals[knob] for knob in knobs}
        cminus = get_closest_tune_approach(madx, "lhc", "lhcb1")
        knobs_after = {knob: madx.globals[knob] for knob in knobs}

        assert math.isclose(cminus, 2e-3, rel_tol=5e-2)
        assert knobs_after == knobs_before


class TestOrbit:
    def test_lhc_orbit_variables(self):
        assert lhc_orbit_variables() == (
            [
                "on_crab1",
                "on_crab5",
                "on_x1",
                "on_sep1",
                "on_o1",
                "on_oh1",
                "on_ov1",
                "on_x2",
                "on_sep2",
                "on_o2",
                "on_oe2",
                "on_a2",
                "on_oh2",
                "on_ov2",
                "on_x5",
                "on_sep5",
                "on_o5",
                "on_oh5",
                "on_ov5",
                "on_phi_IR5",
                "on_x8",
                "on_sep8",
                "on_o8",
                "on_a8",
                "on_sep8h",
                "on_x8v",
                "on_oh8",
                "on_ov8",
                "on_alice",
                "on_sol_alice",
                "on_lhcb",
                "on_sol_atlas",
                "on_sol_cms",
                "phi_IR1",
                "phi_IR2",
                "phi_IR5",
                "phi_IR8",
            ],
            {"on_ssep1": "on_sep1", "on_xx1": "on_x1", "on_ssep5": "on_sep5", "on_xx5": "on_x5"},
        )

    def test_lhc_orbit_setup_fals_on_unknown_scheme(self, _prepared_lhc_madx, caplog):
        madx = _prepared_lhc_madx

        with pytest.raises(ValueError):
            setup_lhc_orbit(madx, scheme="unknown")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("scheme", list(LHC_CROSSING_SCHEMES.keys()))
    def test_lhc_orbit_setup(self, scheme, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        setup_lhc_orbit(madx, scheme=scheme)
        variables, special = lhc_orbit_variables()

        for orbit_variable in variables:
            value = LHC_CROSSING_SCHEMES[scheme].get(orbit_variable, 0)
            assert madx.globals[orbit_variable] == value

        for special_variable, copy_from in special.items():
            assert madx.globals[special_variable] == madx.globals[copy_from]

    def test_get_orbit_setup(self, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        setup_lhc_orbit(madx, scheme="flat")
        setup = get_current_orbit_setup(madx)

        assert isinstance(setup, dict)
        assert all(orbit_var in setup.keys() for orbit_var in lhc_orbit_variables()[0])
        assert all(special_var in setup.keys() for special_var in lhc_orbit_variables()[1])


class TestParameters:
    @pytest.mark.parametrize(
        "pc_gev, en_x_m, en_y_m, delta_p, verbosity, result_dict",
        [
            (
                1.9,
                5e-6,
                5e-6,
                2e-3,
                False,
                {
                    "pc_GeV": 1.9,
                    "B_rho_Tm": 6.3376399999999995,
                    "E_0_GeV": 0.9382720813,
                    "E_tot_GeV": 2.1190456574946737,
                    "E_kin_GeV": 1.1807735761946736,
                    "gamma_r": 2.258455409393277,
                    "beta_r": 0.8966300434726596,
                    "en_x_m": 5e-06,
                    "en_y_m": 5e-06,
                    "eg_x_m": 2.469137056052632e-06,
                    "eg_y_m": 2.469137056052632e-06,
                    "deltap_p": 0.002,
                },
            ),
            (
                19,
                5e-6,
                5e-6,
                2e-4,
                True,
                {
                    "pc_GeV": 19,
                    "B_rho_Tm": 63.3764,
                    "E_0_GeV": 0.9382720813,
                    "E_tot_GeV": 19.023153116624673,
                    "E_kin_GeV": 18.084881035324674,
                    "gamma_r": 20.274666054506927,
                    "beta_r": 0.9987828980567665,
                    "en_x_m": 5e-06,
                    "en_y_m": 5e-06,
                    "eg_x_m": 2.4691370560526314e-07,
                    "eg_y_m": 2.4691370560526314e-07,
                    "deltap_p": 0.0002,
                },
            ),
        ],
    )
    def test_beam_parameters(self, pc_gev, en_x_m, en_y_m, delta_p, result_dict, verbosity):
        assert beam_parameters(pc_gev, en_x_m, en_y_m, delta_p, verbosity) == result_dict


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


class TestPTC:
    pass


class TestSpecial:
    def test_all_lhc_arcs(self):
        assert _all_lhc_arcs(1) == ["A12B1", "A23B1", "A34B1", "A45B1", "A56B1", "A67B1", "A78B1", "A81B1"]
        assert _all_lhc_arcs(2) == ["A12B2", "A23B2", "A34B2", "A45B2", "A56B2", "A67B2", "A78B2", "A81B2"]

    @pytest.mark.parametrize(
        "orient, result",
        [
            ["straight", ["K0L", "K1L", "K2L", "K3L", "K4L"]],
            ["skew", ["K0SL", "K1SL", "K2SL", "K3SL", "K4SL"]],
            ["both", ["K0L", "K0SL", "K1L", "K1SL", "K2L", "K2SL", "K3L", "K3SL", "K4L", "K4SL"]],
        ],
    )
    def test_k_strings(self, orient, result):
        assert _get_k_strings(stop=5, orientation=orient) == result

    def test_k_strings_fails_on_wront_orient(self, caplog):
        with pytest.raises(ValueError):
            _ = _get_k_strings(orientation="qqq")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("current", [100, 200, 300, 400, 500])
    def test_landau_powering(self, current, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        brho = madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
        strength = current / madx.globals.Imax_MO * madx.globals.Kmax_MO / brho
        power_landau_octupoles(madx, mo_current=current, beam=1)

        for arc in _all_lhc_arcs(beam=1):
            for fd in "FD":
                assert madx.globals[f"KO{fd}.{arc}"] == strength

    def test_landau_powering_fails_on_missing_nrj(self, caplog):
        madx = Madx(stdout=False)

        with pytest.raises(EnvironmentError):
            power_landau_octupoles(madx, 100, 1)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("current", [100, 200, 300, 400, 500])
    def test_depower_arc_sextupoles(self, current, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        deactivate_lhc_arc_sextupoles(madx, beam=1)

        for arc in _all_lhc_arcs(beam=1):
            for fd in "FD":
                for i in (1, 2):
                    assert madx.globals[f"KS{fd}{i:d}.{arc}"] == 0.0

    def test_prepare_sixtrack_output(self, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        make_sixtrack_output(madx, energy=6500)

        assert madx.globals["VRF400"] == 16
        assert madx.globals["LAGRF400.B1"] == 0.5
        assert madx.globals["LAGRF400.B2"] == 0.0

    @pytest.mark.parametrize("knob_value", list(range(-10, 11, 2)))
    @pytest.mark.parametrize("IR", [1, 2, 5, 8])
    def test_colinearity_knob(self, knob_value, IR, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        apply_lhc_colinearity_knob(madx, colinearity_knob_value=knob_value, ir=IR)

        assert madx.globals[f"KQSX3.R{IR:d}"] == knob_value * 1e-4
        assert madx.globals[f"KQSX3.L{IR:d}"] == -1 * knob_value * 1e-4

    def test_rigidity_knob_fails_on_invalid_side(self, caplog, _prepared_lhc_madx):
        madx = _prepared_lhc_madx

        with pytest.raises(ValueError):
            apply_lhc_rigidity_waist_shift_knob(madx, 1, 1, "invalid")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("knob_value", [1e-3, 3e-3, 5e-5])
    def test_coupling_knob(self, knob_value, _prepared_lhc_madx):
        madx = _prepared_lhc_madx
        apply_lhc_coupling_knob(madx, coupling_knob=knob_value, beam=1)
        assert madx.globals[f"CMRS.b1"] == knob_value


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


# ---------------------- Private Utilities ---------------------- #


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


@pytest.fixture()
def _prepared_lhc_madx() -> Madx:
    madx = Madx(stdout=False)
    madx.input(LHC_SEQUENCE.read_text())  # could call but fails on Windows with Python 3.7
    madx.input(LHC_OPTICS.read_text())  # could call but fails on Windows with Python 3.7
    # madx.call(str(LHC_SEQUENCE))
    # madx.call(str(LHC_OPTICS))

    NRJ = madx.globals["NRJ"] = 6500
    brho = madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
    geometric_emit = madx.globals["geometric_emit"] = 3.75e-6 / (madx.globals["NRJ"] / 0.938)
    madx.command.beam(
        sequence="lhcb1",
        bv=1,
        energy=NRJ,
        particle="proton",
        npart=1.0e10,
        kbunch=1,
        ex=geometric_emit,
        ey=geometric_emit,
    )
    madx.command.use(sequence="lhcb1")
    return madx