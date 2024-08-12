import pathlib

import pytest
import tfs

from pyhdtoolkit.plotting.sbs.phase import (
    plot_phase_segment,
    plot_phase_segment_both_beams,
    plot_phase_segment_one_beam,
)

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
SBS_INPUTS = INPUTS_DIR / "sbs"


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_one_beam(sbs_phasex, sbs_phasey, sbs_model_b2):
    figure = plot_phase_segment_one_beam(
        phase_x=sbs_phasex,
        phase_y=sbs_phasey,
        model=sbs_model_b2,
        ip=5,
    )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_both_beams(sbs_phasex, sbs_phasey, sbs_model_b2):
    # Only plotting beam 2 data on both, just for the test
    figure = plot_phase_segment_both_beams(
        b1_phase_x=sbs_phasex,
        b1_phase_y=sbs_phasey,
        b2_phase_x=sbs_phasex,
        b2_phase_y=sbs_phasey,
        b1_model=sbs_model_b2,
        b2_model=sbs_model_b2,
        ip=5,
        figsize=(12, 6),
        bbox_to_anchor=(0.535, 0.94),
    )
    return figure


@pytest.mark.parametrize("wrongplane", ["not", "accepted", "incorrect", ""])
def test_plot_phase_segment_raises_on_wrong_plane(wrongplane, sbs_phasex, sbs_model_b2):
    with pytest.raises(ValueError):
        plot_phase_segment(segment_df=sbs_phasex, model_df=sbs_model_b2, plane=wrongplane)


# ----- Fixtures ----- #


@pytest.fixture
def sbs_phasex() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2sbsphasext_IP5.out")


@pytest.fixture
def sbs_phasey() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2sbsphaseyt_IP5.out")


@pytest.fixture
def sbs_model_b2() -> tfs.TfsDataFrame:
    return tfs.read(SBS_INPUTS / "b2_twiss_elements.dat")
