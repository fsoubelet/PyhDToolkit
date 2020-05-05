"""
Module contexts
----------------------

Provides contexts to use functions in.
"""
import time
import warnings

from contextlib import contextmanager

from loguru import logger


@contextmanager
def timeit(function: callable) -> None:
    """
    Returns the time elapsed when executing code in the context via `function`.
    Original code from @jaimecp89

    Args:
        function: any callable taking one argument. Was conceived with a lambda in mind.

    Returns:
        The elapsed time as an argument for the provided function.

    Usage:
        with timeit(lambda spanned: logger.debug(f'Did some stuff in {spanned} seconds')):
            some_stuff()
            some_other_stuff()
    """
    start_time = time.time()
    try:
        yield
    finally:
        time_used = time.time() - start_time
        function(time_used)


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
