import pathlib

import numpy as np
import pytest

from pyhdtoolkit.models.beam import BeamParameters
from pyhdtoolkit.optics import ripken, twiss
from pyhdtoolkit.optics.beam import Beam, compute_beam_parameters
from pyhdtoolkit.optics.rdt import determine_rdt_line, rdt_to_order_and_type

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
INPUT_PATHS = {
    "alpha_beta": INPUTS_DIR / "optics" / "alpha_beta.npy",
    "u_vector": INPUTS_DIR / "optics" / "u_vector.npy",
    "u_bar": INPUTS_DIR / "optics" / "u_bar.npy",
    "beta11": INPUTS_DIR / "optics" / "beta11.npy",
    "beta21": INPUTS_DIR / "optics" / "beta21.npy",
    "lebedev": INPUTS_DIR / "optics" / "lebedev_size.npy",
}


def test_gamma_rel():
    assert Beam(6500, 2.5e-6).gamma_rel == 6928.628011131436


def test_beta_rel():
    assert Beam(6500, 2.5e-6).beta_rel == 1.0000000104153894


def test_brho():
    assert Beam(6500, 2.5e-6).brho == 7.227222137900961e-05


def test_normalized_emittance():
    assert Beam(6500, 2.5e-6).normalized_emittance == 0.01732157020823949


def test_rms_emittance():
    assert Beam(6500, 2.5e-6).rms_emittance == 3.6082179183888383e-10


def test_lhc_revolution_frequency():
    lhc_beam = Beam(6500, 2.5e-6)
    assert lhc_beam.revolution_frequency() == 11245.499628523643


@pytest.mark.parametrize(
    ("alpha_p", "result"),
    [(0, 2.083077890845299e-08), (1e-5, -9.979169221091548e-06), (-500, 500.0000000208308)],
)
def test_eta(alpha_p, result):
    assert Beam(6500, 2.5e-6).eta(alpha_p) == result


@pytest.mark.parametrize(("alpha_p", "result"), [(1e-5, 316.2277660168379), (500, 0.044721359549995794)])
def test_gamma_transition(alpha_p, result):
    assert Beam(6500, 2.5e-6).gamma_transition(alpha_p) == result


def test_gamma_transition_raises():
    with pytest.raises(ZeroDivisionError):
        Beam(6500, 2.5e-6).gamma_transition(0)


@pytest.mark.parametrize(
    ("pc_gev", "en_x_m", "en_y_m", "delta_p", "result"),
    [
        (
            1.9,
            5e-6,
            5e-6,
            2e-3,
            BeamParameters(
                pc_GeV=1.9,
                B_rho_Tm=6.3376399999999995,
                E_0_GeV=0.9382720813,
                E_tot_GeV=2.1190456574946737,
                E_kin_GeV=1.1807735761946736,
                gamma_r=2.258455409393277,
                beta_r=0.8966300434726596,
                en_x_m=5e-06,
                en_y_m=5e-06,
                eg_x_m=2.469137056052632e-06,
                eg_y_m=2.469137056052632e-06,
                deltap_p=0.002,
            ),
        ),
        (
            19,
            5e-6,
            5e-6,
            2e-4,
            BeamParameters(
                pc_GeV=19,
                B_rho_Tm=63.3764,
                E_0_GeV=0.9382720813,
                E_tot_GeV=19.023153116624673,
                E_kin_GeV=18.084881035324674,
                gamma_r=20.274666054506927,
                beta_r=0.9987828980567665,
                en_x_m=5e-06,
                en_y_m=5e-06,
                eg_x_m=2.4691370560526314e-07,
                eg_y_m=2.4691370560526314e-07,
                deltap_p=0.0002,
            ),
        ),
    ],
)
def test_beam_parameters(pc_gev, en_x_m, en_y_m, delta_p, result):
    assert compute_beam_parameters(pc_gev, en_x_m, en_y_m, delta_p) == result


def test_beam_size(_fake_coordinates):
    assert np.allclose(ripken._beam_size(_fake_coordinates), _fake_coordinates.std())  # noqa: SLF001
    assert np.allclose(
        ripken._beam_size(_fake_coordinates, method="rms"),  # noqa: SLF001
        np.sqrt(np.mean(np.square(_fake_coordinates))),
    )


def test_beam_size_raises(_fake_coordinates):
    with pytest.raises(NotImplementedError):
        _ = ripken._beam_size(_fake_coordinates, method="not_real")  # noqa: SLF001


@pytest.mark.parametrize("beta11", [0.3312])
@pytest.mark.parametrize("beta21", [1])
@pytest.mark.parametrize("emit_x", [5e-6, 2.75e-6, 3.5e-6])
@pytest.mark.parametrize("emit_y", [5e-6, 2.75e-6, 3.5e-6])
def test_lebedev_size_floats(beta11, beta21, emit_x, emit_y):
    assert ripken.lebedev_beam_size(beta1_=beta11, beta2_=beta21, geom_emit_x=emit_x, geom_emit_y=emit_y) == np.sqrt(
        emit_x * beta11 + emit_y * beta21
    )


def test_courant_snyder_transform():
    alpha_beta = np.load(INPUT_PATHS["alpha_beta"])
    u_vector = np.load(INPUT_PATHS["u_vector"])
    u_bar_result = np.load(INPUT_PATHS["u_bar"])
    u_transform = twiss.courant_snyder_transform(u_vector, alpha_beta[0], alpha_beta[1])
    np.testing.assert_array_almost_equal(u_transform, u_bar_result)


def test_add_beam_size_to_df(_non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    madx.command.twiss(ripken=True)
    df = madx.table.twiss.dframe()
    df["BETA11"] = df.beta11
    df["BETA12"] = df.beta12
    df["BETA21"] = df.beta21
    df["BETA22"] = df.beta22

    df = ripken._add_beam_size_to_df(df, 1e-6, 1e-6)  # noqa: SLF001
    assert "SIZE_X" in df.columns
    assert "SIZE_Y" in df.columns


def test_rdt_order_and_type():
    assert rdt_to_order_and_type(1001) == "skew_quadrupole"
    assert rdt_to_order_and_type(1010) == "skew_quadrupole"
    assert rdt_to_order_and_type(1020) == "normal_sextupole"
    assert rdt_to_order_and_type(2002) == "normal_octupole"
    assert rdt_to_order_and_type(1003) == "skew_octupole"
    assert rdt_to_order_and_type(1004) ==  "normal_decapole"
    assert rdt_to_order_and_type(3003) == "skew_dodecapole"
    assert rdt_to_order_and_type(4004) == "normal_hexadecapole"

    with pytest.raises(KeyError):
        rdt_to_order_and_type(8888)
    with pytest.raises(KeyError):
        rdt_to_order_and_type(1090)


def test_rdt_spectrum_line():
    # Some simple coupling RDTs lines
    assert determine_rdt_line(1001, "X") == (0, 1, 0)
    assert determine_rdt_line(1010, "Y") == (-1, 0, 0)
    assert determine_rdt_line("0220", "X") == (3, -2, 0)

    with pytest.raises(KeyError):
        determine_rdt_line("0220", "Z")



# ----- Fixtures ----- #


@pytest.fixture
def _fake_coordinates() -> np.ndarray:
    return np.random.random(size=10_000) / 1e4
