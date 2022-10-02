import math
import pathlib
import pickle
import random

from mimetypes import init

import numpy as np
import pytest
import tfs

from cpymad.madx import Madx
from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.constants import (
    LHC_ANGLE_FLAGS,
    LHC_CROSSING_ANGLE_FLAGS,
    LHC_EXPERIMENT_STATE_FLAGS,
    LHC_IP2_SPECIAL_FLAG,
    LHC_IP_OFFSET_FLAGS,
    LHC_PARALLEL_SEPARATION_FLAGS,
)
from pyhdtoolkit.cpymadtools.lhc import (
    _all_lhc_arcs,
    _get_k_strings,
    add_markers_around_lhc_ip,
    apply_lhc_colinearity_knob,
    apply_lhc_colinearity_knob_delta,
    apply_lhc_coupling_knob,
    apply_lhc_rigidity_waist_shift_knob,
    carry_colinearity_knob_over,
    correct_lhc_global_coupling,
    deactivate_lhc_arc_sextupoles,
    do_kmodulation,
    get_lhc_bpms_list,
    get_lhc_bpms_twiss_and_rdts,
    get_lhc_tune_and_chroma_knobs,
    get_magnets_powering,
    install_ac_dipole_as_kicker,
    install_ac_dipole_as_matrix,
    make_lhc_beams,
    make_lhc_thin,
    make_sixtrack_output,
    power_landau_octupoles,
    re_cycle_sequence,
    reset_lhc_bump_flags,
    vary_independent_ir_quadrupoles,
)
from pyhdtoolkit.cpymadtools.track import track_single_particle

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"


def test_all_lhc_arcs():
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
def test_k_strings(orient, result):
    assert _get_k_strings(stop=5, orientation=orient) == result


def test_k_strings_fails_on_wront_orient(caplog):
    with pytest.raises(ValueError):
        _ = _get_k_strings(orientation="qqq")

    for record in caplog.records:
        assert record.levelname == "ERROR"


