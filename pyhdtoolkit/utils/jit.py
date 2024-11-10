from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


def maybe_jit(func: Callable, **kwargs) -> Callable:
    """
    .. versionadded:: 0.17.0

    A `numba.jit` decorator that does nothing if `numba` is not installed.

    Args:
        func (Callable): The function to be decorated.
        **kwargs: Additional keyword arguments are passed to `numba.jit`.

    Returns:
        Callable: The JIT-decorated function if `numba` is installed,
            and the original function otherwise.
    """
    try:
        from numba import jit

        return jit(func, **kwargs)
    except ImportError:
        return func
