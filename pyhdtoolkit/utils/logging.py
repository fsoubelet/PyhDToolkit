"""
.. _utils-logging:


Logging Utilities
-----------------

A module with functions to easily setup logging as well as .
A lot of the code in this module has been copied with permission from :user:`Joschua Dilly <joschd>`.
"""
import inspect
import logging
import os
import subprocess
import sys

from collections import defaultdict
from contextlib import contextmanager, suppress
from io import StringIO
from logging import CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING  # make them available directly
from pathlib import Path

DIVIDER = "|"
NEWLINE = "\n" + " " * 10  # levelname + divider + 2
BASIC_FORMAT = "%(levelname)7s {div:s} %(message)s {div:s} %(name)s".format(div=DIVIDER)
COLOR_LEVEL = "\33[0m\33[38;2;150;150;255m"
COLOR_MESSAGE = "\33[0m"
COLOR_MESSAGE_LOW = "\33[0m\33[38;2;140;140;140m"
COLOR_WARN = "\33[0m\33[38;2;255;161;53m"
COLOR_ERROR = "\33[0m\33[38;2;216;31;42m"
COLOR_NAME = "\33[0m\33[38;2;80;80;80m"
COLOR_DIVIDER = "\33[0m\33[38;2;127;127;127m"
COLOR_RESET = "\33[0m"

# Log Levels should be higher than info to be able to filter debug
# messages in the output and not get line duplicates
# LOG_OUT_LVL: int = logging.WARNING - 2
# LOG_CMD_LVL: int = logging.WARNING - 1

COMMAND = DEBUG - 1
MADX = DEBUG - 5

MADXCMD = "madxcmd"
MADXOUT = "madxout"

# ASCII Colors, change to your liking (the last three three-digits are RGB)
# Default colors should be readable on dark and light backgrounds
CPYMAD_COLORS = dict(
    reset="\33[0m",
    name="\33[0m\33[38;2;127;127;127m",
    msg="",
    cmd_name="\33[0m\33[38;2;132;168;91m",
    cmd_msg="",
    out_name="\33[0m\33[38;2;114;147;203m",
    out_msg="\33[0m\33[38;2;127;127;127m",
    warn_name="",
    warn_msg="\33[0m\33[38;2;193;134;22m",
)

# ----- Utilities ----- #


class MaxFilter(logging.Filter):
    """A filter to get messages only up to a certain level"""

    def __init__(self, level: int):
        super(MaxFilter, self).__init__()
        self.__level = level

    def filter(self, log_record: logging.LogRecord) -> bool:
        """
        Determine if the specified record is to be logged.
        Returns `True` if the record should be logged, `False` otherwise.
        This filter does not modify the log record.
        """

        return log_record.levelno <= self.__level


