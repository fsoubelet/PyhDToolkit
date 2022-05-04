import pathlib

import pytest
import tfs

from pandas._testing import assert_dict_equal
from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.constants import DEFAULT_TWISS_COLUMNS  # for coverage
from pyhdtoolkit.cpymadtools.twiss import get_ips_twiss, get_ir_twiss, get_twiss_tfs

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"


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
        # assert_dict_equal(reference_df.headers, ips_df.headers)  # bugged at the moment
        assert_frame_equal(reference_df.set_index("name"), ips_df.set_index("name"))

    @pytest.mark.parametrize("ir", [1, 5])
    def test_get_irs_twiss(self, ir, _matched_lhc_madx):
        madx = _matched_lhc_madx

        reference_df = tfs.read(INPUTS_DIR / f"ir{ir:d}_twiss.tfs")
        ir_df = get_ir_twiss(madx, ir=ir)
        # assert_dict_equal(reference_df.headers, ir_df.headers)  # bugged at the moment
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
