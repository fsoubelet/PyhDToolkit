import math

import pytest

from pyhdtoolkit.utils.operations import MiscellaneousOperations


def test_longest_item():
    assert MiscellaneousOperations.longest_item(list(range(5)), list(range(100)), list(range(50))) == list(range(100))


def test_longest_item_empty_inputs():
    assert MiscellaneousOperations.longest_item([], []) == []


def test_longest_item_none_input():
    with pytest.raises(TypeError):
        MiscellaneousOperations.longest_item(list(range(5)), None)


def test_longest_item_with_strings():
    assert (
        MiscellaneousOperations.longest_item(
            "A first string", "A second string", "One much longer than the two previous strings"
        )
        == "One much longer than the two previous strings"
    )


def test_map_values_to_bool():
    assert MiscellaneousOperations.map_values({"a": 0, "b": 1, "c": 2, "d": 3}, lambda x: x % 2 == 0) == {
        "a": True,
        "b": False,
        "c": True,
        "d": False,
    }


def test_map_values_to_length():
    assert MiscellaneousOperations.map_values(
        {"a": list(range(5)), "b": list(range(10)), "c": list(range(15))}, lambda x: len(x)
    ) == {"a": 5, "b": 10, "c": 15}


def test_map_values_to_values():
    assert MiscellaneousOperations.map_values({"a": 0.5, "b": 0.9, "c": 1.2, "d": 2.1, "e": 25}, math.floor) == {
        "a": 0,
        "b": 0,
        "c": 1,
        "d": 2,
        "e": 25,
    }
