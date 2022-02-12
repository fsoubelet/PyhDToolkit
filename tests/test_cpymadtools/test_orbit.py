import math

import pytest

from pyhdtoolkit.cpymadtools.constants import LHC_CROSSING_SCHEMES  # for coverage
from pyhdtoolkit.cpymadtools.lhc import make_lhc_beams, re_cycle_sequence
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.orbit import (
    correct_lhc_orbit,
    get_current_orbit_setup,
    lhc_orbit_variables,
    setup_lhc_orbit,
)


class TestOrbit:
    def test_lhc_orbit_variables(self):
        assert lhc_orbit_variables() == (
            [
                "on_crab1",
                "on_crab5",
                "on_x1",
                "on_sep1",
                "on_o1",
                "on_oh1",
                "on_ov1",
                "on_x2",
                "on_sep2",
                "on_o2",
                "on_oe2",
                "on_a2",
                "on_oh2",
                "on_ov2",
                "on_x5",
                "on_sep5",
                "on_o5",
                "on_oh5",
                "on_ov5",
                "on_phi_IR5",
                "on_x8",
                "on_sep8",
                "on_o8",
                "on_a8",
                "on_sep8h",
                "on_x8v",
                "on_oh8",
                "on_ov8",
                "on_alice",
                "on_sol_alice",
                "on_lhcb",
                "on_sol_atlas",
                "on_sol_cms",
                "phi_IR1",
                "phi_IR2",
                "phi_IR5",
                "phi_IR8",
            ],
            {"on_ssep1": "on_sep1", "on_xx1": "on_x1", "on_ssep5": "on_sep5", "on_xx5": "on_x5"},
        )

    def test_lhc_orbit_setup_fals_on_unknown_scheme(self, _non_matched_lhc_madx, caplog):
        madx = _non_matched_lhc_madx

        with pytest.raises(ValueError):
            setup_lhc_orbit(madx, scheme="unknown")

        for record in caplog.records:
            assert record.levelname == "ERROR"

    @pytest.mark.parametrize("scheme", list(LHC_CROSSING_SCHEMES.keys()))
    def test_lhc_orbit_setup(self, scheme, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        setup_lhc_orbit(madx, scheme=scheme)
        variables, special = lhc_orbit_variables()

        for orbit_variable in variables:
            value = LHC_CROSSING_SCHEMES[scheme].get(orbit_variable, 0)
            assert madx.globals[orbit_variable] == value

        for special_variable, copy_from in special.items():
            assert madx.globals[special_variable] == madx.globals[copy_from]

    def test_get_orbit_setup(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        setup_lhc_orbit(madx, scheme="flat")
        setup = get_current_orbit_setup(madx)

        assert isinstance(setup, dict)
        assert all(orbit_var in setup.keys() for orbit_var in lhc_orbit_variables()[0])
        assert all(special_var in setup.keys() for special_var in lhc_orbit_variables()[1])

    def test_orbit_correction(self, _bare_lhc_madx):
        madx = _bare_lhc_madx
        re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
        _ = setup_lhc_orbit(madx, scheme="flat")
        make_lhc_beams(madx)
        madx.use(sequence="lhcb1")
        match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)
        assert madx.table.summ["xcorms"][0] == 0  # rms of horizontal CO

        madx.select(flag="error", pattern="MQ.13R3.B1")  # arc quad in sector 34
        madx.command.ealign(dx="1E-3")
        madx.twiss()
        assert madx.table.summ["xcorms"][0] > 1e-3

        correct_lhc_orbit(madx, sequence="lhcb1")
        assert math.isclose(madx.table.summ["xcorms"], 0, abs_tol=1e-5)
