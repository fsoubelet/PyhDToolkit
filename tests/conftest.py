import pathlib

import pytest
from cpymad.madx import Madx

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
LHC_SEQUENCE = INPUTS_DIR / "lhc_as-built.seq"
LHC_OPTICS = INPUTS_DIR / "opticsfile.22"


@pytest.fixture(scope="function")
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