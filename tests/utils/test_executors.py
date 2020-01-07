import pytest

from pyhdtoolkit.utils.executors import MultiProcessor, MultiThreader


def test_multiprocessing():
    result = MultiProcessor.execute_function(func=_square, func_args=list(range(6)), n_processes=6)
    assert result == [0, 1, 4, 9, 16, 25]


def test_multiprocessing_zero_processes_fails():
    with pytest.raises(ValueError):
        result = MultiProcessor.execute_function(func=_square, func_args=list(range(6)), n_processes=0)


def test_multithreading():
    result = MultiThreader.execute_function(func=_square, func_args=list(range(12)), n_threads=12)
    assert result == [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]


def test_multithreading_zero_processes_fails():
    with pytest.raises(ValueError):
        result = MultiThreader.execute_function(func=_square, func_args=list(range(6)), n_threads=0)


def _square(x):
    return x ** 2
