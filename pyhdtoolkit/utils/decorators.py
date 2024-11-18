"""
.. _utils-decorators:

Decorator Utilities
-------------------

Provides useful decorators.
"""
from __future__ import annotations
import functools
import inspect
import traceback
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


# ----- Utility deprecation decorator ----- #


def deprecated(message: str = "") -> Callable:
    """
    Decorator to mark a function as deprecated. It will result in an
    informative `DeprecationWarning` being issued with the provided
    message when the function is used for the first time.

    Parameters
    ----------
    message : str, optional
        Extra information to be displayed after the deprecation
        notice, when the function is used. Defaults to an empty
        string (no extra information).
    
    Returns
    -------
    Callable
        The decorated function.
    
    Example
    -------
        .. code-block:: python

            @deprecated("Use 'new_alternative' instead.")
            def old_function():
                return "I am old!"
    """

    def decorator_wrapper(func):
        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            current_call_source = "|".join(traceback.format_stack(inspect.currentframe()))
            if current_call_source not in function_wrapper.last_call_source:
                warnings.warn(
                    f"Function {func.__name__} is now deprecated and will be removed in a future release! "
                    f"{message}",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                function_wrapper.last_call_source.add(current_call_source)

            return func(*args, **kwargs)

        function_wrapper.last_call_source = set()

        return function_wrapper

    return decorator_wrapper


# ----- Utility JIT Compilation decorator ----- #

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

    Example
    -------
        .. code-block:: python

            @maybe_jit
            def calculations(x, y):
                return (x + y) / (x - y)
    """
    try:
        from numba import jit

        return jit(func, **kwargs)
    except ImportError:
        return func
