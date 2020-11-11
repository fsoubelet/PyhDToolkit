import pathlib

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
import tfs

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.helpers import LatticeMatcher
from pyhdtoolkit.cpymadtools.lattice_generators import LatticeGenerator
from pyhdtoolkit.tfstools.latwiss import LaTwiss

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


class TestLaTwiss:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel")
    def test_plot_latwiss_from_frame(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_matching(madx, "CAS3", 6.335, 6.29)
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", 100, 100)
        twiss = madx.table.twiss.dframe()

        figure = LaTwiss.plot_latwiss(
            twiss_ouptut=twiss,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel")
    def test_plot_latwiss_from_tfs_file(self, tmp_path, _latwiss_tfs):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        figure = LaTwiss.plot_latwiss(
            twiss_ouptut=_latwiss_tfs,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure


@pytest.fixture()
def _latwiss_tfs() -> tfs.TfsDataFrame:
    tfs_file_path = pathlib.Path(__file__).parent.parent / "inputs" / "tfstools_latwiss.tfs"
    return tfs.read(tfs_file_path, index="NAME")
