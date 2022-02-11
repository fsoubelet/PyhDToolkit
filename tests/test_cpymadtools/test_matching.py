import math

import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.lhc import apply_lhc_coupling_knob
from pyhdtoolkit.cpymadtools.matching import (
    get_lhc_tune_and_chroma_knobs,
    match_tunes_and_chromaticities,
)

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


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
