import math

import pytest

from pyhdtoolkit.utils.operations import ListOperations


def test_all_unique_true():
    assert ListOperations.all_unique([1, 2, 3, 5, 12, 0]) is True


def test_all_unique_false():
    assert ListOperations.all_unique([1, 1, 1]) is False


def test_all_unique_empty_input():
    assert ListOperations.all_unique([]) is True


def test_all_unique_no_input():
    with pytest.raises(TypeError):
        ListOperations.all_unique(None)


def test_average_by():
    assert ListOperations.average_by([{"n": 4}, {"n": 2}, {"n": 8}, {"n": 6}], lambda x: x["n"]) == 5


def test_average_by_no_input():
    with pytest.raises(TypeError):
        assert ListOperations.average_by(None)


def test_bifurcate():
    assert ListOperations.bifurcate(["beep", "boop", "foo", "bar"], [True, True, False, True]) == [
        ["beep", "boop", "bar"],
        ["foo"],
    ]


def test_bifurcate_no_filters():
    with pytest.raises(TypeError):
        ListOperations.bifurcate(["beep", "boop", "foo", "bar"], None)


def test_bifurcate_empty_filters():
    with pytest.raises(IndexError):
        ListOperations.bifurcate(["beep", "boop", "foo", "bar"], [])


def test_bifurcate_by_no_matching_lentghs_inputs():
    with pytest.raises(IndexError):
        ListOperations.bifurcate(["beep", "boop", "foo", "bar"], [True, False, False])


def test_bifurcate_by():
    assert ListOperations.bifurcate_by(list(range(5)), lambda x: x % 2 == 0) == [[0, 2, 4], [1, 3]]


def test_bifurcate_by_empty_input():
    assert ListOperations.bifurcate_by([], lambda x: x % 2 == 0) == [[], []]


def test_chunk_list():
    assert ListOperations.chunk_list(list(range(10)), 3) == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_chunk_list_in_zero_size_elements():
    with pytest.raises(ZeroDivisionError):
        ListOperations.chunk_list(list(range(10)), 0)


def test_chunk_list_by_bigger_size():
    assert ListOperations.chunk_list(list(range(10)), 20) == list(range(10))


def test_deep_flatten():
    assert ListOperations.deep_flatten([["a", "b", "c"], [1, 2, 3], [True, False, False]]) == [
        "a",
        "b",
        "c",
        1,
        2,
        3,
        True,
        False,
        False,
    ]


def test_deep_flatten_with_empty_element():
    assert ListOperations.deep_flatten([["a", "b", "c"], [1, 2, 3], [], [True, False, False]]) == [
        "a",
        "b",
        "c",
        1,
        2,
        3,
        True,
        False,
        False,
    ]


def test_deep_flatten_with_none_element():
    assert ListOperations.deep_flatten([["a", "b", "c"], [1, 2, 3], None, [True, False, False]]) == [
        "a",
        "b",
        "c",
        1,
        2,
        3,
        None,
        True,
        False,
        False,
    ]


def test_eval_none_true():
    assert ListOperations.eval_none([0, 0, 1, 0], lambda x: x >= 2) is True


def test_eval_none_false():
    assert ListOperations.eval_none([0, 1, 2, 0], lambda x: x >= 2) is False


def test_eval_some_true():
    assert ListOperations.eval_some([0, 1, 2, 0], lambda x: x >= 2) is True


def test_eval_some_false():
    assert ListOperations.eval_some([0, 0, 1, 0], lambda x: x >= 2) is False


def test_get_indices():
    assert ListOperations.get_indices(0, [0, 1, 3, 5, 7, 3, 9, 0, 0, 5, 3, 2]) == [0, 7, 8]


def test_get_indices_from_tuple():
    assert ListOperations.get_indices(0, (0, 1, 3, 5, 7, 3, 9, 0, 0, 5, 3, 2)) == [0, 7, 8]


def test_groupby():
    assert ListOperations.group_by(list(range(5)), lambda x: x % 2 == 0) == {True: [0, 2, 4], False: [1, 3]}


def test_has_duplicates_true():
    assert ListOperations.has_duplicates([1, 2, 1]) is True


def test_has_duplicates_false():
    assert ListOperations.has_duplicates([1, 2, 3]) is False


def test_sample():
    assert ListOperations.sample(["a", "b", 1, 2, False]) in ["a", "b", 1, 2, False]


def test_sanitize():
    assert ListOperations.sanitize_list([1, False, "a", 2, "", None, 6, 0]) == [1, "a", 2, 6]


def test_sanitize_to_empty():
    assert ListOperations.sanitize_list([0, "", None, False]) == []


def test_shuffle_list():
    initial_list = [1, 2, "a", "b", False, True]
    shuffled = ListOperations.shuffle(initial_list)
    assert shuffled != initial_list and set(shuffled) == set(initial_list)


def test_spread():
    assert ListOperations.spread([list(range(5)), list(range(5))]) == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]


def test_symmetric_difference_by_value_result():
    assert ListOperations.symmetric_difference_by([2.1, 1.2], [2.3, 3.4], math.floor) == [1.2, 3.4]


def test_symmetric_difference_by_bollean_result():
    assert ListOperations.symmetric_difference_by([2.1, 1.2], [0.5, 1.2], lambda x: x >= 2) == [2.1]


def test_union_by():
    assert ListOperations.union_by([2.1], [1.2, 2.3], math.floor) == [1.2, 2.1]


def test_union_by_with_strings():
    assert ListOperations.union_by(["A", "B"], ["a", "c"], str.lower) == ["A", "B", "c"]


def test_zipper():
    assert ListOperations.zipper([1, 2, 3], [2, 5, 3, 7], ["a", "b", "c"]) == [
        [1, 2, "a"],
        [2, 5, "b"],
        [3, 3, "c"],
        [None, 7, None],
    ]


def test_zipper_with_fillvalue():
    assert ListOperations.zipper([1, 2, 3], [2, 5, 3, 7], ["a", "b", "c"], fillvalue=5) == [
        [1, 2, "a"],
        [2, 5, "b"],
        [3, 3, "c"],
        [5, 7, 5],
    ]
