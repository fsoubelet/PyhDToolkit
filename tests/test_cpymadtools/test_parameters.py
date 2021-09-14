from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.parameters import query_beam_attributes
from pyhdtoolkit.models.madx import MADXBeam


class TestParameters:
    def test_query_default_madx_beam(self):
        madx = Madx(stdout=False)
        beam = query_beam_attributes(madx)

        assert isinstance(beam, MADXBeam)
        for attribute in beam.dict():
            assert getattr(beam, attribute) == madx.beam[attribute]

    def test_query_lhc_madx_beam(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        beam = query_beam_attributes(madx)

        assert isinstance(beam, MADXBeam)
        for attribute in beam.dict():
            assert getattr(beam, attribute) == madx.beam[attribute]
