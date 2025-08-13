import pathlib

import pytest
from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.cpymadtools._generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()
CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
LHC_SEQUENCE = INPUTS_DIR / "madx" / "lhc_as-built.seq"
LHC_OPTICS = INPUTS_DIR / "madx" / "opticsfile.22"
LHC_INJ_OPTICS = INPUTS_DIR / "madx" / "opticsfile.1"
LHC_B1_APERTURE = INPUTS_DIR / "madx" / "aperture.b1.madx"
LHC_B1_APERTOL = INPUTS_DIR / "madx" / "aper_tol.b1.madx"

# ----- Fixtures for cpymadtools tests ----- #


@pytest.fixture
def _matched_base_lattice() -> Madx:
    """Base CAS lattice matched to default working point."""
    with Madx(stdout=False) as madx:
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx,
            sequence="CAS3",
            q1_target=6.335,
            q2_target=6.29,
            dq1_target=100,
            dq2_target=100,
            varied_knobs=["kqf", "kqd", "ksf", "ksd"],
        )
        yield madx


@pytest.fixture
def _bare_lhc_madx() -> Madx:
    """Only loading sequence and optics."""
    with Madx(stdout=False) as madx:
        madx.call(str(LHC_SEQUENCE.absolute()))
        madx.call(str(LHC_OPTICS.absolute()))  # opticsfile.22
        yield madx


@pytest.fixture
def _non_matched_lhc_madx() -> Madx:
    """Important properties & beam for lhcb1 declared and in use, NO MATCHING done here."""
    with Madx(stdout=False) as madx:
        madx.call(str(LHC_SEQUENCE.absolute()))
        madx.call(str(LHC_OPTICS.absolute()))  # opticsfile.22

        nrj = madx.globals["NRJ"] = 6500
        madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
        geometric_emit = madx.globals["geometric_emit"] = 3.75e-6 / (madx.globals["NRJ"] / 0.938)
        madx.command.beam(
            sequence="lhcb1",
            bv=1,
            energy=nrj,
            particle="proton",
            npart=1.0e10,
            kbunch=1,
            ex=geometric_emit,
            ey=geometric_emit,
        )
        madx.use(sequence="lhcb1")
        yield madx


@pytest.fixture
def _matched_lhc_madx() -> Madx:
    """Important properties & beam for lhcb1 declared and in use, WITH matching to working point."""
    with Madx(stdout=False) as madx:
        madx.call(str(LHC_SEQUENCE.absolute()))
        madx.call(str(LHC_OPTICS.absolute()))  # opticsfile.22

        nrj = madx.globals["NRJ"] = 6500
        madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
        geometric_emit = madx.globals["geometric_emit"] = 3.75e-6 / (madx.globals["NRJ"] / 0.938)
        madx.command.beam(
            sequence="lhcb1",
            bv=1,
            energy=nrj,
            particle="proton",
            npart=1.0e10,
            kbunch=1,
            ex=geometric_emit,
            ey=geometric_emit,
        )
        madx.use(sequence="lhcb1")
        match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=True)
        yield madx


@pytest.fixture
def _cycled_lhc_sequences() -> Madx:
    """
    Important properties & beam for lhcb1 and lhcb1 declared and in use,
    WITH a matching performed to working point.
    Uses Run 2 normalized emittances values.
    """
    with Madx(stdout=False) as madx:
        madx.call(str(LHC_SEQUENCE.absolute()))
        madx.call(str(LHC_OPTICS.absolute()))  # opticsfile.22

        lhc.re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
        lhc.re_cycle_sequence(madx, sequence="lhcb2", start="IP3")
        lhc.make_lhc_beams(madx, nemitt_x=3.75e-6, nemitt_y=3.75e-6, energy=6500)
        yield madx


@pytest.fixture
def _injection_aperture_tolerances_lhc_madx() -> Madx:
    """Uses Run 2 normalized emittances values."""
    with Madx(stdout=False) as madx:
        madx.call(str(LHC_SEQUENCE.absolute()))
        madx.call(str(LHC_INJ_OPTICS.absolute()))  # opticsfile.1

        lhc.make_lhc_beams(madx, nemitt_x=3.75e-6, nemitt_y=3.75e-6, energy=450)  # injection
        madx.use(sequence="lhcb1")

        madx.call(str(LHC_B1_APERTURE.absolute()))
        madx.call(str(LHC_B1_APERTOL.absolute()))

        madx.command.twiss()
        madx.command.aperture(cor=0.002, dp=8.6e-4, halo="{6,6,6,6}", bbeat=1.05, dparx=0.14, dpary=0.14)
        yield madx


@pytest.fixture
def _collision_aperture_tolerances_lhc_madx() -> Madx:
    """Uses Run 2 normalized emittances values."""
    with Madx(stdout=False) as madx:
        madx.call(str(LHC_SEQUENCE.absolute()))
        madx.call(str(LHC_OPTICS.absolute()))  # opticsfile.22

        lhc.make_lhc_beams(madx, nemitt_x=3.75e-6, nemitt_y=3.75e-6, energy=6500)  # collision
        madx.use(sequence="lhcb1")

        madx.call(str(LHC_B1_APERTURE.absolute()))
        madx.call(str(LHC_B1_APERTOL.absolute()))

        madx.command.twiss()
        madx.command.aperture(cor=0.002, dp=8.6e-4, halo="{6,6,6,6}", bbeat=1.05, dparx=0.14, dpary=0.14)
        yield madx
