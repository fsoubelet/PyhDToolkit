import pathlib

import pytest
import tfs
from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.constants import DEFAULT_TWISS_COLUMNS  # noqa: F401  |  for coverage
from pyhdtoolkit.cpymadtools.twiss import get_twiss_tfs

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"


def test_twiss_tfs(_twiss_export, _matched_base_lattice):
    madx = _matched_base_lattice
    twiss_tfs = get_twiss_tfs(madx).drop(columns=["COMMENTS"])
    from_disk = tfs.read(_twiss_export, index="NAME").drop(columns=["COMMENTS"])
    assert_frame_equal(twiss_tfs, from_disk)


# ---------------------- Private Utilities ---------------------- #


@pytest.fixture
def _twiss_export() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "twiss_export.tfs"
