"""
.. _utils-logging:


Logging Utilities
-----------------

.. versionadded:: 1.0.0

The `loguru` package is used for logging throughout `pyhdtoolkit`,
and this module provides utilities to easily set up a logger
configuration. Different pre-defined formats are provided to choose
from:

- ``FORMAT1``: will display the full time of the log message, its level, the calling line and the message itself. This is the default format.
- ``FORMAT2``: similar to ``FORMAT1``, but the caller information is displayed at the end of the log line.
- ``SIMPLE_FORMAT``: minimal, displays the local time, the level and the message.
"""

import sys

from loguru import logger

FORMAT1 = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

FORMAT2 = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan>"
)

SIMPLE_FORMAT = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"


def config_logger(level: str | int = "INFO", fmt: str = FORMAT1, **kwargs) -> None:
    """
    .. versionadded:: 0.8.2

    Resets the logger object from `loguru`, with `sys.stdout`
    as a sink and the provided *format*.

    Parameters
    ----------
    level : str | int
        The logging level to set. Case insensitive if a string
        is given. Valuevalue can be any of the `loguru levels
        <https://loguru.readthedocs.io/en/stable/api/logger.html#levels>`_
        or their integer values equivalents. Defaults to ``INFO``.
    fmt : str
        The format to use for the logger to display messages.
        Defaults to a pre-defined format in this module.
    **kwargs
        Any keyword argument is transmitted to the
        `~loguru._logger.Logger.add` call.


    Examples
    --------

        Using the defaults and setting the logging level:

        .. code-block:: python

            config_logger(level="DEBUG")

        Specifying a custom format and setting the logging level:

        .. code-block:: python

            from pyhdtoolkit.utils.logging import config_logger, SIMPLE_FORMAT

            config_logger(level="DEBUG", format=SIMPLE_FORMAT)
    """
    logger.remove()
    level = level.upper() if isinstance(level, str) else level
    logger.add(sys.stdout, level=level, format=fmt, **kwargs)
