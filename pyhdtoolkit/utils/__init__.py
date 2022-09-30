import functools
import inspect
import traceback
import warnings

from typing import Callable

from . import cmdline, contexts, defaults, executors, htc_monitor, operations, printutil

__all__ = [cmdline, contexts, defaults, executors, htc_monitor, operations, printutil]

# ----- Utility deprecation decorator ----- #


def deprecated(message: str = "") -> Callable:
    """
    Decorator to mark some functions in this module as deprecated, as they will be moved to a new `coupling` module.
    It will result in an informative `DeprecationWarning` being issued with the provided message when the function
    is used for the first time.
    """

    def decorator_wrapper(func):
        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            current_call_source = "|".join(traceback.format_stack(inspect.currentframe()))
            if current_call_source not in function_wrapper.last_call_source:
                warnings.warn(
                    f"Function {func.__name__} is now deprecated and will be removed in a future release! {message}",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                function_wrapper.last_call_source.add(current_call_source)

            return func(*args, **kwargs)

        function_wrapper.last_call_source = set()

        return function_wrapper

    return decorator_wrapper
