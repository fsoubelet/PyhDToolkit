import pathlib

import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
LHC_SEQUENCE = INPUTS_DIR / "lhc_as-built.seq"
LHC_OPTICS = INPUTS_DIR / "opticsfile.22"


# ----- Fixtures for cpymadtools tests ----- #


@pytest.fixture()
def _bare_lhc_madx() -> Madx:
    """Only loading sequence and optics."""
    madx = Madx(stdout=False)
    madx.call(str(LHC_SEQUENCE.absolute()))
    madx.call(str(LHC_OPTICS.absolute()))
    yield madx
    madx.exit()


@pytest.fixture()
def _non_matched_lhc_madx() -> Madx:
    """Important properties & beam for lhcb1 declared and in use, NO MATCHING done here."""
    madx = Madx(stdout=False)
    madx.call(str(LHC_SEQUENCE.absolute()))
    madx.call(str(LHC_OPTICS.absolute()))

    NRJ = madx.globals["NRJ"] = 6500
    madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
    geometric_emit = madx.globals["geometric_emit"] = 3.75e-6 / (madx.globals["NRJ"] / 0.938)
    madx.command.beam(
        sequence="lhcb1",
        bv=1,
        energy=NRJ,
        particle="proton",
        npart=1.0e10,
        kbunch=1,
        ex=geometric_emit,
        ey=geometric_emit,
    )
    madx.use(sequence="lhcb1")
    yield madx
    madx.exit()


@pytest.fixture()
def _matched_lhc_madx() -> Madx:
    """Important properties & beam for lhcb1 declared and in use, WITH matching to working point."""
    madx = Madx(stdout=False)
    madx.call(str(LHC_SEQUENCE.absolute()))
    madx.call(str(LHC_OPTICS.absolute()))

    NRJ = madx.globals["NRJ"] = 6500
    madx.globals["brho"] = madx.globals["NRJ"] * 1e9 / madx.globals.clight
    geometric_emit = madx.globals["geometric_emit"] = 3.75e-6 / (madx.globals["NRJ"] / 0.938)
    madx.command.beam(
        sequence="lhcb1",
        bv=1,
        energy=NRJ,
        particle="proton",
        npart=1.0e10,
        kbunch=1,
        ex=geometric_emit,
        ey=geometric_emit,
    )
    madx.use(sequence="lhcb1")
    match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0, telescopic_squeeze=True)
    yield madx
    madx.exit()
