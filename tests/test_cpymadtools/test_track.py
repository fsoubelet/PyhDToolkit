import pytest
from pandas import DataFrame

from pyhdtoolkit.cpymadtools.track import track_single_particle


@pytest.mark.parametrize("obs_points", [[], ["qf", "mb", "msf"]])
def test_single_particle_tracking(_matched_base_lattice, obs_points):
    madx = _matched_base_lattice
    tracks_dict = track_single_particle(
        madx,
        sequence="CAS3",
        nturns=100,
        initial_coordinates=(1e-4, 0, 2e-4, 0, 0, 0),
        observation_points=obs_points,
    )

    assert isinstance(tracks_dict, dict)
    assert len(tracks_dict.keys()) == len(obs_points) + 1
    for tracks in tracks_dict.values():
        assert isinstance(tracks, DataFrame)
        assert all(coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e"))


def test_single_particle_tracking_with_onepass(_matched_base_lattice):
    madx = _matched_base_lattice
    tracks_dict = track_single_particle(
        madx, sequence="CAS3", nturns=100, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0), ONETABLE=True
    )

    assert isinstance(tracks_dict, dict)
    assert len(tracks_dict.keys()) == 1  # should be only one because of ONETABLE option
    assert "trackone" in tracks_dict
    tracks = tracks_dict["trackone"]
    assert isinstance(tracks, DataFrame)
    assert all(coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e"))
