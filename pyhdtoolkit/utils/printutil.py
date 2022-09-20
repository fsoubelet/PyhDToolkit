"""
.. _utils-printutils:

Printing Utilities
------------------

A class utility class to allow me printing text in color, bold, etc.

.. warning::
   This module's functionality is superseeded by the ``rich`` package, and it will be 
   removed in a future release.
"""

END = "\033[0m"


class Background:
    """
    .. versionadded:: 0.2.0

    ANSI color escape sequences for the background of a terminal output.
    """

    black = "\033[40m"
    blue = "\033[44m"
    cyan = "\033[46m"
    green = "\033[42m"
    grey = "\033[47m"
    magenta = "\033[45m"
    red = "\033[41m"
    yellow = "\033[43m"


class Foreground:
    """
    .. versionadded:: 0.2.0

    ANSI color escape sequences for the foreground of a terminal output.
    """

    blue = "\033[94m"
    cyan = "\033[96m"
    dark_blue = "\033[34m"
    dark_cyan = "\033[36m"
    dark_green = "\033[32m"
    dark_grey = "\033[90m"
    dark_red = "\033[31m"
    dark_yellow = "\033[33m"
    green = "\033[92m"
    grey = "\033[37m"
    magenta = "\033[35m"
    pink = "\033[95m"
    red = "\033[91m"
    yellow = "\033[93m"
    white = "\033[30m"


class Styles:
    """
    .. versionadded:: 0.2.0

    ANSI style escape sequences for a terminal output.
    """

    all_off = "\033[0m"
    bold = "\033[1m"
    concealed = "\033[7m"
    disable = "\033[02m"
    reverse = "\033[7m"
    strikethrough = "\033[09m"
    underscore = "\033[4m"
