import math

import pytest

from pyhdtoolkit.utils.operations import NumberOperations


def test_clamp_number_out_of_range():
    assert NumberOperations.clamp_number(17, 4, 5) == 5


def test_clamp_number_in_range():
    assert NumberOperations.clamp_number(15, 10, 20) == 15


def test_degrees_to_radians_no_decompose():
    assert NumberOperations.degrees_to_radians(160) == 2.792526803190927


def test_degrees_to_radians_decompose():
    assert NumberOperations.degrees_to_radians(360, decompose=True) == (2, "pi", "rad")


def test_greatest_common_divisor_two_elements():
    assert NumberOperations.greatest_common_divisor([54, 24]) == 6


def test_greatest_common_divisor_many_elements():
    assert NumberOperations.greatest_common_divisor([30, 132, 378, 582, 738]) == 6


def test_is_divisible_by_true():
    assert NumberOperations.is_divisible_by(25, 5) is True


def test_is_divisible_by_false():
    assert NumberOperations.is_divisible_by(73.4, 2.1) is False


def test_is_divisible_by_error():
    with pytest.raises(ZeroDivisionError):
        NumberOperations.is_divisible_by(50, 0)


def test_least_common_multiple_two_elements():
    assert NumberOperations.least_common_multiple(4, 5) == 20


def test_least_common_multiple_many_elements():
    assert NumberOperations.least_common_multiple(2, 5, 17, 632) == 53720


def test_radians_to_degrees_round():
    assert NumberOperations.radians_to_degrees(2 * math.pi) == 360


def test_radians_to_degrees_not_round():
    assert NumberOperations.radians_to_degrees(2.710) == 155.2715624804531
