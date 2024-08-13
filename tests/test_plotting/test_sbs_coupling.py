import pathlib

import pytest
import tfs

from pyhdtoolkit.plotting.sbs.coupling import plot_full_ip_rdt, plot_rdt_component

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
SBS_INPUTS = INPUTS_DIR / "sbs"


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_rdt_component(sbs_coupling_b1_ip1, sbs_coupling_b2_ip1, sbs_model_b1, sbs_model_b2):
    return plot_rdt_component(
        b1_segment_df=sbs_coupling_b1_ip1,
        b2_segment_df=sbs_coupling_b2_ip1,
        b1_model=sbs_model_b1,
        b2_model=sbs_model_b2,
        ip=1,
    )


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_full_ip(sbs_coupling_b1_ip1, sbs_coupling_b2_ip1, sbs_model_b1, sbs_model_b2):
    return plot_full_ip_rdt(
        b1_segment_df=sbs_coupling_b1_ip1,
        b2_segment_df=sbs_coupling_b2_ip1,
        b1_model=sbs_model_b1,
        b2_model=sbs_model_b2,
        ip=1,
        rdt="f1001",
        figsize=(12, 7),
        bbox_to_anchor=(0.535, 0.95),
    )


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_full_ip_with_ylimits(sbs_coupling_b1_ip1, sbs_coupling_b2_ip1, sbs_model_b1, sbs_model_b2):
    return plot_full_ip_rdt(
        b1_segment_df=sbs_coupling_b1_ip1,
        b2_segment_df=sbs_coupling_b2_ip1,
        b1_model=sbs_model_b1,
        b2_model=sbs_model_b2,
        ip=1,
        rdt="f1001",
        figsize=(12, 7),
        abs_ylimits=(2e-2, 15e-2),
        real_ylimits=(-1.3e-1, 5e-2),
        imag_ylimits=(-1.3e-1, 1e-2),
        bbox_to_anchor=(0.535, 0.95),
    )


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
