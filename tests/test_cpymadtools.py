import math
import pathlib
import random

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
import tfs

from cpymad.madx import Madx
from pandas import DataFrame
from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.constants import (  # for coverage
    CORRECTOR_LIMITS,
    DEFAULT_TWISS_COLUMNS,
    FD_FAMILIES,
    LHC_CROSSING_SCHEMES,
    SPECIAL_FAMILIES,
    TWO_FAMILIES,
)
from pyhdtoolkit.cpymadtools.errors import (
    misalign_lhc_ir_quadrupoles,
    misalign_lhc_triplets,
    switch_magnetic_errors,
)
from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.latwiss import plot_latwiss, plot_machine_survey
from pyhdtoolkit.cpymadtools.matching import (
    get_closest_tune_approach,
    get_lhc_tune_and_chroma_knobs,
    match_tunes_and_chromaticities,
)
from pyhdtoolkit.cpymadtools.orbit import (
    correct_lhc_orbit,
    get_current_orbit_setup,
    lhc_orbit_variables,
    setup_lhc_orbit,
)
from pyhdtoolkit.cpymadtools.parameters import query_beam_attributes
from pyhdtoolkit.cpymadtools.plotters import (
    AperturePlotter,
    DynamicAperturePlotter,
    PhaseSpacePlotter,
    TuneDiagramPlotter,
)
from pyhdtoolkit.cpymadtools.ptc import get_amplitude_detuning, get_rdts, ptc_track_particle, ptc_twiss
from pyhdtoolkit.cpymadtools.special import (
    _all_lhc_arcs,
    _get_k_strings,
    apply_lhc_colinearity_knob,
    apply_lhc_coupling_knob,
    apply_lhc_rigidity_waist_shift_knob,
    deactivate_lhc_arc_sextupoles,
    install_ac_dipole_as_kicker,
    install_ac_dipole_as_matrix,
    make_lhc_beams,
    make_lhc_thin,
    make_sixtrack_output,
    power_landau_octupoles,
    re_cycle_sequence,
    vary_independent_ir_quadrupoles,
)
from pyhdtoolkit.cpymadtools.track import track_single_particle
from pyhdtoolkit.cpymadtools.tune import get_footprint_lines, get_footprint_patches, make_footprint_table
from pyhdtoolkit.cpymadtools.twiss import get_ips_twiss, get_ir_twiss, get_twiss_tfs
from pyhdtoolkit.models.madx import MADXBeam
from pyhdtoolkit.optics.beam import compute_beam_parameters

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

        beam_fb = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
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
    def test_magnetic_errors_switch_no_kwargs(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        switch_magnetic_errors(madx)

        for order in range(1, 16):
            for ab in "AB":
                for sr in "sr":
                    assert madx.globals[f"ON_{ab}{order:d}{sr}"] == 0

    def test_magnetic_errors_switch_with_kwargs(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        random_kwargs = {}

        for order in range(1, 16):
            for ab in "AB":
                random_kwargs[f"{ab}{order:d}"] = random.randint(0, 20)

        switch_magnetic_errors(madx, **random_kwargs)

        for order in range(1, 16):
            for ab in "AB":
                for sr in "sr":
                    assert madx.globals[f"ON_{ab}{order:d}{sr}"] == random_kwargs[f"{ab}{order:d}"]

    @pytest.mark.parametrize("ip", [1, 2, 5, 8])
    @pytest.mark.parametrize("sides", ["R", "L", "RL", "r", "l", "rl"])
    @pytest.mark.parametrize("quadrupoles", [[1, 3, 5, 7, 9], list(range(1, 11))])
    def test_misalign_lhc_ir_quadrupoles(self, _non_matched_lhc_madx, ip, sides, quadrupoles):
        madx = _non_matched_lhc_madx
        misalign_lhc_ir_quadrupoles(
            madx,
            ip=ip,
            quadrupoles=quadrupoles,
            beam=1,
            sides=sides,
            dx="1E-3 * TGAUSS(2.5)",
            dpsi="1E-3 * TGAUSS(2.5)",
        )
        error_table = madx.table["ir_quads_errors"].dframe().copy()
        assert all(error_table["dx"] != 0)
        assert all(error_table["dpsi"] != 0)

    def test_misalign_lhc_ir_quadrupoles_specific_value(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        misalign_lhc_ir_quadrupoles(
            madx, ip=1, quadrupoles=list(range(1, 11)), beam=1, sides="RL", dy="0.001"
        )
        error_table = madx.table["ir_quads_errors"].dframe().copy()
        assert all(error_table["dy"] == 0.001)

    def test_misalign_lhc_ir_quadrupoles_raises_on_wrong_side(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        with pytest.raises(ValueError):
            misalign_lhc_ir_quadrupoles(madx, ip=8, quadrupoles=[1], beam=2, sides="Z", dy="0.001")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_misalign_lhc_ir_quadrupoles_raises_on_wrong_ip(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        with pytest.raises(ValueError):
            misalign_lhc_ir_quadrupoles(madx, ip=100, quadrupoles=[1], beam=2, sides="R", dy="0.001")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_misalign_lhc_ir_quadrupoles_raises_on_wrong_beam(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        with pytest.raises(ValueError):
            misalign_lhc_ir_quadrupoles(madx, ip=2, quadrupoles=[1], beam=10, sides="L", dy="0.001")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_misalign_lhc_triplets(self, _non_matched_lhc_madx):
        # for coverage as this calls `misalign_lhc_ir_quadrupoles` tested above
        madx = _non_matched_lhc_madx
        misalign_lhc_triplets(madx, ip=1, sides="RL", dx="1E-3 * TGAUSS(2.5)", dpsi="1E-3 * TGAUSS(2.5)")
        error_table = madx.table["triplet_errors"].dframe().copy()
        assert all(error_table["dx"] != 0)
        assert all(error_table["dpsi"] != 0)


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
    def test_plot_machine_survey_with_elements(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_survey"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "survey.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        figure = plot_machine_survey(
            madx=madx, show_elements=True, high_orders=True, figsize=(20, 15), savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_without_elements(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        return plot_machine_survey(madx=madx, show_elements=False, high_orders=True, figsize=(20, 15))


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
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_tune_and_chroma_matching(self, q1_target, q2_target, dq1_target, dq2_target, telescopic_squeeze):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.q1[0] != q1_target
        assert madx.table.summ.q2[0] != q2_target
        assert madx.table.summ.dq1[0] != dq1_target
        assert madx.table.summ.dq2[0] != dq2_target

        match_tunes_and_chromaticities(
            madx=madx,
            sequence="CAS3",
            q1_target=q1_target,
            q2_target=q2_target,
            dq1_target=dq1_target,
            dq2_target=dq2_target,
            varied_knobs=["kqf", "kqd", "ksf", "ksd"],
            telescopic_squeeze=telescopic_squeeze,
        )
        assert math.isclose(madx.table.summ.q1[0], q1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.q2[0], q2_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.dq1[0], dq1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.dq2[0], dq2_target, rel_tol=1e-3)

    @pytest.mark.parametrize("q1_target, q2_target", [(6.335, 6.29), (6.34, 6.27), (6.38, 6.27)])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_tune_only_matching(self, q1_target, q2_target, telescopic_squeeze):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.q1[0] != q1_target
        assert madx.table.summ.q2[0] != q2_target

        match_tunes_and_chromaticities(
            madx=madx,
            sequence="CAS3",
            q1_target=q1_target,
            q2_target=q2_target,
            varied_knobs=["kqf", "kqd"],
            telescopic_squeeze=telescopic_squeeze,
        )
        assert math.isclose(madx.table.summ.q1[0], q1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.q2[0], q2_target, rel_tol=1e-3)

    @pytest.mark.parametrize("dq1_target, dq2_target", [(100, 100), (95, 95), (105, 105)])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_chroma_only_matching(self, dq1_target, dq2_target, telescopic_squeeze):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.dq1[0] != dq1_target
        assert madx.table.summ.dq2[0] != dq2_target

        match_tunes_and_chromaticities(
            madx=madx,
            sequence="CAS3",
            dq1_target=dq1_target,
            dq2_target=dq2_target,
            varied_knobs=["ksf", "ksd"],
            telescopic_squeeze=telescopic_squeeze,
        )
        assert math.isclose(madx.table.summ.dq1[0], dq1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.dq2[0], dq2_target, rel_tol=1e-3)

    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_closest_tune_approach(self, _non_matched_lhc_madx, telescopic_squeeze):
        """Using LHC lattice."""
        madx = _non_matched_lhc_madx
        apply_lhc_coupling_knob(madx, 2e-3, telescopic_squeeze=telescopic_squeeze)
        match_tunes_and_chromaticities(
            madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=telescopic_squeeze
        )

        knobs = get_lhc_tune_and_chroma_knobs("lhc", telescopic_squeeze=telescopic_squeeze)
        knobs_before = {knob: madx.globals[knob] for knob in knobs}
        cminus = get_closest_tune_approach(madx, "lhc", "lhcb1", telescopic_squeeze=telescopic_squeeze)
        knobs_after = {knob: madx.globals[knob] for knob in knobs}  # should be put back

        assert math.isclose(cminus, 2e-3, rel_tol=1e-1)  # let's say 10% as MAD-X does what it can
        assert knobs_after == knobs_before

    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_closest_tune_approach_with_explicit_targets(self, _non_matched_lhc_madx, telescopic_squeeze):
        """Using LHC lattice."""
        madx = _non_matched_lhc_madx
        apply_lhc_coupling_knob(madx, 2e-3, telescopic_squeeze=telescopic_squeeze)
        match_tunes_and_chromaticities(
            madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=telescopic_squeeze
        )

        knobs = get_lhc_tune_and_chroma_knobs("lhc", telescopic_squeeze=telescopic_squeeze)
        knobs_before = {knob: madx.globals[knob] for knob in knobs}
        cminus = get_closest_tune_approach(
            madx, "lhc", "lhcb1", explicit_targets=(62.315, 60.315), telescopic_squeeze=telescopic_squeeze
        )
        knobs_after = {knob: madx.globals[knob] for knob in knobs}  # should be put back

        assert math.isclose(cminus, 2e-3, rel_tol=1e-1)  # let's say 10% as MAD-X does what it can
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

    def test_lhc_orbit_setup_fals_on_unknown_scheme(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx

        with pytest.raises(ValueError):
            setup_lhc_orbit(madx, scheme="unknown")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("scheme", list(LHC_CROSSING_SCHEMES.keys()))
    def test_lhc_orbit_setup(self, scheme, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        setup_lhc_orbit(madx, scheme=scheme)
        variables, special = lhc_orbit_variables()

        for orbit_variable in variables:
            value = LHC_CROSSING_SCHEMES[scheme].get(orbit_variable, 0)
            assert madx.globals[orbit_variable] == value

        for special_variable, copy_from in special.items():
            assert madx.globals[special_variable] == madx.globals[copy_from]

    def test_get_orbit_setup(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        setup_lhc_orbit(madx, scheme="flat")
        setup = get_current_orbit_setup(madx)

        assert isinstance(setup, dict)
        assert all(orbit_var in setup.keys() for orbit_var in lhc_orbit_variables()[0])
        assert all(special_var in setup.keys() for special_var in lhc_orbit_variables()[1])

    def test_orbit_correction(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
        _ = setup_lhc_orbit(madx, scheme="flat")
        make_lhc_beams(madx)
        madx.use(sequence="lhcb1")
        match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)
        assert madx.table.summ["xcorms"][0] == 0  # rms of horizontal CO

        madx.select(flag="error", pattern="MQ.13R3.B1")  # arc quad in sector 34
        madx.command.ealign(dx="1E-3")
        madx.twiss()
        assert madx.table.summ["xcorms"][0] > 1e-3

        correct_lhc_orbit(madx, sequence="lhcb1")
        assert math.isclose(madx.table.summ["xcorms"], 0, abs_tol=1e-5)


class TestParameters:
    def test_query_default_madx_beam(self):
        madx = Madx(stdout=False)
        beam = query_beam_attributes(madx)

        assert isinstance(beam, MADXBeam)
        for attribute in beam.dict():
            assert getattr(beam, attribute) == madx.beam[attribute]

    def test_query_lhc_madx_beam(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        beam = query_beam_attributes(madx)

        assert isinstance(beam, MADXBeam)
        for attribute in beam.dict():
            assert getattr(beam, attribute) == madx.beam[attribute]


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
    def test_amplitude_detuning_fails_on_high_order(self, caplog):
        madx = Madx(stdout=False)

        with pytest.raises(NotImplementedError):
            _ = get_amplitude_detuning(madx, order=5)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_amplitude_detuning(self, tmp_path, _ampdet_tfs_path, _matched_base_lattice):
        madx = _matched_base_lattice

        reference_df = tfs.read(_ampdet_tfs_path)
        ampdet_df = get_amplitude_detuning(madx, file=tmp_path / "here.tfs")

        assert (tmp_path / "here.tfs").is_file()
        assert_frame_equal(reference_df, ampdet_df)

    def test_rdts(self, tmp_path, _rdts_tfs_path):
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        reference_df = tfs.read(_rdts_tfs_path)
        rdts_df = get_rdts(madx, file=tmp_path / "here.tfs")

        assert (tmp_path / "here.tfs").is_file()
        assert_frame_equal(reference_df.set_index("NAME"), rdts_df.set_index("NAME"))

    def test_ptc_twiss(self, tmp_path, _matched_base_lattice, _ptc_twiss_tfs_path):
        madx = _matched_base_lattice
        ptc_twiss_df = ptc_twiss(madx, file=tmp_path / "here.tfs").reset_index(drop=True)
        reference_df = tfs.read(_ptc_twiss_tfs_path)

        assert (tmp_path / "here.tfs").is_file()
        assert_frame_equal(reference_df.drop(columns=["COMMENTS"]), ptc_twiss_df.drop(columns=["COMMENTS"]))

    @pytest.mark.parametrize("obs_points", [[], ["qf", "mb", "msf"]])
    def test_single_particle_ptc_track(self, _matched_base_lattice, obs_points):
        madx = _matched_base_lattice
        tracks_dict = ptc_track_particle(
            madx,
            sequence="CAS3",
            nturns=100,
            initial_coordinates=(1e-4, 0, 2e-4, 0, 0, 0),
            observation_points=obs_points,
        )

        assert isinstance(tracks_dict, dict)
        assert len(tracks_dict.keys()) == len(obs_points) + 1
        for tracks in tracks_dict.values():
            assert isinstance(tracks, DataFrame)
            assert all(
                [coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")]
            )

    def test_single_particle_ptc_track_with_onepass(self, _matched_base_lattice):
        madx = _matched_base_lattice
        tracks_dict = ptc_track_particle(
            madx, sequence="CAS3", nturns=100, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0), onetable=True,
        )

        assert isinstance(tracks_dict, dict)
        assert len(tracks_dict.keys()) == 1  # should be only one because of ONETABLE option
        assert "trackone" in tracks_dict.keys()
        tracks = tracks_dict["trackone"]
        assert isinstance(tracks, DataFrame)
        assert all(
            [coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")]
        )


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
    def test_landau_powering(self, current, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        brho = madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
        strength = current / madx.globals.Imax_MO * madx.globals.Kmax_MO / brho
        power_landau_octupoles(madx, mo_current=current, beam=1)

        for arc in _all_lhc_arcs(beam=1):
            for fd in "FD":
                assert madx.globals[f"KO{fd}.{arc}"] == strength

        power_landau_octupoles(madx, mo_current=current, beam=1, defective_arc=True)
        assert madx.globals["KOD.A56B1"] == strength * 4.65 / 6

    def test_landau_powering_fails_on_missing_nrj(self, caplog):
        madx = Madx(stdout=False)

        with pytest.raises(EnvironmentError):
            power_landau_octupoles(madx, 100, 1)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("current", [100, 200, 300, 400, 500])
    def test_depower_arc_sextupoles(self, current, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        deactivate_lhc_arc_sextupoles(madx, beam=1)

        for arc in _all_lhc_arcs(beam=1):
            for fd in "FD":
                for i in (1, 2):
                    assert madx.globals[f"KS{fd}{i:d}.{arc}"] == 0.0

    def test_prepare_sixtrack_output(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        make_sixtrack_output(madx, energy=6500)

        assert madx.globals["VRF400"] == 16
        assert madx.globals["LAGRF400.B1"] == 0.5
        assert madx.globals["LAGRF400.B2"] == 0.0

    @pytest.mark.parametrize("knob_value", [-5, 10])
    @pytest.mark.parametrize("IR", [1, 2, 5, 8])
    def test_colinearity_knob(self, knob_value, IR, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        apply_lhc_colinearity_knob(madx, colinearity_knob_value=knob_value, ir=IR)

        assert madx.globals[f"KQSX3.R{IR:d}"] == knob_value * 1e-4
        assert madx.globals[f"KQSX3.L{IR:d}"] == -1 * knob_value * 1e-4

    def test_rigidity_knob_fails_on_invalid_side(self, caplog, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx

        with pytest.raises(ValueError):
            apply_lhc_rigidity_waist_shift_knob(madx, 1, 1, "invalid")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("side", ["left", "right"])
    @pytest.mark.parametrize("knob_value", [1, 2])
    @pytest.mark.parametrize("IR", [1, 2, 5, 8])
    def test_rigidity_knob(self, side, knob_value, IR, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        right_knob, left_knob = (f"kqx.r{IR:d}", f"kqx.l{IR:d}")
        current_right_knob = madx.globals[right_knob]
        current_left_knob = madx.globals[left_knob]

        apply_lhc_rigidity_waist_shift_knob(madx, rigidty_waist_shift_value=knob_value, ir=IR, side=side)

        if side == "left":
            assert madx.globals[right_knob] == (1 - knob_value * 0.005) * current_right_knob
            assert madx.globals[left_knob] == (1 + knob_value * 0.005) * current_left_knob

        elif side == "right":
            assert madx.globals[right_knob] == (1 + knob_value * 0.005) * current_right_knob
            assert madx.globals[left_knob] == (1 - knob_value * 0.005) * current_left_knob

    @pytest.mark.parametrize("knob_value", [1e-3, 3e-3, 5e-5])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_coupling_knob(self, knob_value, _non_matched_lhc_madx, telescopic_squeeze):
        madx = _non_matched_lhc_madx
        apply_lhc_coupling_knob(madx, coupling_knob=knob_value, beam=1, telescopic_squeeze=telescopic_squeeze)
        knob_suffix = "_sq" if telescopic_squeeze else ""
        assert madx.globals[f"CMRS.b1{knob_suffix}"] == knob_value

    @pytest.mark.parametrize("energy", [450, 6500, 7000])
    def test_make_lhc_beams(self, energy, _bare_lhc_madx):
        madx = _bare_lhc_madx
        make_lhc_beams(madx, energy=energy)

        madx.use(sequence="lhcb1")
        assert madx.sequence.lhcb1.beam
        assert madx.sequence.lhcb1.beam.energy == energy

        madx.use(sequence="lhcb2")
        assert madx.sequence.lhcb2.beam
        assert madx.sequence.lhcb2.beam.energy == energy

    @pytest.mark.parametrize("top_turns", [1000, 6000, 10_000])
    def test_install_ac_dipole_as_kicker(self, top_turns, _matched_lhc_madx):
        madx = _matched_lhc_madx
        make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
        install_ac_dipole_as_kicker(
            madx, deltaqx=-0.01, deltaqy=0.012, sigma_x=1, sigma_y=1, top_turns=top_turns
        )
        ramp3 = 2100 + top_turns
        ramp4 = ramp3 + 2000

        assert "MKACH.6L4.B1" in madx.elements
        assert madx.elements["MKACH.6L4.B1"].l == 0
        assert madx.elements["MKACH.6L4.B1"].ramp1 == 100
        assert madx.elements["MKACH.6L4.B1"].ramp2 == 2100
        assert madx.elements["MKACH.6L4.B1"].ramp3 == ramp3
        assert madx.elements["MKACH.6L4.B1"].ramp4 == ramp4
        assert math.isclose(madx.elements["MKACH.6L4.B1"].at, 9846.0765, rel_tol=1e-2)
        assert math.isclose(madx.elements["MKACH.6L4.B1"].freq, 62.3, rel_tol=1e-2)

    def test_install_ac_dipole_matrix(self, _matched_lhc_madx):
        madx = _matched_lhc_madx
        twiss_before = madx.twiss().dframe().copy()
        install_ac_dipole_as_matrix(madx, deltaqx=-0.01, deltaqy=0.012)
        twiss_after = madx.twiss().dframe().copy()

        for acd_name in ("hacmap", "vacmap"):
            assert acd_name in madx.elements
            assert math.isclose(madx.elements[acd_name].at, 9846.0765, rel_tol=1e-2)

        assert math.isclose(madx.sequence.lhcb1.elements["hacmap"].rm21, 0.00044955222, rel_tol=1e-3)
        assert math.isclose(madx.sequence.lhcb1.elements["vacmap"].rm43, -0.00039327690, rel_tol=1e-3)

        with pytest.raises(AssertionError):
            assert_frame_equal(twiss_before, twiss_after)  # they should be different!

    def test_makethin_lhc(self, _matched_lhc_madx):
        """
        Little trick: if we haven't sliced properly, tracking will fail so we can check all is ok by
        attempting a tracking and seeing that it succeeds.
        """
        madx = _matched_lhc_madx
        make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)

        tracks_dict = track_single_particle(
            madx, initial_coordinates=(1e-4, 0, 1e-4, 0, 0, 0), nturns=10, sequence="lhcb1"
        )
        assert isinstance(tracks_dict, dict)
        tracks = tracks_dict["observation_point_1"]
        assert len(tracks) == 11  # nturns + 1 because $start coordinates also given by MAD-X
        assert all(
            [coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")]
        )

    def test_re_cycling(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
        make_lhc_beams(madx)
        madx.command.use(sequence="lhcb1")
        madx.twiss()
        twiss = madx.table.twiss.dframe().copy()
        assert "ip3" in twiss.name[0].lower()

    def test_vary_independent_ir_quads(self, _non_matched_lhc_madx):
        # still need to find how to test MAD-X has done this, but don't think we can test just a VARY
        madx = _non_matched_lhc_madx
        vary_independent_ir_quadrupoles(
            madx, quad_numbers=[4, 5, 6, 7, 8, 9, 10, 11, 12, 13], ip=1, sides=("r", "l")
        )

    def test_vary_independent_ir_quads_raises_on_wrong_side(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        with pytest.raises(ValueError):
            vary_independent_ir_quadrupoles(madx, quad_numbers=[4], ip=1, sides="Z")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_vary_independent_ir_quads_raises_on_wrong_ip(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        with pytest.raises(ValueError):
            vary_independent_ir_quadrupoles(madx, quad_numbers=[4], ip=100, sides="R")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_vary_independent_ir_quads_raises_on_wrong_quads(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        with pytest.raises(ValueError):
            vary_independent_ir_quadrupoles(madx, quad_numbers=[5, 20, 100], ip=1, sides="R")

        for record in caplog.records:
            assert record.levelname == "ERROR"


class TestTrack:
    @pytest.mark.parametrize("obs_points", [[], ["qf", "mb", "msf"]])
    def test_single_particle_tracking(self, _matched_base_lattice, obs_points):
        madx = _matched_base_lattice
        tracks_dict = track_single_particle(
            madx,
            sequence="CAS3",
            nturns=100,
            initial_coordinates=(1e-4, 0, 2e-4, 0, 0, 0),
            observation_points=obs_points,
        )

        assert isinstance(tracks_dict, dict)
        assert len(tracks_dict.keys()) == len(obs_points) + 1
        for tracks in tracks_dict.values():
            assert isinstance(tracks, DataFrame)
            assert all(
                [coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")]
            )

    def test_single_particle_tracking_with_onepass(self, _matched_base_lattice):
        madx = _matched_base_lattice
        tracks_dict = track_single_particle(
            madx, sequence="CAS3", nturns=100, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0), ONETABLE=True,
        )

        assert isinstance(tracks_dict, dict)
        assert len(tracks_dict.keys()) == 1  # should be only one because of ONETABLE option
        assert "trackone" in tracks_dict.keys()
        tracks = tracks_dict["trackone"]
        assert isinstance(tracks, DataFrame)
        assert all(
            [coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")]
        )


class TestTune:
    @pytest.mark.parametrize("sigma", [2, 5])
    @pytest.mark.parametrize("dense", [True, False])
    def test_make_footprint_table(self, _non_matched_lhc_madx, tmp_path, sigma, dense):
        export_file = tmp_path / "out.tfs"
        madx = _non_matched_lhc_madx
        re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
        orbit_scheme = setup_lhc_orbit(madx, scheme="flat")
        madx.use(sequence="lhcb1")
        match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=True)

        make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
        madx.use(sequence="lhcb1")

        expected_headers = [
            "NAME",
            "TYPE",
            "TITLE",
            "MADX_VERSION",
            "ORIGIN",
            "ANGLE",
            "AMPLITUDE",
            "DSIGMA",
            "ANGLE_MEANING",
            "AMPLITUDE_MEANING",
            "DSIGMA_MEANING",
        ]
        foot = make_footprint_table(madx, sigma=sigma, file=str(export_file))
        assert isinstance(foot, tfs.TfsDataFrame)
        assert all(header in foot.headers for header in expected_headers)
        assert foot.headers["ANGLE"] == 7  # hard-coded in the function
        assert foot.headers["AMPLITUDE"] == sigma
        assert foot.headers["DSIGMA"] == 1 if not dense else 0.5
        assert export_file.exists()

    def test_make_footprint_table_crashes_without_slicing(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx
        re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
        orbit_scheme = setup_lhc_orbit(madx, scheme="flat")
        madx.use(sequence="lhcb1")

        with pytest.raises(RuntimeError):
            foot = make_footprint_table(madx, sigma=2)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_get_footprint_lines(self, _dynap_tfs_path, _plottable_footprint_path):
        dynap_tfs = tfs.read(_dynap_tfs_path)  # obtained from make_footprint_table and written to disk
        npzfile = np.load(_plottable_footprint_path)
        ref_qxs, ref_qys = npzfile["qx"], npzfile["qy"]
        npzfile.close()

        qxs, qys = get_footprint_lines(dynap_tfs)
        assert np.allclose(qxs, ref_qxs)
        assert np.allclose(qys, ref_qys)

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_get_footprint_patches(self, _dynap_tfs_path):
        dynap_dframe = tfs.read(_dynap_tfs_path)
        dynap_dframe.headers["AMPLITUDE"] = 6

        plt.rcParams.update({"patch.linewidth": 1.5})
        figure, axis = plt.subplots(figsize=(18, 11))
        polygons = get_footprint_patches(dynap_dframe)
        assert isinstance(polygons, matplotlib.collections.PatchCollection)

        axis.add_collection(polygons)
        axis.set_xlim(0.3095, 0.311)
        axis.set_ylim(0.31925, 0.3208)
        return figure

    def test_get_footprint_patches_raises_wrong_shape(self, _dynap_tfs_path, caplog):
        dynap_dframe = tfs.read(_dynap_tfs_path)

        with pytest.raises(ValueError):
            polygons = get_footprint_patches(dynap_dframe)

        for record in caplog.records:
            assert record.levelname == "ERROR"


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


class TestTwiss:
    def test_twiss_tfs(self, _twiss_export, _matched_base_lattice):
        madx = _matched_base_lattice
        twiss_tfs = get_twiss_tfs(madx).drop(columns=["COMMENTS"])
        from_disk = tfs.read(_twiss_export, index="NAME").drop(columns=["COMMENTS"])
        assert_frame_equal(twiss_tfs, from_disk)

    def test_get_ips_twiss(self, _ips_twiss_path, _matched_lhc_madx):
        madx = _matched_lhc_madx

        reference_df = tfs.read(_ips_twiss_path)
        ips_df = get_ips_twiss(madx)
        assert_dict_equal(reference_df.headers, ips_df.headers)
        assert_frame_equal(reference_df.set_index("name"), ips_df.set_index("name"))

    @pytest.mark.parametrize("ir", [1, 5])
    def test_get_irs_twiss(self, ir, _matched_lhc_madx):
        madx = _matched_lhc_madx

        reference_df = tfs.read(INPUTS_DIR / f"ir{ir:d}_twiss.tfs")
        ir_df = get_ir_twiss(madx, ir=ir)
        assert_dict_equal(reference_df.headers, ir_df.headers)
        assert_frame_equal(reference_df.set_index("name"), ir_df.set_index("name"))

        extra_columns = ["k0l", "k0sl", "k1l", "k1sl", "k2l", "k2sl", "sig11", "sig12", "sig21", "sig22"]
        ir_extra_columns_df = get_ir_twiss(madx, ir=ir, columns=DEFAULT_TWISS_COLUMNS + extra_columns)
        assert all([colname in ir_extra_columns_df.columns for colname in extra_columns])


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
def _bare_lhc_madx() -> Madx:
    """Only loading sequence and optics."""
    madx = Madx(stdout=False)
    madx.call(str(LHC_SEQUENCE.absolute()))
    madx.call(str(LHC_OPTICS.absolute()))
    yield madx
    madx.exit()


@pytest.fixture()
def _non_matched_lhc_madx() -> Madx:
    """Important properties & beam for lhcb1 declared and in use, NO MATCHING done here."""
    madx = Madx(stdout=False)
    madx.call(str(LHC_SEQUENCE.absolute()))
    madx.call(str(LHC_OPTICS.absolute()))

    NRJ = madx.globals["NRJ"] = 6500
    madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
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
    madx.use(sequence="lhcb1")
    yield madx
    madx.exit()


@pytest.fixture()
def _matched_lhc_madx() -> Madx:
    """Important properties & beam for lhcb1 declared and in use, WITH matching to working point."""
    madx = Madx(stdout=False)
    madx.call(str(LHC_SEQUENCE.absolute()))
    madx.call(str(LHC_OPTICS.absolute()))

    NRJ = madx.globals["NRJ"] = 6500
    madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
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
    madx.use(sequence="lhcb1")
    match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=True)
    yield madx
    madx.exit()


@pytest.fixture()
def _matched_base_lattice() -> Madx:
    """Base CAS lattice matched to default working point."""
    madx = Madx(stdout=False)
    madx.input(BASE_LATTICE)
    match_tunes_and_chromaticities(
        madx=madx,
        sequence="CAS3",
        q1_target=6.335,
        q2_target=6.29,
        dq1_target=100,
        dq2_target=100,
        varied_knobs=["kqf", "kqd", "ksf", "ksd"],
    )
    yield madx
    madx.exit()


@pytest.fixture()
def _ampdet_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "ampdet.tfs"


@pytest.fixture()
def _rdts_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "rdts.tfs"


@pytest.fixture()
def _ptc_twiss_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "ptc_twiss.tfs"


@pytest.fixture()
def _ips_twiss_path() -> pathlib.Path:
    return INPUTS_DIR / "ips_twiss.tfs"


@pytest.fixture()
def _twiss_export() -> pathlib.Path:
    return INPUTS_DIR / "twiss_export.tfs"


@pytest.fixture()
def _dynap_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "dynap.tfs"


@pytest.fixture()
def _plottable_footprint_path() -> pathlib.Path:
    return INPUTS_DIR / "plottable_footprint.npz"
