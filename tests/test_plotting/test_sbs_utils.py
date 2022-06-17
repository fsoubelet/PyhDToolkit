import math
import pathlib

import pytest
import tfs

from pyhdtoolkit.plotting.sbs.utils import (
    determine_default_coupling_ylabel,
    determine_default_phase_ylabel,
    find_ip_s_from_segment_start,
)

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
SBS_INPUTS = INPUTS_DIR / "sbs"


class TestSbsPlottingUtils:
    def test_find_ip_s(self, sbs_coupling_b1_ip1, sbs_model_b1):
        assert math.isclose(
            find_ip_s_from_segment_start(segment_df=sbs_coupling_b1_ip1, model_df=sbs_model_b1, ip=1),
            493.25226,
            rel_tol=1e-5,
        )

    @pytest.mark.parametrize("f1001", ["F1001", "f1001"])
    @pytest.mark.parametrize("f1010", ["F1010", "f1010"])
    @pytest.mark.parametrize("abs_", ["abs", "ABS", "aBs"])
    @pytest.mark.parametrize("real", ["RE", "re", "Re", "rE"])
    @pytest.mark.parametrize("imag", ["IM", "im", "Im", "iM"])
    def test_coupling_ylabel(self, f1001, f1010, abs_, real, imag):
        """Parametrization also tests case insensitiveness."""
        assert determine_default_coupling_ylabel(f1001, abs_) == r"$|f_{1001}|$"
        assert determine_default_coupling_ylabel(f1001, real) == r"$\Re f_{1001}$"
        assert determine_default_coupling_ylabel(f1001, imag) == r"$\Im f_{1001}$"

        assert determine_default_coupling_ylabel(f1010, abs_) == r"$|f_{1010}|$"
        assert determine_default_coupling_ylabel(f1010, real) == r"$\Re f_{1010}$"
        assert determine_default_coupling_ylabel(f1010, imag) == r"$\Im f_{1010}$"

    @pytest.mark.parametrize("rdt", ["invalid", "F1111", "nope"])
    def test_coupling_ylabel_raises_on_invalid_rdt(self, rdt):
        with pytest.raises(AssertionError):
            determine_default_coupling_ylabel(rdt, "abs")

    @pytest.mark.parametrize("plane", ["x", "X", "y", "Y"])
    def test_phase_ylabel(self, plane):
        """Parametrization also tests case insensitiveness."""
        if plane.upper() == "X":
            assert determine_default_phase_ylabel(plane) == r"$\Delta \phi_{x}$"
        else:
            assert determine_default_phase_ylabel(plane) == r"$\Delta \phi_{y}$"

    @pytest.mark.parametrize("plane", ["a", "Fb1", "nope", "not a plane"])
    def test_phase_ylabel_raises_on_invalid_rdt(self, plane):
        with pytest.raises(AssertionError):
            determine_default_phase_ylabel(plane)


# ----- Fixtures ----- #


@pytest.fixture()
def sbs_model_b1() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b1_twiss_elements.dat")


@pytest.fixture()
def sbs_model_b2() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2_twiss_elements.dat")


@pytest.fixture()
def sbs_coupling_b1_ip1() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b1_sbscouple_IP1.out")


@pytest.fixture()
def sbs_coupling_b2_ip1() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2_sbscouple_IP1.out")
