import os
import subprocess

import pytest

from pyhdtoolkit.utils.cmdline import CommandLine


def test_run_echo_cmd():
    assert CommandLine.run("echo hello") == (0, b"hello\n")


def test_run_cmd_noshell():
    with pytest.raises(FileNotFoundError):
        CommandLine.run("echo hello", shell=False)


def test_run_cmd_modified_env():
    modified_env = os.environ.copy()
    modified_env["TEST_VAR"] = "Check_me_string"
    assert CommandLine.run("echo $TEST_VAR", env=modified_env) == (0, b"Check_me_string\n")


def test_run_cmd_timedout():
    with pytest.raises(subprocess.TimeoutExpired):
        CommandLine.run("sleep 5", timeout=0.5)
