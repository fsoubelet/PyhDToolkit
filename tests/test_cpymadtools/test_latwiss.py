import matplotlib
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.latwiss import plot_latwiss, plot_machine_survey
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")


BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


class TestLaTwiss:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )
        figure = plot_latwiss(
            madx=madx,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            k2l_lim=(-0.25, 0.25),
            plot_bpms=True,
            savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_with_elements(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_survey"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "survey.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        figure = plot_machine_survey(
            madx=madx, show_elements=True, high_orders=True, figsize=(20, 15), savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_without_elements(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        return plot_machine_survey(madx=madx, show_elements=False, high_orders=True, figsize=(20, 15))
