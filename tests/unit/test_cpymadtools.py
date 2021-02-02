import random
import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.helpers import LatticeMatcher, Parameters
from pyhdtoolkit.cpymadtools.lattice_generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.latwiss import LaTwiss
from pyhdtoolkit.cpymadtools.plotters import (
    AperturePlotter,
    DynamicAperturePlotter,
    PhaseSpacePlotter,
    TuneDiagramPlotter,
)

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

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


class TestAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_aperture(self, tmp_path):
        savefig_dir = tmp_path / "test_plot_aperture"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "aperture.png"

        beam_fb = Parameters.beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3, verbose=True)
        madx = Madx(stdout=False)
        madx.input(GUIDO_LATTICE)
        figure = AperturePlotter.plot_aperture(madx, beam_fb, xlimits=(0, 20), savefig=saved_fig)
        assert saved_fig.is_file()
        return figure


class TestDynamicAperturePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_dynamic_aperture(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_aperture"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "dynamic_aperture.png"

        n_particles = 100
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, y_coords_stable, _, _ = _perform_tracking_for_coordinates(madx)
        x_coords_stable = np.array(x_coords_stable)
        y_coords_stable = np.array(y_coords_stable)
        figure = DynamicAperturePlotter.plot_dynamic_aperture(
            x_coords_stable, y_coords_stable, n_particles=n_particles, savefig=saved_fig
        )
        assert saved_fig.is_file()
        return figure


class TestLatticeGenerator:
    def test_base_cas_lattice_generation(self):
        base_cas_lattice = LatticeGenerator.generate_base_cas_lattice()
        assert isinstance(base_cas_lattice, str)
        assert len(base_cas_lattice) == 1493

    def test_onesext_cas_lattice(self):
        onesext_cas_lattice = LatticeGenerator.generate_onesext_cas_lattice()
        assert isinstance(onesext_cas_lattice, str)
        assert len(onesext_cas_lattice) == 2051

    def test_oneoct_cas_lattice(self):
        oneoct_cas_lattice = LatticeGenerator.generate_oneoct_cas_lattice()
        assert isinstance(oneoct_cas_lattice, str)
        assert len(oneoct_cas_lattice) == 2050

    def test_tripleterrors_study_reference(self):
        tripleterrors_study_reference = LatticeGenerator.generate_tripleterrors_study_reference()
        assert isinstance(tripleterrors_study_reference, str)
        assert len(tripleterrors_study_reference) == 1617

    @pytest.mark.parametrize(
        "randseed, tferror",
        [
            ("", ""),
            ("95", "195"),
            ("105038", "0.001"),
            (str(random.randint(0, 1e7)), str(random.randint(0, 1e7))),
            (random.randint(0, 1e7), random.randint(0, 1e7)),
        ],
    )
    def test_tripleterrors_study_tferror_job(self, randseed, tferror):
        tripleterrors_study_tferror_job = LatticeGenerator.generate_tripleterrors_study_tferror_job(
            rand_seed=randseed, tf_error=tferror,
        )
        assert isinstance(tripleterrors_study_tferror_job, str)
        assert len(tripleterrors_study_tferror_job) == 2521 + len(str(randseed)) + len(str(tferror))
        assert f"eoption, add, seed = {randseed};" in tripleterrors_study_tferror_job
        assert f"B2r = {tferror};" in tripleterrors_study_tferror_job

    @pytest.mark.parametrize(
        "randseed, mserror",
        [
            ("", ""),
            ("95", "195"),
            ("105038", "0.001"),
            (str(random.randint(0, 1e7)), str(random.randint(0, 1e7))),
            (random.randint(0, 1e7), random.randint(0, 1e7)),
        ],
    )
    def test_tripleterrors_study_mserror_job(self, randseed, mserror):
        tripleterrors_study_mserror_job = LatticeGenerator.generate_tripleterrors_study_mserror_job(
            rand_seed=randseed, ms_error=mserror,
        )
        assert isinstance(tripleterrors_study_mserror_job, str)
        assert len(tripleterrors_study_mserror_job) == 2384 + len(str(randseed)) + len(str(mserror))
        assert f"eoption, add, seed = {randseed};" in tripleterrors_study_mserror_job
        assert f"ealign, ds := {mserror} * 1E-3 * TGAUSS(GCUTR);" in tripleterrors_study_mserror_job


class TestLaTwiss:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_latwiss(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "latwiss.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )
        figure = LaTwiss.plot_latwiss(
            cpymad_instance=madx,
            title="Project 3 Base Lattice",
            xlimits=(-50, 1_050),
            beta_ylim=(5, 75),
            plot_sextupoles=True,
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
        figure = LaTwiss.plot_machine_survey(
            cpymad_instance=madx, show_elements=True, high_orders=True, figsize=(20, 15), savefig=saved_fig,
        )
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_machine_survey_without_elements(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        return LaTwiss.plot_machine_survey(
            cpymad_instance=madx, show_elements=False, high_orders=True, figsize=(20, 15)
        )


class TestLatticeMatcher:
    @pytest.mark.parametrize("beam", [1, 2, 3, 4])
    def test_lhc_tune_and_chroma_knobs(self, beam):
        expected_beam = 2 if beam == 4 else beam
        assert LatticeMatcher.get_tune_and_chroma_knobs("LHC", beam) == (
            f"dQx.b{expected_beam}",
            f"dQy.b{expected_beam}",
            f"dQpx.b{expected_beam}",
            f"dQpy.b{expected_beam}",
        )

    @pytest.mark.parametrize("beam", [1, 2, 3, 4])
    def test_hllhc_tune_and_chroma_knobs(self, beam):
        expected_beam = 2 if beam == 4 else beam
        assert LatticeMatcher.get_tune_and_chroma_knobs("HLLHC", beam) == (
            f"kqtf.b{expected_beam}",
            f"kqtd.b{expected_beam}",
            f"ksf.b{expected_beam}",
            f"ksd.b{expected_beam}",
        )

    @pytest.mark.parametrize("q1_target, q2_target", [(6.335, 6.29), (6.34, 6.27), (6.38, 6.27)])
    @pytest.mark.parametrize("dq1_target, dq2_target", [(100, 100), (95, 95), (105, 105)])
    def test_tune_and_chroma_matching(self, q1_target, q2_target, dq1_target, dq2_target):
        """Using my CAS19 project's lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)

        assert madx.table.summ.q1[0] != q1_target
        assert madx.table.summ.q2[0] != q2_target
        assert madx.table.summ.dq1[0] != dq1_target
        assert madx.table.summ.dq2[0] != dq2_target

        LatticeMatcher.perform_tune_and_chroma_matching(
            cpymad_instance=madx,
            sequence="CAS3",
            q1_target=q1_target,
            q2_target=q2_target,
            dq1_target=dq1_target,
            dq2_target=dq2_target,
            varied_knobs=["kqf", "kqd", "ksf", "ksd"],
        )

        assert np.isclose(madx.table.summ.q1[0], q1_target, rtol=1e-3)
        assert np.isclose(madx.table.summ.q2[0], q2_target, rtol=1e-3)
        assert np.isclose(madx.table.summ.dq1[0], dq1_target, rtol=1e-3)
        assert np.isclose(madx.table.summ.dq2[0], dq2_target, rtol=1e-3)


class TestParameters:
    @pytest.mark.parametrize(
        "pc_gev, en_x_m, en_y_m, delta_p, verbosity, result_dict",
        [
            (
                1.9,
                5e-6,
                5e-6,
                2e-3,
                False,
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
                True,
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
    def test_beam_parameters(self, pc_gev, en_x_m, en_y_m, delta_p, result_dict, verbosity):
        assert Parameters.beam_parameters(pc_gev, en_x_m, en_y_m, delta_p, verbosity) == result_dict


class TestPhaseSpacePlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_horizontal_courant_snyder_phase_space(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "phase_space.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space(
            madx, x_coords_stable, px_coords_stable, plane="Horizontal", savefig=saved_fig
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_vertical_courant_snyder_phase_space(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space(
            madx, x_coords_stable, px_coords_stable, plane="Vertical"
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        return figure

    def test_plot_courant_snyder_phase_space_wrong_plane_input(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, px_coords_stable = np.array([]), np.array([])  # no need for tracking
        with pytest.raises(ValueError):
            _ = PhaseSpacePlotter.plot_courant_snyder_phase_space(
                madx, x_coords_stable, px_coords_stable, plane="invalid_plane"
            )

    @pytest.mark.mpl_image_compare(tolerance=20, savefig_kwargs={"dpi": 200})
    def test_plot_horizontal_courant_snyder_phase_space_colored(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "colored_phase_space.png"

        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
            madx, x_coords_stable, px_coords_stable, plane="Horizontal", savefig=saved_fig
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        assert saved_fig.is_file()
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, savefig_kwargs={"dpi": 200})
    def test_plot_vertical_courant_snyder_phase_space_colored(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)
        figure = PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
            madx, x_coords_stable, px_coords_stable, plane="Vertical"
        )
        plt.xlim(-0.012 * 1e3, 0.02 * 1e3)
        plt.ylim(-0.02 * 1e3, 0.023 * 1e3)
        return figure

    def test_plot_courant_snyder_phase_space_colored_wrong_plane_input(self):
        """Using my CAS 19 project's base lattice."""
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, px_coords_stable = np.array([]), np.array([])  # no need for tracking
        with pytest.raises(ValueError):
            _ = PhaseSpacePlotter.plot_courant_snyder_phase_space_colored(
                madx, x_coords_stable, px_coords_stable, plane="invalid_plane"
            )


class TestTuneDiagramPlotter:
    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_blank_tune_diagram(self):
        """Does not need any input."""
        figure = TuneDiagramPlotter.plot_blank_tune_diagram()
        plt.xlim(0, 0.5)
        plt.ylim(0, 0.5)
        return figure

    @pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
    def test_plot_tune_diagram(self, tmp_path):
        """Using my CAS 19 project's base lattice."""
        savefig_dir = tmp_path / "test_plot_latwiss"
        savefig_dir.mkdir()
        saved_fig = savefig_dir / "tune_diagram.png"

        n_particles = 100
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        LatticeMatcher.perform_tune_and_chroma_matching(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        x_coords_stable, _, px_coords_stable, _ = _perform_tracking_for_coordinates(madx)

        x_coords_stable = np.array(x_coords_stable)
        qxs_stable, xgood_stable = [], []

        for particle in range(n_particles):
            if np.isnan(x_coords_stable[particle]).any():
                qxs_stable.append(0)
                xgood_stable.append(False)
            else:
                signal = x_coords_stable[particle]
                signal = np.array(signal)
                try:
                    qxs_stable.append(pnf.naff(signal, n_turns, 1, 0, False)[0][1])
                    xgood_stable.append(True)
                except:
                    qxs_stable.append(0)
                    xgood_stable.append(False)

        qxs_stable = np.array(qxs_stable)
        xgood_stable = np.array(xgood_stable)
        figure = TuneDiagramPlotter.plot_tune_diagram(madx, qxs_stable, xgood_stable, savefig=saved_fig)
        plt.xlim(0, 0.4)
        plt.ylim(0, 0.4)
        assert saved_fig.is_file()
        return figure


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
        cpymad_instance.command.track()
        cpymad_instance.command.start(X=starting_x, PX=0, Y=0, PY=0, T=0, PT=0)
        cpymad_instance.command.run(turns=n_turns)
        cpymad_instance.command.endtrack()

        x_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["x"].to_numpy())
        y_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["y"].to_numpy())
        px_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["px"].to_numpy())
        py_coords_stable.append(cpymad_instance.table["track.obs0001.p0001"].dframe()["py"].to_numpy())
    return x_coords_stable, y_coords_stable, px_coords_stable, py_coords_stable
