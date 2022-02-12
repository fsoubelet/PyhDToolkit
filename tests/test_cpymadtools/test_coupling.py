import math

import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.coupling import get_closest_tune_approach
from pyhdtoolkit.cpymadtools.lhc import apply_lhc_coupling_knob, get_lhc_tune_and_chroma_knobs
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities


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
