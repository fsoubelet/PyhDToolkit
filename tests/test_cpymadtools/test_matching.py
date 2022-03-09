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

    def test_tune_and_chroma_matching_fails_on_unknown_accelerator(self):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)

        with pytest.raises(NotImplementedError):
            match_tunes_and_chromaticities(
                madx, "some_machine", "some_sequence1", q1_target=6.335, q2_target=6.29, dq1_target=100, dq2_target=100
            )

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
