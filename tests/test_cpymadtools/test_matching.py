import math
import sys

import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.lhc import apply_lhc_coupling_knob, get_lhc_tune_and_chroma_knobs
from pyhdtoolkit.cpymadtools.matching import (
    get_closest_tune_approach,
    match_chromaticities,
    match_tunes,
    match_tunes_and_chromaticities,
)

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Windows is very flaky on this.")
class TestMatching:
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

    @pytest.mark.parametrize("q1_target, q2_target", [(6.335, 6.29), (6.34, 6.27), (6.38, 6.27)])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_tune_matching_wrapper(self, q1_target, q2_target, telescopic_squeeze):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.q1[0] != q1_target
        assert madx.table.summ.q2[0] != q2_target

        match_tunes(
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

    @pytest.mark.parametrize("dq1_target, dq2_target", [(100, 100), (95, 95), (105, 105)])
    @pytest.mark.parametrize("telescopic_squeeze", [False, True])
    def test_chroma_matching_wrapper(self, dq1_target, dq2_target, telescopic_squeeze):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.dq1[0] != dq1_target
        assert madx.table.summ.dq2[0] != dq2_target

        match_chromaticities(
            madx=madx,
            sequence="CAS3",
            dq1_target=dq1_target,
            dq2_target=dq2_target,
            varied_knobs=["ksf", "ksd"],
            telescopic_squeeze=telescopic_squeeze,
        )
        assert math.isclose(madx.table.summ.dq1[0], dq1_target, rel_tol=1e-3)
        assert math.isclose(madx.table.summ.dq2[0], dq2_target, rel_tol=1e-3)

    # TODO: remove these below once they are removed from cpymadtools.lhc for being deprecated
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
