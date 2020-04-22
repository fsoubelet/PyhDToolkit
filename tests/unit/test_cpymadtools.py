"""
Considering cpymad only installs on Linux, most test classes have been decorated with a skipif
and none of those will run unless in a linux environment.
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytest

from matplotlib.testing.decorators import image_comparison

from pyhdtoolkit.cpymadtools.helpers import LatticeMatcher, Parameters
from pyhdtoolkit.cpymadtools.lattice_generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.latwiss import LaTwiss
from pyhdtoolkit.cpymadtools.plotters import (
    AperturePlotter,
    DynamicAperturePlotter,
    PhaseSpacePlotter,
    TuneDiagramPlotter,
)

# This will only work on Linux, and we don't want to fail tests because import is not ok on some platforms
try:
    import cpymad
    from cpymad.madx import Madx
except ModuleNotFoundError:
    pass

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()
GUIDO_LATTICE = f"""
circum = 500.0;
n_cells = 25; ! Number of cells 
lcell = circum / n_cells;
lq = 0.5; ! Length of a quadrupole
ldip = 3.5;

! ELEMENT DEFINITIONS
! Define bending magnet as multipole, we have 4 bending magnets per cell
!mb:multipole, knl={{2.0*pi/(4*n_cells)}};

mb: sbend, l=ldip, angle=2.0*pi/(4*n_cells), apertype=ellipse, aperture= {{0.09, 0.065}};
f = lcell / (2 * sqrt(2));

! Define quadrupoles as multipoles 
qf: multipole, knl:={{0,1/f+qtrim_f}}; 
qd: multipole, knl:={{0,-1/f+qtrim_d}};
qf: quadrupole, l=lq, K1:=1/f/lq  + qtrim_f/lq, apertype=ellipse, aperture={{0.065, 0.065}}; 
qd: quadrupole, l=lq, K1:=-1/f/lq + qtrim_d/lq, apertype=ellipse, aperture={{0.065, 0.065}};

! Define the sextupoles as multipole
!ATTENTION: must use knl:= and NOT knl= to match later! 
lsex = 0.00001; ! dummy length, only used in the sequence
msf: multipole, knl:={{0,0,ksf}};
msd: multipole, knl:={{0,0,ksd}};

! SEQUENCE DECLARATION
! Switch off the warning to limit outputs (use this option with moderation)
option, warn=false;
cas19: sequence, refer=centre, l=circum;
   start_machine: marker, at = 0;
   n = 1;
   while (n < n_cells+1) {{
    qf: qf,   at=(n-1)*lcell+ lq/2.0;
    msf: msf, at=(n-1)*lcell + lsex/2.0+lq/1.0;
    mb: mb,   at=(n-1)*lcell + 0.15*lcell;
    mb: mb,   at=(n-1)*lcell + 0.35*lcell;
    qd: qd,   at=(n-1)*lcell + 0.50*lcell+ lq/2.0;
    msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0+lq/1.0;
    mb: mb,   at=(n-1)*lcell + 0.65*lcell;
    mb: mb,   at=(n-1)*lcell + 0.85*lcell;
    n = n + 1;
}}
end_machine: marker at=circum;
endsequence;
option, warn=true;

! DEFINE BEAM PARAMETERS AND PROPERTIES
beam, particle=proton, sequence=cas19, energy=2.1190456574946737, exn=5e-06, eyn=5e-06,sige=5e-06;
use, sequence=cas19;
select, flag=twiss, column=apertype, aper_1, aper_2;

