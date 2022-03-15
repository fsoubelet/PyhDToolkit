import random

from pyhdtoolkit.cpymadtools.constants import (
    LHC_KCD_KNOBS,
    LHC_KCO_KNOBS,
    LHC_KCOSX_KNOBS,
    LHC_KCOX_KNOBS,
    LHC_KCS_KNOBS,
    LHC_KCSSX_KNOBS,
    LHC_KCSX_KNOBS,
    LHC_KCTX_KNOBS,
    LHC_KO_KNOBS,
    LHC_KQS_KNOBS,
    LHC_KQSX_KNOBS,
    LHC_KQTF_KNOBS,
    LHC_KSF_KNOBS,
    LHC_KSS_KNOBS,
    LHC_TRIPLETS_REGEX,
)
from pyhdtoolkit.cpymadtools.correctors import (
    query_arc_correctors_powering,
    query_triplet_correctors_powering,
)
from pyhdtoolkit.cpymadtools.lhc import make_lhc_beams

ALL_TRIPLET_CORRECTOR_KNOBS = (
    LHC_KQSX_KNOBS + LHC_KCSX_KNOBS + LHC_KCSSX_KNOBS + LHC_KCOX_KNOBS + LHC_KCOSX_KNOBS + LHC_KCTX_KNOBS
)
ALL_ARC_CORRECTOR_KNOBS = (
    LHC_KQTF_KNOBS
    + LHC_KQS_KNOBS
    + LHC_KSF_KNOBS
    + LHC_KSS_KNOBS
    + LHC_KCS_KNOBS
    + LHC_KCO_KNOBS
    + LHC_KCD_KNOBS
    + LHC_KO_KNOBS
)


class TestCorrectors:
    def test_query_undefined_triplet_corrector_knobs(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        make_lhc_beams(madx)  # parameters don't matter, just need beams and brho defined
        triplet_knobs = query_triplet_correctors_powering(madx)
        assert all(knob in triplet_knobs for knob in ALL_TRIPLET_CORRECTOR_KNOBS)
        assert all(knob_value == 0 for knob_value in triplet_knobs.values())  # as none were set

    def test_query_defined_triplet_corrector_knobs(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        make_lhc_beams(madx)  # parameters don't matter, just need beams and brho defined
        fake_knob_values = {knob: random.random() for knob in ALL_TRIPLET_CORRECTOR_KNOBS}
        with madx.batch():
            madx.globals.update(fake_knob_values)
        triplet_knobs = query_triplet_correctors_powering(madx)

        assert all(knob in triplet_knobs for knob in ALL_TRIPLET_CORRECTOR_KNOBS)
        assert all(knob_value != 0 for knob_value in triplet_knobs.values())

    def test_query_undefined_arc_corrector_knobs(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        make_lhc_beams(madx)  # parameters don't matter, just need beams and brho defined
        arc_knobs = query_arc_correctors_powering(madx)
        assert all(knob in arc_knobs for knob in ALL_ARC_CORRECTOR_KNOBS)
        assert all(abs(knob_value) < 115 for knob_value in arc_knobs.values())  # set in opticsfile

    def test_query_defined_arc_corrector_knobs(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        make_lhc_beams(madx)  # parameters don't matter, just need beams and brho defined
        fake_knob_values = {knob: random.random() for knob in ALL_ARC_CORRECTOR_KNOBS}
        with madx.batch():
            madx.globals.update(fake_knob_values)
        arc_knobs = query_arc_correctors_powering(madx)

        assert all(knob in arc_knobs for knob in ALL_ARC_CORRECTOR_KNOBS)
        assert all(knob_value != 0 for knob_value in arc_knobs.values())
