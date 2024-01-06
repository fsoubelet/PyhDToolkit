from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.parameters import query_beam_attributes
from pyhdtoolkit.models.madx import MADXBeam


def test_query_default_madx_beam():
    madx = Madx(stdout=False)
    beam = query_beam_attributes(madx)

    assert isinstance(beam, MADXBeam)
    for attribute in beam.model_dump():
        assert getattr(beam, attribute) == madx.beam[attribute]


def test_query_lhc_madx_beam(_non_matched_lhc_madx):
    madx = _non_matched_lhc_madx
    beam = query_beam_attributes(madx)

    assert isinstance(beam, MADXBeam)
    for attribute in beam.model_dump():
        assert getattr(beam, attribute) == madx.beam[attribute]
