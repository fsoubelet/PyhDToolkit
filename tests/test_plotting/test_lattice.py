import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools._generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.plotting.lattice import plot_latwiss, plot_machine_survey
from pyhdtoolkit.plotting.layout import scale_patches

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
mpl.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()
OCT_LATTICE = LatticeGenerator.generate_oneoct_cas_lattice()
ELETTRA_LATTICE = INPUTS_DIR / "madx" / "elettra2_v15_VADER_2.3T.madx"
ELETTRA_OPTICS = INPUTS_DIR / "madx" / "optics_elettra2_v15_VADER_2.3T.madx"


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_latwiss():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        figure = plt.figure(figsize=(18, 11))
        plot_latwiss(
            madx,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            k2l_lim=(-0.25, 0.25),
            plot_bpms=True,
        )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_latwiss_with_scaled_patches():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        figure = plt.figure(figsize=(18, 11))
        plot_latwiss(
            madx,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            k0l_lim=115,
            k1l_lim=8,
            k2l_lim=(-0.25, 0.25),
            plot_bpms=True,
        )
        # Scale all bends and quads patches
        scale_patches(ax=figure.axes[0], scale=100, ylabel=r"$K_{1}L$ $[10^{-2} m^{-1}]$")
        scale_patches(ax=figure.axes[1], scale=1000, ylabel=r"$K_{0}L$ $[mrad]$")
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_latwiss_single_value_ylimts_inputs():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        figure = plt.figure(figsize=(18, 11))
        plot_latwiss(
            madx,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            k1l_lim=8e-2,
            k2l_lim=0.35,
            plot_bpms=True,
        )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_latwiss_with_octupoles():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(OCT_LATTICE)
        madx.input("koct = -15;")
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        figure = plt.figure(figsize=(18, 11))
        plot_latwiss(
            madx,
            title="Project 3 Octupole Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            k1l_lim=-1e-1,  # tests that negative values are handled correctly too
            k2l_lim=0.6,
            k3l_lim=25,
            lw=2,
            plot_bpms=True,
        )
        plt.tight_layout()
    return figure


def test_plot_layout_raises_on_wrong_limits_type():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        plt.figure(figsize=(18, 11))

        with pytest.raises(TypeError):
            plot_latwiss(madx, k1l_lim=[8e-2])


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_latwiss_with_dipole_k1():
    """Using ELETTRA2.0 lattice provided by Axel."""
    elettra_parameters = {"ON_SEXT": 1, "ON_OCT": 1, "ON_RF": 1, "NRJ_GeV": 2.4, "DELTAP": 0.00095}

    with Madx(stdout=False) as madx:
        with madx.batch():
            madx.globals.update(elettra_parameters)
        madx.call(str(ELETTRA_LATTICE))
        madx.call(str(ELETTRA_OPTICS))
        madx.use(sequence="ring")
        madx.command.twiss(sequence="ring")

        init_twiss = madx.table.twiss.dframe()
        x0 = init_twiss.s[init_twiss.name == "ll:1"].iloc[0]
        x1 = init_twiss.s[init_twiss.name == "ll:3"].iloc[0]

        figure = plt.figure(figsize=(18, 11))
        plot_latwiss(
            madx,
            title="Elettra Cell",
            xlimits=(x0, x1),
            k0l_lim=(-7e-2, 7e-2),
            k1l_lim=(-1.5, 1.5),
            disp_ylim=(-madx.table.twiss.dx.max() * 2, madx.table.twiss.dx.max() * 2),
            plot_dipole_k1=True,
            lw=2,
        )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_machine_survey_with_elements():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)

        figure = plt.figure(figsize=(16, 11))
        plot_machine_survey(madx, show_elements=True, high_orders=True)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_machine_survey_without_elements():
    """Using my CAS 19 project's base lattice."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        figure = plt.figure(figsize=(16, 11))
        plot_machine_survey(madx, show_elements=False, high_orders=True)
    return figure
