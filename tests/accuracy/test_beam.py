import pytest
import numpy as np
from pyhdtoolkit.optics.beam import Beam


class TestProperties:
    def test_gamma_rel(self):
        assert Beam(6500, 2.5e-6).gamma_rel == 6928.628011131436

    def test_beta_rel(self):
        assert Beam(6500, 2.5e-6).beta_rel == 1.0000000104153894

    def test_brho(self):
        assert Beam(6500, 2.5e-6).brho == 7.227222137900961e-05

    def test_normalized_emittance(self):
        assert Beam(6500, 2.5e-6).normalized_emittance == 0.01732157020823949

    def test_rms_emittance(self):
        assert Beam(6500, 2.5e-6).rms_emittance == 3.6082179183888383e-10


class TestCalculations:
    def test_lhc_revolution_frequency(self):
        lhc_beam = Beam(6500, 2.5e-6)
        assert lhc_beam.revolution_frequency() == 11245.499628523643

    @pytest.mark.parametrize(
        "alpha_p, result",
        [(0, 2.083077890845299e-08), (1e-5, -9.979169221091548e-06), (-500, 500.0000000208308)],
    )
    def test_eta(self, alpha_p, result):
        assert Beam(6500, 2.5e-6).eta(alpha_p) == result

    @pytest.mark.parametrize(
        "alpha_p, result",
        [(1e-5, 316.2277660168379), (500, 0.044721359549995794)],
    )
    def test_gamma_transition(self, alpha_p, result):
        assert Beam(6500, 2.5e-6).gamma_transition(alpha_p) == result

    def test_gamma_transition_raises(self):
        with pytest.raises(ZeroDivisionError):
            Beam(6500, 2.5e-6).gamma_transition(0)
