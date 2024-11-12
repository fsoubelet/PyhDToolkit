import math

from pyhdtoolkit.models.beam import BeamParameters


def test_beam_parameters():
    beam = BeamParameters(
        charge=1,
        pc_GeV=1.9,
        E_0_GeV=0.9382720813,
        nemitt_x=5e-6,
        nemitt_y=5e-6,
        deltap_p=2e-3,
        verbose=True,
    )
    assert math.isclose(beam.B_rho_Tm, 6.333333333333333)
    assert math.isclose(beam.E_tot_GeV, 2.1190456574946737)
    assert math.isclose(beam.E_kin_GeV, 1.1807735761946736)
    assert math.isclose(beam.gamma_rel, 2.258455409393277)
    assert math.isclose(beam.beta_rel, 0.8966300434726596)
    assert math.isclose(beam.nemitt_x, 5e-06)
    assert math.isclose(beam.gemitt_y, 1.9850514642517005e-06)
    beam.__str__()
    beam.__repr__()
