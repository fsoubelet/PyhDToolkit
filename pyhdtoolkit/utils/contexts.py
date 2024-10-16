"""
.. _utils-contexts:

Context Utilities
-----------------

Provides useful contexts to use functions in.
"""

import time

from collections.abc import Callable, Iterator
from contextlib import contextmanager


@contextmanager
def timeit(function: Callable) -> Iterator[None]:
    """
    .. versionadded:: 0.4.0

    Returns the time elapsed when executing code in the context via *function*.
    Original code from is from :user:`Jaime Coello de Portugal <jaimecp89>`.

    Args:
        function (Callable): any callable taking one argument. This was conceived
            with a `lambda` in mind.

    Returns:
        The elapsed time as an argument for the provided function.

    Example:
        .. code-block:: python

            with timeit(lambda x: logger.debug(f"Did some stuff in {x} seconds")):
                some_stuff()
                some_other_stuff()
    """
    start_time = time.time()
    try:
        yield
    finally:
        time_used = time.time() - start_time
        function(time_used)
