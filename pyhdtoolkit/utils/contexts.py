"""
.. _utils-contexts:

Context Utilities
-----------------

Provides useful contexts to use functions in.
"""

from __future__ import annotations

import time

from contextlib import contextmanager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import NoneType

@contextmanager
def timeit(function: Callable) -> NoneType: # type: ignore
    """
    .. versionadded:: 0.4.0

    Returns the time elapsed when executing code in the context
    via *function*. Original code from is from :user:`Jaime Coello
    de Portugal <jaimecp89>`.

    Parameters
    ----------
    function : Callable
        Function to be executed with the elapsed time as argument,
        this was conceived with a `lambda` in mind. See the example
        below.

    Returns
    -------
    Iterator[None]
        The elapsed time as an argument for the provided function.

    Example
    -------
        .. code-block:: python

            with timeit(lambda x: logger.debug(f"Took {x} seconds")):
                some_stuff()
                some_other_stuff()
    """
    start_time = time.time()
    try:
        yield
    finally:
        time_used = time.time() - start_time
        function(time_used)