class StreamToLogger:
    """A file-like stream object that redirects writes to a logger instance."""

    def __init__(self, logger: logging.Logger, log_level: int = INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def write(self, buf) -> None:
        last_line_empty = False
        for line in buf.rstrip().splitlines():
            with suppress(AttributeError):
                line = line.decode("utf-8")  # convert madx output from binary
            line = line.rstrip()

            if last_line_empty or len(line):
                self.logger.log(self.log_level, line)
                last_line_empty = False
            else:
                last_line_empty = True  # skips multiple empty lines

    def __call__(self, *args, **kwargs):
        self.write(*args, **kwargs)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()


@contextmanager
def silence_logging():
    """
    Context manager to temporarily remove all handlers from the root logger.
    The logging statements within the context-managed block will not be logged.

    Example:
        .. code-block:: python

            >>> with silence_logging():
            >>>     logger.info("Some message that won't be logged")
    """
    root_logger = logging.getLogger("")
    handlers = list(root_logger.handlers)
    root_logger.handlers = []

    yield

    root_logger.handlers = handlers


def running_in_notebook() -> bool:
    """
    Returns `True` if the code is running in a Jupyter notebook, otherwise `False`.
    This is relevant when setting up loggers as ``stdout`` is slowly printed and
    can potentially freeze a notebook.
    """
    try:
        from IPython import get_ipython

        if "IPKernelApp" not in get_ipython().config:  # pragma: no cover
            return False
    except ImportError:
        return False
    except AttributeError:
        return False
    return True


# ----- The setup functions ----- #


def cpymad_logging_setup(
    command_log: Path = None,
    output_log: Path = None,
    full_log: Path = None,
    colors: bool = True,
    level: int = logging.INFO,
    clear_handlers: bool = True,
):
    """
    Adds stream handlers to the root logger including for `cpymad` output and commands.
    Takes care of file handlers if specified. Used with permission of :user:`@Joschd <joschd>`

    Args:
        command_log (Path): `~pathlib.Path` to file in which to write to write commands sent to
            ``MAD-X``. Defaults to `None`, which deactivates the writing.
        output_log (Path): `~pathlib.Path` to file in which to write ``MAD-X`` output. Defaults
            to `None`, which deactivates the writing.
        full_log (Path): `~pathlib.Path` to file in which to write full logging output. Defaults
            to `None`, which deactivates the writing.
        colors (bool): if set to `True` ascii colors will be used in the logging. Defaults to `True`.
        level (int): the minimum stdout logging level. ``MAD-X``.
        clear_loggers: Clears all handlers of the loggers first.

    Returns:
        A `dict` with StreamToLoggers 'stdout' and 'command_log'.
        Can be used as `Madx(**cpymad_logging_setup())`
    """
    cdict = defaultdict(str)
    if colors:
        cdict.update(CPYMAD_COLORS)

    msg_fmt = logging.Formatter("%(message)s")

    logging.addLevelName(MADX, "MADX")
    logging.addLevelName(COMMAND, "CMD")

    # Setup Root Logger
    root_logger = logging.getLogger("")
    if clear_handlers:
        root_logger.handlers = []  # remove handlers in case someone already created them
    root_logger.setLevel(logging.NOTSET)

    if full_log is not None:
        # Add full logging to file
        fullfile_handler = logging.FileHandler(
            full_log,
            mode="w",
        )
        fullfile_handler.setFormatter(_lvl_fmt())
        root_logger.addHandler(fullfile_handler)

    # Add full logging to stdout
    fullstream_handler = logging.StreamHandler(sys.stdout)
    fullstream_handler.setLevel(level)
    fullstream_handler.addFilter(MaxFilter(min(LOG_CMD_LVL, LOG_OUT_LVL, logging.WARNING) - 1))
    fullstream_handler.setFormatter(_lvl_fmt(cdict["name"], cdict["msg"]))
    root_logger.addHandler(fullstream_handler)

    if level <= logging.WARNING:
        warnstream_handler = logging.StreamHandler(sys.stdout)
        warnstream_handler.setLevel(logging.WARNING)
        warnstream_handler.addFilter(MaxFilter(logging.WARNING))
        warnstream_handler.setFormatter(_lvl_fmt(cdict["warn_name"], cdict["warn_msg"]))
        root_logger.addHandler(warnstream_handler)

    cmdstream_handler = logging.StreamHandler(sys.stdout)
    cmdstream_handler.setLevel(LOG_CMD_LVL)
    cmdstream_handler.addFilter(MaxFilter(LOG_CMD_LVL))
    cmdstream_handler.setFormatter(_lvl_fmt(cdict["cmd_name"], cdict["cmd_msg"]))
    root_logger.addHandler(cmdstream_handler)

    outstream_handler = logging.StreamHandler(sys.stdout)
    outstream_handler.setLevel(LOG_OUT_LVL)
    outstream_handler.addFilter(MaxFilter(LOG_OUT_LVL))
    outstream_handler.setFormatter(_lvl_fmt(cdict["out_name"], cdict["out_msg"]))
    root_logger.addHandler(outstream_handler)

    # create file-like loggers for madx-instance
    # create logger for madx output
    madx_out_logger = logging.getLogger(MADXOUT)
    if clear_handlers:
        madx_out_logger.handlers = []

    if output_log is not None:
        # log everything also to file
        madx_out_handler = logging.FileHandler(
            output_log,
            mode="w",
        )
        madx_out_handler.setFormatter(msg_fmt)
        madx_out_logger.addHandler(madx_out_handler)
    out_stream = StreamToLogger(madx_out_logger, log_level=LOG_OUT_LVL)

    # create logger for madx commands
    madx_cmd_logger = logging.getLogger(MADXCMD)
    if clear_handlers:
        madx_cmd_logger.handlers = []

    if command_log is not None:
        # log everything also to file
        madx_cmd_handler = logging.FileHandler(
            command_log,
            mode="w",
        )
        madx_cmd_handler.setFormatter(msg_fmt)
        madx_cmd_logger.addHandler(madx_cmd_handler)
    cmd_stream = StreamToLogger(madx_cmd_logger, log_level=LOG_CMD_LVL)

    return dict(stdout=out_stream, command_log=cmd_stream, stderr=subprocess.STDOUT)


def get_logger(
    name: str, level_root: int = DEBUG, level_console: int = None, fmt: str = BASIC_FORMAT, color: bool = None
) -> logging.Logger:
    """
    Returns a logger based on module name, with specific setup if name is **__main__**.

    Args:
        name (str): only used to check if __name__ is **__main__**.
        level_root (int): main logging level, defaults to ``DEBUG``.
        level_console (int): console logging level, defaults to ``INFO``.
        fmt (str): Format of the logging. For default see ``BASIC_FORMAT``.
        color (bool): If `None` colors are used if tty is detected.
              `False` will never use colors and `True` will always enforce them.
    Returns:
        A `~logging.Logger` instance.

    Example:
        .. code-block:: python

            >>> logger = get_logger(__name__)
    """
    logger_name = _get_caller_logger_name()

    if name == "__main__":
        if level_console is None:
            level_console = DEBUG if sys.flags.debug else INFO

        # set up root logger
        root_logger = logging.getLogger("")
        root_logger.handlers = []  # remove handlers in case someone already created them
        root_logger.setLevel(level_root)

        logging.addLevelName(MADX, "MADX")

        # print logs to the console
        root_logger.addHandler(
            get_stream_handler(
                level=max(level_console, DEBUG),
                max_level=INFO - 1,
                fmt=_maybe_bring_color(fmt, DEBUG, color),
            )
        )

        root_logger.addHandler(
            get_stream_handler(
                level=max(level_console, INFO),
                max_level=WARNING - 1,
                fmt=_maybe_bring_color(fmt, INFO, color),
            )
        )

        # print console warnings
        root_logger.addHandler(
            get_stream_handler(
                level=max(WARNING, level_console),
                max_level=ERROR - 1,
                fmt=_maybe_bring_color(fmt, WARNING, color),
            )
        )

        # print errors to error-stream
        root_logger.addHandler(
            get_stream_handler(
                stream=sys.stderr,
                level=max(ERROR, level_console),
                fmt=_maybe_bring_color(fmt, ERROR, color),
            )
        )

    # logger for the current file
    return logging.getLogger(logger_name)


def get_stream_handler(
    stream: StringIO = sys.stdout, level: int = DEBUG, fmt: str = BASIC_FORMAT, max_level: int = None
) -> logging.StreamHandler:
    """Convenience function so the caller does not have to import `logging`."""
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    console_formatter = logging.Formatter(fmt)
    handler.setFormatter(console_formatter)
    if max_level:
        handler.addFilter(MaxFilter(max_level))
    return handler


# ----- Helpers ----- #


def _lvl_fmt(name_color: str = "", msg_color: str = "") -> logging.Formatter:
    """Defines the level/message formatter with colors"""
    name_reset, msg_reset = "", ""
    if name_color:
        name_reset = CPYMAD_COLORS["reset"]
    if msg_color:
        msg_reset = CPYMAD_COLORS["reset"]

    return logging.Formatter(f"{name_color}%(levelname)7s{name_reset}" f" | " f"{msg_color}%(message)s{msg_reset}")


def _get_caller() -> str:
    """Find the caller of the current log-function."""
    this_file, _ = os.path.splitext(__file__)
    caller_file = this_file
    caller_frame = inspect.currentframe()
    while this_file == caller_file:
        caller_frame = caller_frame.f_back
        (caller_file_full, _, _, _, _) = inspect.getframeinfo(caller_frame)
        caller_file, _ = os.path.splitext(caller_file_full)
    return caller_file


def _get_current_module(current_file: str = None) -> str:
    """Find the name of the current module."""
    if not current_file:
        current_file = _get_caller()
    path_parts = os.path.abspath(current_file).split(os.path.sep)
    repo_parts = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir)).split(
        os.path.sep
    )

    current_module = ".".join(path_parts[len(repo_parts) : -1])
    return current_module


