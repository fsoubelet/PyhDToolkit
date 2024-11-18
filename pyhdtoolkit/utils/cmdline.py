"""
.. _utils-cmdline:

Command Line Utilities
----------------------

Utility class and functions to help run commands and access the command line.
"""

from __future__ import annotations

import errno
import os
import signal
import subprocess

from typing import TYPE_CHECKING

from loguru import logger

from pyhdtoolkit.utils.contexts import timeit

if TYPE_CHECKING:
    from collections.abc import Mapping


class CommandLine:
    """
    .. versionadded:: 0.2.0

    A high-level object to encapsulate the different
    methods for interacting with the commandline.
    """

    @staticmethod
    def check_pid_exists(pid: int) -> bool:
        """
        .. versionadded:: 0.2.0

        Check whether the given *PID* exists in the
        current process table.

        Parameters
        ----------
        pid : int
            The Process ID to check the existence of.

        Returns
        -------
        bool
            A boolean stating the result.

        Example
        -------
            .. code-block:: python

                CommandLine.check_pid_exists(os.getpid())
                # True
        """
        if pid == 0:
            # According to "man 2 kill", PID 0 refers to <<every process in the process group of
            # the calling process>>. Best not to go any further.
            logger.warning("PID 0 refers to 'every process in calling processes', and should be untouched")
            return True
        try:
            # Sending SIG 0 only checks if process has terminated,
            # we're not actually terminating it by doing so
            os.kill(pid, 0)
        except OSError as pid_checkout_error:
            # Below is ERROR "No such process"
            if pid_checkout_error.errno == errno.ESRCH:
                return False
            # Below is ERROR "Operation not permitted" -> there's a process to deny access to.
            if pid_checkout_error.errno == errno.EPERM:
                return True
            # According to "man 2 kill" possible error values are (EINVAL, EPERM, ESRCH), therefore
            # we should never get here. If so let's be explicit in considering this an error.
            logger.exception("Could not figure out the provided PID for some reason")
            raise
        return True

    @staticmethod
    def run(
        command: str, shell: bool = True, env: Mapping | None = None, timeout: float | None = None
    ) -> tuple[int | None, bytes]:
        """
        .. versionadded:: 0.2.0

        Runs *command* through `subprocess.Popen` and
        returns the tuple of `(returncode, stdout)`.

        Note
        ----
            Note that ``stderr`` is redirected to ``stdout``.
            Here *shell* is identical to the same parameter
            of `subprocess.Popen`.

        Parameters
        ----------
        command : str
            The command to run.
        shell : bool
            Same parameter as `subprocess.Popen`. If `True`, the
            command will be run through an intermediate shell,
            and variables, glob patterns, and other special shell
            features in the command string are processed before
            the command is run. Defaults to `True`.
        env : Mapping, optional
            A mapping that defines the environment variables for
            the new process.
        timeout : float, optional
            Same as the `subprocess.Popen.communicate` argument,
            the number of seconds to wait for a response before
            raising a `TimeoutExpired` exception.

        Returns
        -------
        tuple[int | None, bytes]
            The `tuple` of `(returncode, stdout)`. Beware, the stdout
            will be a byte array (i.e. ``b"some returned text"``). This
            output, returned as stdout, needs to be decoded properly
            before you do anything with it, especially if you intend to
            log it into a file. While it will most likely be "utf-8", the
            encoding can vary from system to system so the standard output
            is returned in bytes format and should be decoded later on.

        Raises
        ------
        TimeoutExpired
            If a value was provided for *timeout* and the process does not
            terminate before *timeout* seconds.

        Examples
        --------

            .. code-block:: python

                CommandLine.run("echo hello")
                # returns (0, b"hello\\r\\n")

            .. code-block:: python

                import os

                modified_env = os.environ.copy()
                modified_env["ENV_VAR"] = "new_value"
                CommandLine.run("echo $ENV_VAR", env=modified_env)
                # returns (0, b"new_value")
        """
        with timeit(lambda spanned: logger.info(f"Ran command '{command}' in a subprocess, in: {spanned:.4f} seconds")):
            process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            stdout, _ = process.communicate(timeout=timeout)
            if process.poll() != 0:  # pragma: no cover
                logger.warning(f"Subprocess command '{command}' finished with exit code: {process.poll()}")
            else:
                logger.success(f"Subprocess command '{command}' finished with exit code: {process.poll()}")
        return process.poll(), stdout

    @staticmethod
    def terminate(pid: int) -> bool:
        """
        .. versionadded:: 0.2.0

        Terminates the process corresponding to the given *PID*.
        On other platforms, uses `os.kill` with `signal.SIGTERM`
        to kill.

        Parameters
        ----------
        pid : int
            The ID of the process to kill.

        Returns
        -------
        bool
            A boolean stating the success of the operation.

        Example
        -------
            .. code-block:: python

                CommandLine.terminate(500_000)  # max PID is 32768 (99999) on linux (macOS).
                # returns False
        """
        if CommandLine.check_pid_exists(pid):
            os.kill(pid, signal.SIGTERM)
            logger.debug(f"Process {pid} has successfully been terminated.")
            return True
        logger.error(f"Process with ID {pid} could not be terminated.")
        return False
