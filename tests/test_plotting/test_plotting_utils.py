import math
import pathlib

import matplotlib.pyplot as plt
import pytest
import tfs

from pyhdtoolkit.plotting.utils import (
    _determine_default_sbs_coupling_ylabel,
    _determine_default_sbs_phase_ylabel,
    draw_ip_locations,
    find_ip_s_from_segment_start,
    get_lhc_ips_positions,
)

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
SBS_INPUTS = INPUTS_DIR / "sbs"


def test_find_ip_s(sbs_coupling_b1_ip1, sbs_model_b1):
    assert math.isclose(
        find_ip_s_from_segment_start(segment_df=sbs_coupling_b1_ip1, model_df=sbs_model_b1, ip=1),
        493.25226,
        rel_tol=1e-5,
    )

    # This one is cut by the end of sequence, tests we properly loop around
    # Value is high because segment in test file is for IP1
    assert math.isclose(
        find_ip_s_from_segment_start(segment_df=sbs_coupling_b1_ip1, model_df=sbs_model_b1, ip=2),
        3825.68884,
        rel_tol=1e-5,
    )


@pytest.mark.parametrize("f1001", ["F1001", "f1001"])
@pytest.mark.parametrize("f1010", ["F1010", "f1010"])
@pytest.mark.parametrize("abs_", ["abs", "ABS", "aBs"])
@pytest.mark.parametrize("real", ["RE", "re", "Re", "rE"])
@pytest.mark.parametrize("imag", ["IM", "im", "Im", "iM"])
def test_coupling_ylabel(f1001, f1010, abs_, real, imag):
    """Parametrization also tests case insensitiveness."""
    assert _determine_default_sbs_coupling_ylabel(f1001, abs_) == r"$|f_{1001}|$"
    assert _determine_default_sbs_coupling_ylabel(f1001, real) == r"$\Re f_{1001}$"
    assert _determine_default_sbs_coupling_ylabel(f1001, imag) == r"$\Im f_{1001}$"

    assert _determine_default_sbs_coupling_ylabel(f1010, abs_) == r"$|f_{1010}|$"
    assert _determine_default_sbs_coupling_ylabel(f1010, real) == r"$\Re f_{1010}$"
    assert _determine_default_sbs_coupling_ylabel(f1010, imag) == r"$\Im f_{1010}$"


@pytest.mark.parametrize("rdt", ["invalid", "F1111", "nope"])
def test_coupling_ylabel_raises_on_invalid_rdt(rdt):
    with pytest.raises(AssertionError):
        _determine_default_sbs_coupling_ylabel(rdt, "abs")


@pytest.mark.parametrize("plane", ["x", "X", "y", "Y"])
def test_phase_ylabel(plane):
    """Parametrization also tests case insensitiveness."""
    if plane.upper() == "X":
        assert _determine_default_sbs_phase_ylabel(plane) == r"$\Delta \phi_{x}$"
    else:
        assert _determine_default_sbs_phase_ylabel(plane) == r"$\Delta \phi_{y}$"


@pytest.mark.parametrize("plane", ["a", "Fb1", "nope", "not a plane"])
def test_phase_ylabel_raises_on_invalid_rdt(plane):
    with pytest.raises(AssertionError):
        _determine_default_sbs_phase_ylabel(plane)


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_ip_locations(_non_matched_lhc_madx):
    # tests both querying the locations and adding them on a plot
    madx = _non_matched_lhc_madx
    twiss_df = madx.twiss().dframe().copy()
    ips_dict = get_lhc_ips_positions(twiss_df)

    figure, ax = plt.subplots(figsize=(10, 6))
    twiss_df.plot(ax=ax, x="s", y=["betx", "bety"])
    draw_ip_locations(ips_dict)
    return figure


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