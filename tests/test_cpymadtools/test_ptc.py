import pathlib

import pytest
import tfs

from cpymad.madx import Madx
from pandas import DataFrame
from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.cpymadtools.matching import match_tunes_and_chromaticities
from pyhdtoolkit.cpymadtools.ptc import get_amplitude_detuning, get_rdts, ptc_track_particle, ptc_twiss

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"

BASE_LATTICE = LatticeGenerator.generate_base_cas_lattice()


class TestPTC:
    def test_amplitude_detuning_fails_on_high_order(self, caplog):
        madx = Madx(stdout=False)

        with pytest.raises(NotImplementedError):
            _ = get_amplitude_detuning(madx, order=5)

        for record in caplog.records:
            assert record.levelname == "ERROR"

    def test_amplitude_detuning(self, tmp_path, _ampdet_tfs_path, _matched_base_lattice):
        madx = _matched_base_lattice

        reference_df = tfs.read(_ampdet_tfs_path)
        ampdet_df = get_amplitude_detuning(madx, file=tmp_path / "here.tfs")

        assert (tmp_path / "here.tfs").is_file()
        assert_frame_equal(reference_df, ampdet_df)

    def test_rdts(self, tmp_path, _rdts_tfs_path):
        madx = Madx(stdout=False)
        madx.input(BASE_LATTICE)
        match_tunes_and_chromaticities(
            madx, None, "CAS3", 6.335, 6.29, 100, 100, varied_knobs=["kqf", "kqd", "ksf", "ksd"]
        )

        reference_df = tfs.read(_rdts_tfs_path)
        rdts_df = get_rdts(madx, file=tmp_path / "here.tfs")

        assert (tmp_path / "here.tfs").is_file()
        assert_frame_equal(reference_df.set_index("NAME"), rdts_df.set_index("NAME"))

    def test_ptc_twiss(self, tmp_path, _matched_base_lattice, _ptc_twiss_tfs_path):
        madx = _matched_base_lattice
        ptc_twiss_df = ptc_twiss(madx, file=tmp_path / "here.tfs").reset_index(drop=True)
        reference_df = tfs.read(_ptc_twiss_tfs_path)

        assert (tmp_path / "here.tfs").is_file()
        assert_frame_equal(reference_df.drop(columns=["COMMENTS"]), ptc_twiss_df.drop(columns=["COMMENTS"]))

    @pytest.mark.parametrize("obs_points", [[], ["qf", "mb", "msf"]])
    def test_single_particle_ptc_track(self, _matched_base_lattice, obs_points):
        madx = _matched_base_lattice
        tracks_dict = ptc_track_particle(
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
            assert all([coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")])

    def test_single_particle_ptc_track_with_onepass(self, _matched_base_lattice):
        madx = _matched_base_lattice
        tracks_dict = ptc_track_particle(
            madx, sequence="CAS3", nturns=100, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0), onetable=True
        )

        assert isinstance(tracks_dict, dict)
        assert len(tracks_dict.keys()) == 1  # should be only one because of ONETABLE option
        assert "trackone" in tracks_dict.keys()
        tracks = tracks_dict["trackone"]
        assert isinstance(tracks, DataFrame)
        assert all([coordinate in tracks.columns for coordinate in ("x", "px", "y", "py", "t", "pt", "s", "e")])


# ----- Fixtures ----- #


@pytest.fixture()
def _ampdet_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "ampdet.tfs"


@pytest.fixture()
def _rdts_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "rdts.tfs"


@pytest.fixture()
def _ptc_twiss_tfs_path() -> pathlib.Path:
    return INPUTS_DIR / "ptc_twiss.tfs"
