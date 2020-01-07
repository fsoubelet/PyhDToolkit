"""
Created on 2019.11.06
:author: Felix Soubelet (felix.soubelet@cern.ch)

Utility script to help run commands and access the commandline.
"""

import os
import signal
import sys
from subprocess import PIPE, STDOUT, Popen


class CommandLine:
    """
    A high-level object to encapsulate the different methods for interacting with the commandline.
    """

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
        p = Popen(command, shell=shell, stdout=PIPE, stderr=STDOUT, env=env)
        stdout, _ = p.communicate(timeout=timeout)
        return p.poll(), stdout

    @staticmethod
    def terminate(pid: int) -> None:
        """
        Terminate process by given pid.
        On Other platforms, using os.kill with signal.SIGTERM to kill.
        """
        os.kill(pid, signal.SIGTERM)

    @staticmethod
    def get_cmdline_argv() -> list:
        """
        Get command line argv of self python process.
        :return: a list wi
        """
        return sys.argv


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
