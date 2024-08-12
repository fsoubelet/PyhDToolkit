import math

from pyhdtoolkit.models.beam import BeamParameters


def test_beam_parameters():
    beam = BeamParameters(
        charge=1, pc_GeV=1.9, E_0_GeV=0.9382720813, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3, verbose=True
    )
    assert math.isclose(beam.B_rho_Tm, 6.333333333333333)
    assert math.isclose(beam.E_tot_GeV, 2.1190456574946737)
    assert math.isclose(beam.E_kin_GeV, 1.1807735761946736)
    assert math.isclose(beam.gamma_r, 2.258455409393277)
    assert math.isclose(beam.beta_r, 0.8966300434726596)
    assert math.isclose(beam.eg_x_m, 2.469137056052632e-06)
    assert math.isclose(beam.eg_y_m, 2.469137056052632e-06)
    beam.__str__()
    beam.__repr__()