@pytest.mark.parametrize("current", [100, 200, 300, 400, 500])
def test_landau_powering(current, _non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    brho = madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
    strength = current / madx.globals.Imax_MO * madx.globals.Kmax_MO / brho
    power_landau_octupoles(madx, mo_current=current, beam=1)

    for arc in _all_lhc_arcs(beam=1):
        for fd in "FD":
            assert madx.globals[f"KO{fd}.{arc}"] == strength

    power_landau_octupoles(madx, mo_current=current, beam=1, defective_arc=True)
    assert madx.globals["KOD.A56B1"] == strength * 4.65 / 6


def test_landau_powering_fails_on_missing_nrj(caplog):
    madx = Madx(stdout=False)

    with pytest.raises(EnvironmentError):
        power_landau_octupoles(madx, 100, 1)

    for record in caplog.records:
        assert record.levelname == "ERROR"


def test_depower_arc_sextupoles(_non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    deactivate_lhc_arc_sextupoles(madx, beam=1)

    for arc in _all_lhc_arcs(beam=1):
        for fd in "FD":
            for i in (1, 2):
                assert madx.globals[f"KS{fd}{i:d}.{arc}"] == 0.0


def test_prepare_sixtrack_output(_non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    make_sixtrack_output(madx, energy=6500)

    assert madx.globals["VRF400"] == 16
    assert madx.globals["LAGRF400.B1"] == 0.5
    assert madx.globals["LAGRF400.B2"] == 0.0


def test_get_lhc_bpms_list(_non_matched_lhc_madx, _correct_bpms_list):
    madx = _non_matched_lhc_madx
    bpms = get_lhc_bpms_list(madx)
    with _correct_bpms_list.open("rb") as f:
        correct_list = pickle.load(f)
    assert bpms == correct_list


@pytest.mark.parametrize("knob_value", [-5, 10])
@pytest.mark.parametrize("IR", [1, 2, 5, 8])
def test_colinearity_knob(knob_value, IR, _non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    apply_lhc_colinearity_knob(madx, colinearity_knob_value=knob_value, ir=IR)

    assert madx.globals[f"KQSX3.R{IR:d}"] == knob_value * 1e-4
    assert madx.globals[f"KQSX3.L{IR:d}"] == -1 * knob_value * 1e-4


@pytest.mark.parametrize("knob_delta", [-3, 5])
@pytest.mark.parametrize("IR", [1, 2, 5, 8])
def test_colinearity_knob_delta(knob_delta, IR, _non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    # Assign a value first to make it trickier
    init = 1.5e-4
    madx.globals[f"KQSX3.R{IR:d}"] = init
    madx.globals[f"KQSX3.L{IR:d}"] = -1 * init

    # We started from 0 so it should be this value
    apply_lhc_colinearity_knob_delta(madx, colinearity_knob_delta=knob_delta, ir=IR)
    assert madx.globals[f"KQSX3.R{IR:d}"] == init + knob_delta * 1e-4
    assert madx.globals[f"KQSX3.L{IR:d}"] == -1 * init - knob_delta * 1e-4

    # Now change the knob value and check that the delta is applied
    apply_lhc_colinearity_knob_delta(madx, colinearity_knob_delta=knob_delta, ir=IR)
    assert madx.globals[f"KQSX3.R{IR:d}"] == init + 2 * knob_delta * 1e-4
    assert madx.globals[f"KQSX3.L{IR:d}"] == -1 * init - 2 * knob_delta * 1e-4


def test_rigidity_knob_fails_on_invalid_side(caplog, _non_matched_lhc_madx):
    madx = _non_matched_lhc_madx

    with pytest.raises(ValueError):
        apply_lhc_rigidity_waist_shift_knob(madx, 1, 1, "invalid")

    for record in caplog.records:
        assert record.levelname == "ERROR"


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("knob_value", [1, 2])
@pytest.mark.parametrize("IR", [1, 2, 5, 8])
def test_rigidity_knob(side, knob_value, IR, _non_matched_lhc_madx):
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
def test_coupling_knob(knob_value, _non_matched_lhc_madx, telescopic_squeeze):
    madx = _non_matched_lhc_madx
    apply_lhc_coupling_knob(madx, coupling_knob=knob_value, beam=1, telescopic_squeeze=telescopic_squeeze)
    knob_suffix = "_sq" if telescopic_squeeze else ""
    assert madx.globals[f"CMRS.b1{knob_suffix}"] == knob_value


@pytest.mark.parametrize("energy", [450, 6500, 7000])
def test_make_lhc_beams(energy, _bare_lhc_madx):
    madx = _bare_lhc_madx
    make_lhc_beams(madx, energy=energy)

    madx.use(sequence="lhcb1")
    assert madx.sequence.lhcb1.beam
    assert madx.sequence.lhcb1.beam.energy == energy

    madx.use(sequence="lhcb2")
    assert madx.sequence.lhcb2.beam
    assert madx.sequence.lhcb2.beam.energy == energy


@pytest.mark.parametrize("top_turns", [1000, 6000, 10_000])
def test_install_ac_dipole_as_kicker(top_turns, _matched_lhc_madx):
    madx = _matched_lhc_madx
    make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
    install_ac_dipole_as_kicker(madx, deltaqx=-0.01, deltaqy=0.012, sigma_x=1, sigma_y=1, top_turns=top_turns)
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


def test_install_ac_dipole_matrix(_matched_lhc_madx):
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


def test_makethin_lhc(_matched_lhc_madx):
    """
    Little trick: if we haven't sliced properly, tracking will fail so we can check all is ok by
    attempting a tracking and seeing that it succeeds.
    """
    madx = _matched_lhc_madx
    make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)

    tracks_dict = track_single_particle(madx, initial_coordinates=(1e-4, 0, 1e-4, 0, 0, 0), nturns=10, sequence="lhcb1")
    assert isinstance(tracks_dict, dict)
    tracks = tracks_dict["observation_point_1"]
    assert len(tracks) == 11  # nturns + 1 because $start coordinates also given by MAD-X
    assert all([coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")])


@pytest.mark.parametrize("markers", [100, 1000])
@pytest.mark.parametrize("ip", [1, 2, 5, 8])
def test_add_ip_markers(_non_matched_lhc_madx, markers, ip):
    madx = _non_matched_lhc_madx
    re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
    madx.use(sequence="lhcb1")
    init_twiss = madx.twiss().dframe().copy()
    ip_s = init_twiss.s[f"ip{ip:d}"]
    init_twiss = init_twiss[init_twiss.s.between(ip_s - 15, ip_s + 15)]

    make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
    add_markers_around_lhc_ip(madx, sequence=f"lhcb1", ip=ip, n_markers=markers, interval=0.001)
    new_twiss = madx.twiss().dframe().copy()
    new_twiss = new_twiss[new_twiss.s.between(ip_s - 15, ip_s + 15)]

    assert len(init_twiss) < len(new_twiss)


@pytest.mark.parametrize("start_point", ["IP3", "MSIA.EXIT.B1"])
def test_re_cycling(_bare_lhc_madx, start_point):
    madx = _bare_lhc_madx
    re_cycle_sequence(madx, sequence="lhcb1", start=start_point)
    make_lhc_beams(madx)
    madx.command.use(sequence="lhcb1")
    madx.twiss()
    twiss = madx.table.twiss.dframe().copy()
    assert start_point.lower() in twiss.name[0].lower()


def test_resetting_lhc_bump_flags(_bare_lhc_madx):
    madx = _bare_lhc_madx
    make_lhc_beams(madx)
    ALL_BUMPS = (
        LHC_ANGLE_FLAGS
        + LHC_CROSSING_ANGLE_FLAGS
        + LHC_EXPERIMENT_STATE_FLAGS
        + LHC_IP2_SPECIAL_FLAG
        + LHC_IP_OFFSET_FLAGS
        + LHC_PARALLEL_SEPARATION_FLAGS
    )
    with madx.batch():
        madx.globals.update({bump: random.random() for bump in ALL_BUMPS})
    assert all([madx.globals[bump] != 0 for bump in ALL_BUMPS])

    reset_lhc_bump_flags(madx)
    assert all([madx.globals[bump] == 0 for bump in ALL_BUMPS])


def test_vary_independent_ir_quads(_non_matched_lhc_madx):
    # still need to find how to test MAD-X has done this, but don't think we can test just a VARY
    madx = _non_matched_lhc_madx
    vary_independent_ir_quadrupoles(madx, quad_numbers=[4, 5, 6, 7, 8, 9, 10, 11, 12, 13], ip=1, sides=("r", "l"))


def test_vary_independent_ir_quads_raises_on_wrong_side(_non_matched_lhc_madx, caplog):
    madx = _non_matched_lhc_madx
    with pytest.raises(ValueError):
        vary_independent_ir_quadrupoles(madx, quad_numbers=[4], ip=1, sides="Z")

    for record in caplog.records:
        assert record.levelname == "ERROR"


def test_vary_independent_ir_quads_raises_on_wrong_ip(_non_matched_lhc_madx, caplog):
    madx = _non_matched_lhc_madx
    with pytest.raises(ValueError):
        vary_independent_ir_quadrupoles(madx, quad_numbers=[4], ip=100, sides="R")

    for record in caplog.records:
        assert record.levelname == "ERROR"


def test_vary_independent_ir_quads_raises_on_wrong_quads(_non_matched_lhc_madx, caplog):
    madx = _non_matched_lhc_madx
    with pytest.raises(ValueError):
        vary_independent_ir_quadrupoles(madx, quad_numbers=[5, 20, 100], ip=1, sides="R")

    for record in caplog.records:
        assert record.levelname == "ERROR"


@pytest.mark.parametrize("beam", [1, 2, 3, 4])
@pytest.mark.parametrize("telescopic_squeeze", [False, True])
@pytest.mark.parametrize("run3", [False, True])
def test_lhc_tune_and_chroma_knobs(beam, telescopic_squeeze, run3):
    expected_beam = 2 if beam == 4 else beam
    if run3:
        expected_suffix = "_op"
    elif telescopic_squeeze:
        expected_suffix = "_sq"
    else:
        expected_suffix = ""
    assert get_lhc_tune_and_chroma_knobs("LHC", beam, telescopic_squeeze, run3) == (
        f"dQx.b{expected_beam}{expected_suffix}",
        f"dQy.b{expected_beam}{expected_suffix}",
        f"dQpx.b{expected_beam}{expected_suffix}",
        f"dQpy.b{expected_beam}{expected_suffix}",
    )


@pytest.mark.parametrize("beam", [1, 2, 3, 4])
@pytest.mark.parametrize("telescopic_squeeze", [False, True])
def test_hllhc_tune_and_chroma_knobs(beam, telescopic_squeeze):
    expected_beam = 2 if beam == 4 else beam
    expected_suffix = "_sq" if telescopic_squeeze else ""
    assert get_lhc_tune_and_chroma_knobs("HLLHC", beam, telescopic_squeeze) == (
        f"kqtf.b{expected_beam}{expected_suffix}",
        f"kqtd.b{expected_beam}{expected_suffix}",
        f"ksf.b{expected_beam}{expected_suffix}",
        f"ksd.b{expected_beam}{expected_suffix}",
    )


def test_get_knobs_fails_on_unknown_accelerator(caplog):
    with pytest.raises(NotImplementedError):
        _ = get_lhc_tune_and_chroma_knobs("not_an_accelerator")

    for record in caplog.records:
        assert record.levelname == "ERROR"


def test_get_magnets_powering(_matched_lhc_madx, _magnets_fields_path):
    madx = _matched_lhc_madx

    # Specific pattern and extra column, and brho for coverage
    magnets_df = get_magnets_powering(
        madx, patterns=["mqxa.1[rl]1"], brho=madx.globals["NRJ"] * 1e9 / madx.globals.clight, columns=["s"]
    )
    reference_df = tfs.read(_magnets_fields_path)
    # Somehow they're equal but with different columns order, let's reindex to avoid that
    assert_frame_equal(
        reference_df.reindex(sorted(reference_df.columns), axis=1).set_index("name"),
        magnets_df.reindex(sorted(magnets_df.columns), axis=1).set_index("name"),
    )


def test_get_bpms_coupling_rdts(_non_matched_lhc_madx, _reference_twiss_rdts):
    madx = _non_matched_lhc_madx
    madx.globals["CMRS.b1_sq"] = 0.001

    twiss_with_rdts = get_lhc_bpms_twiss_and_rdts(madx)
    # We separate the complex components to compare to the reference
    twiss_with_rdts["F1001R"] = twiss_with_rdts.F1001.apply(np.real)
    twiss_with_rdts["F1001I"] = twiss_with_rdts.F1001.apply(np.imag)
    twiss_with_rdts["F1010R"] = twiss_with_rdts.F1010.apply(np.real)
    twiss_with_rdts["F1010I"] = twiss_with_rdts.F1010.apply(np.imag)
    twiss_with_rdts = twiss_with_rdts.drop(columns=["F1001", "F1010"]).set_index("NAME")

    reference = tfs.read(_reference_twiss_rdts, index="NAME")
    assert_frame_equal(twiss_with_rdts, reference)


def test_k_modulation(_non_matched_lhc_madx, _reference_kmodulation):
    madx = _non_matched_lhc_madx
    results = do_kmodulation(madx)
    assert all(var == 0 for var in results.ERRTUNEX)
    assert all(var == 0 for var in results.ERRTUNEY)

    reference = tfs.read(_reference_kmodulation)
    assert_frame_equal(results.convert_dtypes(), reference.convert_dtypes())  # avoid dtype comparison error on 0 cols


@pytest.mark.parametrize("ir", [1, 2, 5, 8])
def test_carry_colinearity_knob_over(_non_matched_lhc_madx, ir):
    madx = _non_matched_lhc_madx
    madx.globals[f"kqsx3.l{ir:d}"] = 0.001
    madx.globals[f"kqsx3.r{ir:d}"] = 0.001

    # Carry to left
    carry_colinearity_knob_over(madx, ir=ir, to_left=True)
    assert madx.globals[f"kqsx3.l{ir:d}"] == 0.002
    assert madx.globals[f"kqsx3.r{ir:d}"] == 0

    # Reset
    madx.globals[f"kqsx3.l{ir:d}"] = 0.001
    madx.globals[f"kqsx3.r{ir:d}"] = 0.001

    # Carry to right
    carry_colinearity_knob_over(madx, ir=ir, to_left=False)
    assert madx.globals[f"kqsx3.l{ir:d}"] == 0
    assert madx.globals[f"kqsx3.r{ir:d}"] == 0.002


@pytest.mark.parametrize("telesqueeze", [True, False])
def test_correct_lhc_global_coupling(_non_matched_lhc_madx, telesqueeze):
    madx = _non_matched_lhc_madx
    madx.globals["CMRS.b1"] = 0.001
    madx.globals["CMIS.b1"] = 0.001
    madx.command.twiss(chrom=True)
    assert madx.table.summ.dqmin[0] > 0

    correct_lhc_global_coupling(madx, telescopic_squeeze=telesqueeze)
    assert madx.table.summ.dqmin[0] >= 0
    assert math.isclose(madx.table.summ.dqmin[0], 0, abs_tol=1e-7)


# ---------------------- Private Utilities ---------------------- #


@pytest.fixture()
def _magnets_fields_path() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "magnets_fields.tfs"


@pytest.fixture()
def _correct_bpms_list() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "correct_bpms_list.pkl"


@pytest.fixture()
def _reference_twiss_rdts() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "twiss_with_rdts.tfs"


@pytest.fixture()
def _reference_kmodulation() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "kmodulation.tfs"