ksf=0;
ksd=0;
twiss;
"""


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="The cpymad library will only install on linux.")
class TestAperturePlotter:
    @image_comparison(
        baseline_images=["physical_aperture"], remove_text=True, extensions=["png", "pdf"], savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_aperture(self):
        beam_fb = Parameters.beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3, verbose=True)
        madx = Madx(stdout=False)
        madx.input(GUIDO_LATTICE)
        AperturePlotter.plot_aperture(madx, beam_fb, xlimits=(0, 20))


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="The cpymad library will only install on linux.")
class TestDynamicAperturePlotter:
    @image_comparison(
        baseline_images=["dynamic_aperture"], remove_text=True, extensions=["png", "pdf"], savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_dynamic_aperture(self):
        """Using my CAS 19 project's base lattice."""
        n_particles = 100
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_matching(madx, "CAS3", 6.335, 6.29)
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", 100, 100)

        x_coords_stable, y_coords_stable, _, _ = _perform_tracking_for_coordinates(madx)
        DynamicAperturePlotter.plot_dynamic_aperture(x_coords_stable, y_coords_stable, n_particles=n_particles)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="The cpymad library will only install on linux.")
class TestLaTwiss:
    @image_comparison(
        baseline_images=["latwiss"], remove_text=True, extensions=["png", "pdf"], savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_latwiss(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_matching(madx, "CAS3", 6.335, 6.29)
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", 100, 100)
        LaTwiss.plot_latwiss(cpymad_instance=madx, title="Project 3 Base Lattice")

    @image_comparison(
        baseline_images=["machine_survey"], remove_text=True, extensions=["png", "pdf"], savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_machine_survey(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        Latwiss.plot_machine_survey(cpymad_instance=madx, show_elements=True, high_orders=True, figsize=(20, 15))


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="The cpymad library will only install on linux.")
class TestLatticeMatcher:
    @pytest.mark.parametrize("q1_target, q2_target", [(6.335, 6.29), (6.34, 6.27), (6.38, 6.27)])
    def test_tune_matching(self, q1_target, q2_target):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.q1[0] != q1_target
        assert madx.table.summ.q2[0] != q2_target
        LatticeMatcher.perform_tune_matching(madx, "CAS3", q1_target, q2_target)
        assert np.isclose(madx.table.summ.q1[0], q1_target)
        assert np.isclose(madx.table.summ.q2[0], q2_target)

    @pytest.mark.parametrize("dq1_target, dq2_target", [(100, 100), (95, 95), (105, 105)])
    def test_chroma_matching(self, dq1_target, dq2_target):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        assert madx.table.summ.dq1[0] != dq1_target
        assert madx.table.summ.dq2[0] != dq2_target
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", dq1_target, dq2_target)
        assert np.isclose(madx.table.summ.dq1[0], dq1_target)
        assert np.isclose(madx.table.summ.dq2[0], dq2_target)


class TestParameters:
    @pytest.mark.parametrize(
        "pc_Gev, en_x_m, en_y_m, delta_p, result_dict",
        [
            (
                1.9,
                5e-6,
                5e-6,
                2e-3,
                {
                    "pc_GeV": 1.9,
                    "B_rho_Tm": 6.3376399999999995,
                    "E_0_GeV": 0.9382720813,
                    "E_tot_GeV": 2.1190456574946737,
                    "E_kin_GeV": 1.1807735761946736,
                    "gamma_r": 2.258455409393277,
                    "beta_r": 0.8966300434726596,
                    "en_x_m": 5e-06,
                    "en_y_m": 5e-06,
                    "eg_x_m": 2.469137056052632e-06,
                    "eg_y_m": 2.469137056052632e-06,
                    "deltap_p": 0.002,
                },
            ),
            (
                19,
                5e-6,
                5e-6,
                2e-4,
                {
                    "pc_GeV": 19,
                    "B_rho_Tm": 63.3764,
                    "E_0_GeV": 0.9382720813,
                    "E_tot_GeV": 19.023153116624673,
                    "E_kin_GeV": 18.084881035324674,
                    "gamma_r": 20.274666054506927,
                    "beta_r": 0.9987828980567665,
                    "en_x_m": 5e-06,
                    "en_y_m": 5e-06,
                    "eg_x_m": 2.4691370560526314e-07,
                    "eg_y_m": 2.4691370560526314e-07,
                    "deltap_p": 0.0002,
                },
            ),
        ],
    )
    def test_beam_parameters(self, pc_Gev, en_x_m, en_y_m, delta_p, result_dict):
        assert Parameters.beam_parameters(pc_Gev, en_x_m, en_y_m, delta_p) == result_dict


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="The cpymad library will only install on linux.")
class TestPhaseSpacePlotter:
    @image_comparison(
        baseline_images=["normalized_phase_space"],
        remove_text=True,
        extensions=["png", "pdf"],
        savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_normalized_phase_space(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_matching(madx, "CAS3", 6.335, 6.29)
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", 100, 100)

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        PhaseSpacePlotter.plot_normalized_phase_space(madx, x_coords_stable, px_coords_stable, plane="Horizontal")
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)

    @image_comparison(
        baseline_images=["normalized_phase_space_colored"],
        remove_text=True,
        extensions=["png", "pdf"],
        savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_normalized_phase_space_colored(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_matching(madx, "CAS3", 6.335, 6.29)
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", 100, 100)

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        PhaseSpacePlotter.plot_normalized_phase_space_colored(
            madx, x_coords_stable, px_coords_stable, plane="Horizontal"
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="The cpymad library will only install on linux.")
class TestTuneDiagramPlotter:
    @image_comparison(
        baseline_images=["blank_tune_diagram"], remove_text=True, extensions=["png", "pdf"], savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_blank_tune_diagram(self):
        """Does not need any input."""
        TuneDiagramPlotter.plot_blank_tune_diagram()
        plt.xlim(0, 0.5)
        plt.ylim(0, 0.5)

    @image_comparison(
        baseline_images=["tune_diagram"], remove_text=True, extensions=["png", "pdf"], savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Not sure this is the way to how to handle this yet.")
    def test_plot_tune_diagram(self):
        """Using my CAS 19 project's base lattice."""
        n_particles = 100
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_matching(madx, "CAS3", 6.335, 6.29)
        LatticeMatcher.perform_chroma_matching(madx, "CAS3", 100, 100)

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        x_coords_stable = np.array(x_coords_stable)
        Qxs_stable, xgood_stable = [], []

        for particle in range(n_particles):
            if np.isnan(x_coords_stable[particle]).any():
                # print(f"Particle {particle} lost!")
                Qxs_stable.append(0)
                xgood_stable.append(False)
            else:
                signal = x_coords_stable[particle]
                signal = np.array(signal)
                try:
                    Qxs_stable.append(pnf.naff(signal, n_turns, 1, 0, False)[0][1])
                    xgood_stable.append(True)
                except:
                    # print(f"Particle {particle} lost!")
                    Qxs_stable.append(0)
                    xgood_stable.append(False)

        Qxs_stable = np.array(Qxs_stable)
        xgood_stable = np.array(xgood_stable)
        TuneDiagramPlotter.plot_tune_diagram(madx, Qxs_stable, xgood_stable)
        plt.xlim(0, 0.4)
        plt.ylim(0, 0.4)


# ---------------------- Private Utilities ---------------------- #


def _perform_tracking_for_coordinates(cpymad_instance) -> tuple:
    """
    Tracks 100 particles on 500 turns.
    This modifies inplace the state of the provided cpymad_instance.

    Args:
        cpymad_instance: an instantiated cpymad.madx.Madx object

    Returns:
        The x, y, px, py coordinates along the tracking.
    """
    # Toning the tracking down in particles / turns so it doesn't take too long (~20s?)
    n_particles = 100
    n_turns = 500
    initial_x_coordinates = np.linspace(1e-4, 0.05, n_particles)
    x_coords_stable, px_coords_stable, y_coords_stable, py_coords_stable = [], [], [], []

    for _, starting_x in enumerate(initial_x_coordinates):
        cpymad_instance.input(
            f"""
    TRACK;
    START, X={starting_x}, PX=0, Y=0.0, PY=0, T=0, PT=0;
    RUN, TURNS={n_turns};
    ENDTRACK;
    """
        )
        x_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["x"])
        y_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["y"])
        px_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["px"])
        py_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["py"])
    return x_coords_stable, y_coords_stable, px_coords_stable, py_coords_stable
