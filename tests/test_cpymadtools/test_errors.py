import pathlib
import random

import pytest
from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.errors import (
    misalign_lhc_ir_quadrupoles,
    misalign_lhc_triplets,
    switch_magnetic_errors,
)
from pyhdtoolkit.cpymadtools.generators import LatticeGenerator

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
LHC_SEQUENCE = INPUTS_DIR / "lhc_as-built.seq"
LHC_OPTICS = INPUTS_DIR / "opticsfile.22"


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

