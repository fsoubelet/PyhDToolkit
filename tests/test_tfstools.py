import pathlib

import matplotlib
import numpy as np
import pytest
import tfs

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.tfstools.latwiss import _assert_necessary_columns, plot_latwiss

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


class TestLaTwiss:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss_from_pandas_frame(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )
        twiss = madx.table.twiss.dframe()

        figure = plot_latwiss(
            twiss_ouptut=twiss,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss_from_tfs_frame(self, tmp_path, _latwiss_tfs_frame):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        figure = plot_latwiss(
            twiss_ouptut=_latwiss_tfs_frame,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss_from_file(self, tmp_path, _latwiss_tfs_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        figure = plot_latwiss(
            twiss_ouptut=_latwiss_tfs_path,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    def test_plot_latwiss_crash_on_wrong_datatype(self, caplog):
        wrong_data = np.array([1, 2, 3, 4, 5])

        with pytest.raises(ValueError):
            _ = plot_latwiss(twiss_ouptut=wrong_data, title="Project 3 Base Lattice",)

        for record in caplog.records:
            assert record.levelname == "ERROR"


def test_assert_columns_fails_on_absent_column(caplog):
    madx = Madx(stdout=False)
    madx.input(BASE_LATTICE)
    match_tunes_and_chromaticities(
        madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
    )
    twiss = madx.table.twiss.dframe()

    with pytest.raises(KeyError):
        _assert_necessary_columns(twiss, columns=["some_obviously_absent_colname"])

    for record in caplog.records:
        assert record.levelname == "ERROR"


# ----- Fixtures -----


@pytest.fixture()
def _latwiss_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "tfstools_latwiss.tfs"


@pytest.fixture()
def _latwiss_tfs_frame() -> tfs.TfsDataFrame:
    tfs_file_path = INPUTS_DIR / "tfstools_latwiss.tfs"
    return tfs.read(tfs_file_path)
