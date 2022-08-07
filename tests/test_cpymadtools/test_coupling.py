import math
import pathlib

import numpy as np
import pytest
import tfs

from optics_functions.constants import F1001, F1010
from optics_functions.coupling import split_complex_columns
from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.coupling import (
    get_closest_tune_approach,
    get_cminus_from_coupling_rdts,
    get_coupling_rdts,
    match_no_coupling_through_ripkens,
)
from pyhdtoolkit.cpymadtools.lhc import apply_lhc_coupling_knob, get_lhc_tune_and_chroma_knobs
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"


class TestCoupling:
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

    @pytest.mark.parametrize("filtering", [0, 3.5])
    def test_complex_cminus_from_coupling_rdts(self, _non_matched_lhc_madx, filtering):
        """Using LHC lattice."""
        madx = _non_matched_lhc_madx
        apply_lhc_coupling_knob(madx, 2e-3, telescopic_squeeze=True)
        # match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=True)

        complex_cminus = get_cminus_from_coupling_rdts(madx, method="teapot", filtering=filtering)
        assert np.isclose(np.abs(complex_cminus), 2e-3, rtol=1e-1)  # let's say 10% here too

    @pytest.mark.parametrize("variable", ["kqsx3.l1", "kqsx3.r1"])
    @pytest.mark.parametrize("powering", [2e-4, 5e-4, 1e-3])
    def test_match_no_coupling_through_ripken(self, _non_matched_lhc_madx, variable, powering):
        madx = _non_matched_lhc_madx
        madx.globals[variable] = powering  # power MQSX, this will create coupling at IP1
        match_no_coupling_through_ripkens(madx, "lhcb1", location="IP1", vary_knobs=[variable])
        twiss_df = madx.twiss(chrom=True, ripken=True).dframe().copy()
        twiss_df.name = twiss_df.name.apply(lambda x: x[:-2])
        assert math.isclose(twiss_df[twiss_df.name == "ip1"].beta21[0], 0, abs_tol=1e-10)
        assert math.isclose(twiss_df[twiss_df.name == "ip1"].beta21[0], 0, abs_tol=1e-10)

    def test_get_coupling_rdts(self, _non_matched_lhc_madx, _coupling_bump_script, _correct_bump_rdts_path):
        madx = _non_matched_lhc_madx
        madx.call(str(_coupling_bump_script.absolute()))
        res = get_coupling_rdts(madx)[[F1001, F1010]]
        assert F1001 in res.columns
        assert F1010 in res.columns
        res = split_complex_columns(res, columns=[F1001, F1010], drop=True)
        reference = tfs.read(_correct_bump_rdts_path)
        assert_frame_equal(res, reference)


# ---------------------- Private Utilities ---------------------- #


@pytest.fixture()
def _coupling_bump_script() -> pathlib.Path:
    return INPUTS_DIR / "madx" / "lhc_coupling_bump.madx"


@pytest.fixture()
def _correct_bump_rdts_path() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "lhc_coupling_bump.tfs"
