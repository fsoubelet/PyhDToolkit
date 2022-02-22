"""
.. _utils-contexts:

Context Utilities
-----------------

Provides useful contexts to use functions in.
"""
import time

from contextlib import contextmanager
from typing import Callable, Iterator


@contextmanager
def timeit(function: Callable) -> Iterator[None]:
    """
    Returns the time elapsed when executing code in the context via *function*.
    Original code from is from :user:`Jaime Coello de Portugal <jaimecp89>`.

    Args:
        function (Callable): any callable taking one argument. This was conceived
            with a `lambda` in mind.

    Returns:
        The elapsed time as an argument for the provided function.

    Example:
        .. code-block:: python

            >>> with timeit(lambda spanned: logger.debug(f"Did some stuff in {spanned} seconds")):
            ...     some_stuff()
            ...     some_other_stuff()
    """
    start_time = time.time()
    try:
        yield
    finally:
        time_used = time.time() - start_time
        function(time_used)
