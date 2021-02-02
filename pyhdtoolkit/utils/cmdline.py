"""
Module utils.cmdline
--------------------

Created on 2019.11.06
:author: Felix Soubelet (felix.soubelet@cern.ch)

Utility script to help run commands and access the commandline.
"""

import errno
import os
import signal
import subprocess

from typing import Mapping, Optional, Tuple

from loguru import logger

from pyhdtoolkit.utils.contexts import timeit


class CommandLine:
    """
    A high-level object to encapsulate the different methods for interacting with the commandline.
    """

    @staticmethod
    def check_pid_exists(pid: int) -> bool:
        """
        Check whether the given PID exists in the current process table.

        Args:
            pid (int): the Process ID you want to check.

        Returns:
            A boolean stating the result.
        """
        if pid == 0:
            # According to "man 2 kill", PID 0 refers to <<every process in the process group of
            # the calling process>>. Best not to go any further.
            logger.warning("PID 0 refers to 'every process in calling processes', and should be untouched")
            return True
        try:
            # Sending SIG 0 only checks if process has terminated, we're not actually terminating it
            os.kill(pid, 0)
        except OSError as pid_checkout_error:
            if pid_checkout_error.errno == errno.ESRCH:  # ERROR "No such process"
                return False
            if (
                pid_checkout_error.errno == errno.EPERM
            ):  # ERROR "Operation not permitted" -> there's a process to deny access to.
                return True
            # According to "man 2 kill" possible error values are (EINVAL, EPERM, ESRCH), therefore
            # we should never get here. If so let's be explicit in considering this an error.
            logger.exception("Could not figure out the provided PID for some reason")
            raise pid_checkout_error
        return True

    @staticmethod
    def run(
        command: str, shell: bool = True, env: Mapping = None, timeout: float = None
    ) -> Tuple[Optional[int], bytes]:
        """
        Run command based on `subprocess.Popen` and return the tuple of `(returncode, stdout)`.
        Note that `stderr` is redirected to `stdout`. `shell` is same to parameter of `Popen`.
        If the process does not terminate after `timeout` seconds, a `TimeoutExpired` exception
        will be raised.

        Args:
            command (str): string, the command you want to run.
            shell (bool): same as `Popen` argument. Setting the shell argument to a true value
                causes subprocess to spawn an intermediate shell process, and tell it to run the
                command. In other words, using an intermediate shell means that variables, glob
                patterns, and other special shell features in the command string are processed
                before the command is ran. Defaults to True.
            env (Mapping): mapping that defines the environment variables for the new process.
            timeout (float): same as `Popen.communicate` argument, number of seconds to wait for a
                response before raising a TimeoutExpired exception.

        Returns:
            The tuple of (returncode, stdout). Beware, the stdout will be a byte array (id est
            b'some returned text'). This output, returned as stdout, needs to be decoded properly
            before you do anything with it, especially if you intend to log it into a file. While
            it will most likely be 'utf-8', the encoding can vary from system to system so the
            standard output is returned in bytes format and should be decoded later on.

        Usage:
            CommandLine.run('echo hello') -> (0, b'hello\r\n')

            modified_env = os.environ.copy()
            modified_env['ENV_VAR'] = new_value
            CommandLine.run('echo $ENV_VAR', env=modified_env) -> (0, b'new_value')
        """
        with timeit(
            lambda spanned: logger.info(f"Ran command '{command}' in a subprocess, in: {spanned:.4f} seconds")
        ):
            process = subprocess.Popen(
                command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
            )
            stdout, _ = process.communicate(timeout=timeout)
            if process.poll() != 0:
                logger.warning(f"Subprocess command '{command}' finished with exit code: {process.poll()}")
            else:
                logger.success(f"Subprocess command '{command}' finished with exit code: {process.poll()}")
        return process.poll(), stdout

    @staticmethod
    def terminate(pid: int) -> bool:
        """
        Terminate process by given pid. On Other platforms, using os.kill with signal.SIGTERM
        to kill.

        Args:
            pid (int): the process ID to kill.

        Returns:
            A boolean stating the success of the operation.
        """
        if CommandLine.check_pid_exists(pid):
            os.kill(pid, signal.SIGTERM)
            logger.debug(f"Process {pid} has successfully been terminated.")
            return True
        logger.error(f"Process with ID {pid} could not be terminated.")
        return False
