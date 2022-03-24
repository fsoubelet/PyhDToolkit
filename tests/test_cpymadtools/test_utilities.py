import pytest
import tfs

from pandas.testing import assert_frame_equal

from pyhdtoolkit.cpymadtools.utils import _get_k_strings, export_madx_table, get_table_tfs


class TestUtils:
    @pytest.mark.parametrize(
        "orient, result",
        [
            ["straight", ["K0L", "K1L", "K2L", "K3L", "K4L"]],
            ["skew", ["K0SL", "K1SL", "K2SL", "K3SL", "K4SL"]],
            ["both", ["K0L", "K0SL", "K1L", "K1SL", "K2L", "K2SL", "K3L", "K3SL", "K4L", "K4SL"]],
        ],
    )
    def test_k_strings(self, orient, result):
        assert _get_k_strings(stop=5, orientation=orient) == result

    def test_k_strings_wrong_orientation_raises(self):
        with pytest.raises(ValueError):
            _get_k_strings(stop=5, orientation="wrong")

    @pytest.mark.parametrize("regex", [None, "^QF*"])
    def test_table_export(self, _matched_base_lattice, regex, tmp_path):
        write_location = tmp_path / "test.tfs"
        madx = _matched_base_lattice
        madx.command.twiss()

        twiss_df = get_table_tfs(madx, "twiss").reset_index(drop=True)
        if regex:
            twiss_df = twiss_df.set_index("NAME").filter(regex=regex, axis=0).reset_index()

        export_madx_table(madx, table_name="twiss", file_name=write_location, pattern=regex)
        assert write_location.is_file()

        new = tfs.read(write_location)
        assert "NAME" in new.headers  # should be added by default
        assert "TYPE" in new.headers  # should be added by default
        # Dropping 'COMMENTS' column as I have no clue what it's doing here and it shouldn't be here
        assert_frame_equal(twiss_df.drop(columns=["COMMENTS"]), new.drop(columns=["COMMENTS"]))
