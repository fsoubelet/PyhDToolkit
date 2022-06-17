import pathlib

import pytest
import tfs

from pyhdtoolkit.plotting.sbs.coupling import plot_full_ip_rdt, plot_rdt_component

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
SBS_INPUTS = INPUTS_DIR / "sbs"


class TestCouplingSbsPlotting:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_rdt_component(self, sbs_coupling_b1_ip1, sbs_coupling_b2_ip1, sbs_model_b1, sbs_model_b2):
        figure = plot_rdt_component(
            b1_segment_df=sbs_coupling_b1_ip1,
            b2_segment_df=sbs_coupling_b2_ip1,
            b1_model=sbs_model_b1,
            b2_model=sbs_model_b2,
            ip=1,
        )
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_full_ip(self, sbs_coupling_b1_ip1, sbs_coupling_b2_ip1, sbs_model_b1, sbs_model_b2):
        figure = plot_full_ip_rdt(
            b1_segment_df=sbs_coupling_b1_ip1,
            b2_segment_df=sbs_coupling_b2_ip1,
            b1_model=sbs_model_b1,
            b2_model=sbs_model_b2,
            ip=1,
            rdt="f1001",
            figsize=(18, 9),
            # abs_ylimits=(8e-2, 14e-2),
            # real_ylimits=(-1e-1, 1e-1),
            # imag_ylimits=(-1e-1, 1e-1),
        )
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
