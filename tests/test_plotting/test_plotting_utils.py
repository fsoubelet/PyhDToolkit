import math
import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pytest
import tfs

from pyhdtoolkit.plotting.utils import (
    _determine_default_sbs_coupling_ylabel,
    _determine_default_sbs_phase_ylabel,
    draw_confidence_ellipse,
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
    twiss_df = madx.twiss().dframe()
    ips_dict = get_lhc_ips_positions(twiss_df)

    figure, ax = plt.subplots(figsize=(10, 6))
    twiss_df.plot(ax=ax, x="s", y=["betx", "bety"])
    draw_ip_locations(ips_dict)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_ip_locations_with_xlimits(_non_matched_lhc_madx):
    # tests both querying the locations and adding them on a plot
    madx = _non_matched_lhc_madx
    twiss_df = madx.twiss().dframe()
    ips_dict = get_lhc_ips_positions(twiss_df)

    figure, ax = plt.subplots(figsize=(10, 6))
    twiss_df.plot(ax=ax, x="s", y=["betx", "bety"])
    ax.set_xlim(8500, 18000)
    draw_ip_locations(ips_dict)  # should only draw IPs in the range
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_confidence_ellipse_subplots():
    """Confidence ellipse on three correlated datasets in subplots."""
    np.random.seed(0)
    PARAMETERS = {
        "Positive correlation": [[0.85, 0.35], [0.15, -0.65]],
        "Negative correlation": [[0.9, -0.4], [0.1, -0.6]],
        "Weak correlation": [[1, 0], [0, 1]],
    }
    mu = 2, 4
    scale = 3, 5

    figure, axs = plt.subplots(1, 3, figsize=(9, 3))
    for ax, (title, dependency) in zip(axs, PARAMETERS.items(), strict=False):
        x, y = get_correlated_dataset(800, dependency, mu, scale)
        ax.scatter(x, y, s=0.5)
        ax.axvline(c="grey", lw=1)
        ax.axhline(c="grey", lw=1)
        draw_confidence_ellipse(x, y, ax=ax, n_std=2.5, edgecolor="red")
        ax.scatter(mu[0], mu[1], c="red", s=3)
        ax.set_title(title)
        ax.set_xlim(-8, 12)
        ax.set_ylim(-15, 20)

    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_confidence_ellipse_several_stds():
    np.random.seed(0)
    figure, ax_nstd = plt.subplots(figsize=(6, 6))
    dependency_nstd = [[0.8, 0.75], [-0.2, 0.35]]
    mu = 0, 0
    scale = 8, 5

    ax_nstd.axvline(c="grey", lw=1)
    ax_nstd.axhline(c="grey", lw=1)
    x, y = get_correlated_dataset(500, dependency_nstd, mu, scale)
    ax_nstd.scatter(x, y, s=0.5)
    draw_confidence_ellipse(x, y, ax=ax_nstd, n_std=1, label=r"$1\sigma$", edgecolor="firebrick")
    draw_confidence_ellipse(x, y, ax=ax_nstd, n_std=2, label=r"$2\sigma$", edgecolor="fuchsia", linestyle="--")
    draw_confidence_ellipse(x, y, ax=ax_nstd, n_std=3, label=r"$3\sigma$", edgecolor="blue", linestyle=":")
    ax_nstd.scatter(mu[0], mu[1], c="red", s=3)
    ax_nstd.set_title("Different standard deviations")
    ax_nstd.legend()
    return figure


# ----- Helpers ----- #


def get_correlated_dataset(n, dependency, mu, scale):
    """This one is from the matplotlib doc."""
    latent = np.random.randn(n, 2)
    dependent = latent.dot(dependency)
    scaled = dependent * scale
    scaled_with_offset = scaled + mu
    # return x and y of the new, correlated dataset
    return scaled_with_offset[:, 0], scaled_with_offset[:, 1]


# ----- Fixtures ----- #


@pytest.fixture
def sbs_model_b1() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b1_twiss_elements.dat")


@pytest.fixture
def sbs_model_b2() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2_twiss_elements.dat")


@pytest.fixture
def sbs_coupling_b1_ip1() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b1_sbscouple_IP1.out")


@pytest.fixture
def sbs_coupling_b2_ip1() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2_sbscouple_IP1.out")
