"""
.. _utils-logging:


Logging Utilities
-----------------

The `loguru` package is used for logging throughout `pyhdtoolkit`, and below are utilities to easily set up a good logger configuration.
"""
import sys

from typing import Union

from loguru import logger

LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def config_logger(level: Union[str, int] = "INFO", **kwargs) -> None:
    """
    .. versionadded:: 1.0.0

    Resets the logger object from `loguru`, with `sys.stdout` as a sink and the
    aforedefined format, which comes down to personnal preference.

    Args:
        level (Union[str, int]): The logging level to set. Case-insensitive if a
            string is given. Defaults to ``INFO``.
        **kwargs: any keyword argument is transmitted to the ``logger.add`` call.

    Example:
        .. code-block:: python

            >>> config_logger(level="DEBUG")
    """
    logger.remove()
    level = level.upper() if isinstance(level, str) else level
    logger.add(sys.stdout, format=LOGURU_FORMAT, level=level, **kwargs)