def _get_caller_logger_name() -> str:
    """Returns logger name of the caller."""
    caller_file = _get_caller()
    current_module = _get_current_module(caller_file)
    return ".".join([current_module, os.path.basename(caller_file)])


def _maybe_bring_color(format_string: str, colorlevel: int = INFO, color_flag: bool = None) -> str:
    """Adds color to the logs (can only be used in a terminal)."""
    if color_flag is None:
        color_flag = _isatty()

    if not color_flag:
        return format_string

    level = "%(levelname)"
    message = "%(message)"
    name = "%(name)"

    if colorlevel <= WARNING:
        format_string = format_string.replace(level, COLOR_LEVEL + level)
    else:
        format_string = format_string.replace(level, COLOR_ERROR + level)

    if colorlevel <= DEBUG:
        format_string = format_string.replace(message, COLOR_MESSAGE_LOW + message)
    elif colorlevel <= INFO:
        format_string = format_string.replace(message, COLOR_MESSAGE + message)
    elif colorlevel <= WARNING:
        format_string = format_string.replace(message, COLOR_WARN + message)
    else:
        format_string = format_string.replace(message, COLOR_ERROR + message)

    format_string = format_string.replace(name, COLOR_NAME + name)
    format_string = format_string.replace(DIVIDER, COLOR_DIVIDER + DIVIDER)
    format_string = format_string + COLOR_RESET

    return format_string


def _isatty() -> bool:
    """Checks if stdout is a tty, which means it should support color-codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
