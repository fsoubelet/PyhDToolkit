"""
.. _utils-jit:

JIT Compilation
---------------

Provides a useful decorator to potentially JIT
compile functions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


def maybe_jit(func: Callable, **kwargs) -> Callable:
    """
    .. versionadded:: 1.7.0

    A `numba.jit` decorator that does nothing if
    `numba` is not installed.

    Parameters
    ----------
    func : Callable
        The function to be decorated.
    **kwargs
        Additional keyword arguments are passed to
        the `numba.jit` decorator.

    Returns
    -------
    Callable
        The JIT-decorated function if `numba` is
        installed, the original function otherwise.
    """
    try:
        from numba import jit

        return jit(func, **kwargs)
    except ImportError:
        return func
