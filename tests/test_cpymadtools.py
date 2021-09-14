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
