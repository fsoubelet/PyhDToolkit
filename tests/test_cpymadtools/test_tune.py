import pathlib

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
import tfs

from pyhdtoolkit.cpymadtools.lhc import make_lhc_thin, re_cycle_sequence
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.orbit import setup_lhc_orbit
from pyhdtoolkit.cpymadtools.tune import get_footprint_lines, get_footprint_patches, make_footprint_table

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"


@pytest.mark.parametrize("sigma", [2, 5])
@pytest.mark.parametrize("dense", [True, False])
def test_make_footprint_table(_non_matched_lhc_madx, tmp_path, sigma, dense):
    export_file = tmp_path / "out.tfs"
    madx = _non_matched_lhc_madx
    re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
    orbit_scheme = setup_lhc_orbit(madx, scheme="flat")
    madx.use(sequence="lhcb1")
    match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=True)

    make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
    madx.use(sequence="lhcb1")

    expected_headers = [
        "NAME",
        "TYPE",
        "TITLE",
        "MADX_VERSION",
        "ORIGIN",
        "ANGLE",
        "AMPLITUDE",
        "DSIGMA",
        "ANGLE_MEANING",
        "AMPLITUDE_MEANING",
        "DSIGMA_MEANING",
    ]
    foot = make_footprint_table(madx, sigma=sigma, file=str(export_file))
    assert isinstance(foot, tfs.TfsDataFrame)
    assert all(header in foot.headers for header in expected_headers)
    assert foot.headers["ANGLE"] == 7  # hard-coded in the function
    assert foot.headers["AMPLITUDE"] == sigma
    assert foot.headers["DSIGMA"] == 1 if not dense else 0.5
    assert export_file.exists()


def test_make_footprint_table_crashes_without_slicing(_non_matched_lhc_madx, caplog):
    madx = _non_matched_lhc_madx
    re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
    orbit_scheme = setup_lhc_orbit(madx, scheme="flat")
    madx.use(sequence="lhcb1")

    with pytest.raises(RuntimeError):
        foot = make_footprint_table(madx, sigma=2)

    for record in caplog.records:
        assert record.levelname == "ERROR"


def test_get_footprint_lines(_dynap_tfs_path, _plottable_footprint_path):
    dynap_tfs = tfs.read(_dynap_tfs_path)  # obtained from make_footprint_table and written to disk
    npzfile = np.load(_plottable_footprint_path)
    ref_qxs, ref_qys = npzfile["qx"], npzfile["qy"]
    npzfile.close()

    qxs, qys = get_footprint_lines(dynap_tfs)
    assert np.allclose(qxs, ref_qxs)
    assert np.allclose(qys, ref_qys)


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_get_footprint_patches(_dynap_tfs_path):
    dynap_dframe = tfs.read(_dynap_tfs_path)
    dynap_dframe.headers["AMPLITUDE"] = 6

    plt.rcParams.update({"patch.linewidth": 1.5})
    figure, axis = plt.subplots(figsize=(18, 11))
    polygons = get_footprint_patches(dynap_dframe)
    assert isinstance(polygons, matplotlib.collections.PatchCollection)

    axis.add_collection(polygons)
    axis.set_xlim(0.3095, 0.311)
    axis.set_ylim(0.31925, 0.3208)
    return figure


def test_get_footprint_patches_raises_wrong_shape(_dynap_tfs_path, caplog):
    dynap_dframe = tfs.read(_dynap_tfs_path)

    with pytest.raises(ValueError):
        polygons = get_footprint_patches(dynap_dframe)

    for record in caplog.records:
        assert record.levelname == "ERROR"


# ----- Fixtures ----- #


@pytest.fixture()
def _plottable_footprint_path() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "plottable_footprint.npz"


@pytest.fixture()
def _dynap_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "dynap.tfs"
