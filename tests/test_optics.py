import pathlib

import numpy as np
import pytest

from pyhdtoolkit.optics import ripken, twiss
from pyhdtoolkit.optics.beam import Beam

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
INPUT_PATHS = {
    "alpha_beta": INPUTS_DIR / "alpha_beta.npy",
    "u_vector": INPUTS_DIR / "u_vector.npy",
    "u_bar": INPUTS_DIR / "u_bar.npy",
    "beta11": INPUTS_DIR / "beta11.npy",
    "beta21": INPUTS_DIR / "beta21.npy",
    "lebedev": INPUTS_DIR / "lebedev_size.npy",
}


class TestBeamProperties:
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


class TestBeamCalculations:
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
        "alpha_p, result", [(1e-5, 316.2277660168379), (500, 0.044721359549995794)],
    )
    def test_gamma_transition(self, alpha_p, result):
        assert Beam(6500, 2.5e-6).gamma_transition(alpha_p) == result

    def test_gamma_transition_raises(self):
        with pytest.raises(ZeroDivisionError):
            Beam(6500, 2.5e-6).gamma_transition(0)


class TestRipken:
    def test_beam_size(self, _fake_coordinates):
        assert np.allclose(ripken._beam_size(_fake_coordinates), _fake_coordinates.std())
        assert np.allclose(
            ripken._beam_size(_fake_coordinates, method="rms"),
            np.sqrt(np.mean(np.square(_fake_coordinates))),
        )

    def test_beam_size_raises(self, _fake_coordinates):
        with pytest.raises(NotImplementedError):
            _ = ripken._beam_size(_fake_coordinates, method="not_real")

    @pytest.mark.parametrize("beta11", [0.3312])
    @pytest.mark.parametrize("beta21", [1])
    @pytest.mark.parametrize("emit_x", [5e-6, 2.75e-6, 3.5e-6])
    @pytest.mark.parametrize("emit_y", [5e-6, 2.75e-6, 3.5e-6])
    def test_lebedev_size_floats(self, beta11, beta21, emit_x, emit_y):
        assert ripken.lebedev_beam_size(
            beta1_=beta11, beta2_=beta21, geom_emit_x=emit_x, geom_emit_y=emit_y
        ) == np.sqrt(emit_x * beta11 + emit_y * beta21)


class TestTwiss:
    def test_courant_snyder_transform(self):
        alpha_beta = np.load(INPUT_PATHS["alpha_beta"])
        u_vector = np.load(INPUT_PATHS["u_vector"])
        u_bar_result = np.load(INPUT_PATHS["u_bar"])
        u_transform = twiss.courant_snyder_transform(u_vector, alpha_beta[0], alpha_beta[1])
        np.testing.assert_array_almost_equal(u_transform, u_bar_result)


@pytest.fixture()
def _fake_coordinates() -> np.ndarray:
    return np.random.random(size=10_000) / 1e4
