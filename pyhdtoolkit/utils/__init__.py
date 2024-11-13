from __future__ import annotations

import functools
import inspect
import traceback
import warnings

from typing import TYPE_CHECKING

from . import cmdline, contexts, htc_monitor, logging  # noqa: TID252

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["cmdline", "contexts", "htc_monitor", "logging"]

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
