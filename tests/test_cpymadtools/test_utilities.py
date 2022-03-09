import pytest

from pyhdtoolkit.cpymadtools.utils import _get_k_strings


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
