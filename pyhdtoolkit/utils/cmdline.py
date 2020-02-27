"""
Created on 2019.11.06
:author: Felix Soubelet (felix.soubelet@cern.ch)

Utility script to help run commands and access the commandline.
"""

import errno
import os
import signal
import subprocess
import sys

from fsbox import logging_tools
from fsbox.contexts import timeit

LOGGER = logging_tools.get_logger(__name__)


class CommandLine:
    """
    A high-level object to encapsulate the different methods for interacting with the commandline.
    """

    @staticmethod
    def check_pid_exists(pid: int) -> bool:
        """
        Check whether the given PID exists in the current process table.
        :return: a boolean stating the result.
        """
        if pid == 0:
            # According to "man 2 kill",  PID 0 has a special meaning: it refers to <<every process in the process
            # group of the calling process>>, so it is best to not go any further.
            LOGGER.info(f"PID 0 refers to 'every process in the group of calling processes', and should be untouched.")
            return True
        try:
            # sending SIG 0 only checks if process has terminated, we're not actually terminating it
            os.kill(pid, 0)
        except OSError as error:
            if error.errno == errno.ESRCH:  # ERROR "No such process"
                return False
            if error.errno == errno.EPERM:  # ERROR "Operation not permitted" -> there's a process to deny access to.
                return True
            # According to "man 2 kill" possible error values are (EINVAL, EPERM, ESRCH), therefore we should
            # never get here. If so let's be explicit in considering this an error.
            raise error
        return True

    @staticmethod
    def run(command, shell: bool = True, env=None, timeout: float = None) -> tuple:
        """
        Run command based on `subprocess.Popen` and return the tuple of `(returncode, stdout)`.
        Note that `stderr` is redirected to `stdout`. `shell` is same to parameter of `Popen`.
        If the process does not terminate after `timeout` seconds, a `TimeoutExpired`
        exception will be raised.
        :param command: the command you want to run.
        :param shell: same as `Popen` argument. Setting the shell argument to a true value causes subprocess to spawn an
        intermediate shell process, and tell it to run the command. In other words, using an intermediate shell means
        that variables, glob patterns, and other special shell features in the command string are processed before the
        command is run.
        :param env: same as `Popen` argument, a bit beyond me for now.
        :param timeout: same as `Popen.communicate` argument, number of seconds to wait for a response before raising an
        exception.
        :return: the tuple of (returncode, stdout).
        Usage:
            run('echo hello') -> (0, b'hello\r\n')
        """
        with timeit(lambda spanned: LOGGER.info(f"Ran command '{command}' in a subprocess, in: {spanned}s")):
            process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            stdout, _ = process.communicate(timeout=timeout)
        return process.poll(), stdout

    @staticmethod
    def terminate(pid: int) -> None:
        """
        Terminate process by given pid.
        On Other platforms, using os.kill with signal.SIGTERM to kill.
        :param pid: the process ID to kill
        """
        if CommandLine.check_pid_exists(pid):
            os.kill(pid, signal.SIGTERM)
            LOGGER.info(f"Process {pid} has successfully been terminated.")
        else:
            LOGGER.error(f"Process with ID {pid} could not be terminated.")

    @staticmethod
    def get_cmdline_argv() -> list:
        """
        Get command line argv of self python process.
        :return: a list with those arguments.
        """
        return sys.argv


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
