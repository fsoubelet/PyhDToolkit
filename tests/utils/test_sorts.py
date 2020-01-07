import pytest

from pyhdtoolkit.utils.sorts import quick_sort


def test_quicksort():
    assert quick_sort([0, 5, 3, 2, 2]) == [0, 2, 2, 3, 5]


def test_quicksort_empty_input():
    assert quick_sort([]) == []


def test_quicksort_negatives():
    assert quick_sort([-2, -5, -45]) == [-45, -5, -2]
