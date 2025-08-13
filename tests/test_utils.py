import os
import pathlib
import pickle
import random
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import pytest
import tfs
from loguru import logger
from numpy.testing import assert_array_equal
from rich.table import Table

from pyhdtoolkit.utils import _misc, logging
from pyhdtoolkit.utils.cmdline import CommandLine
from pyhdtoolkit.utils.decorators import deprecated, maybe_jit
from pyhdtoolkit.utils.htc_monitor import (
    ClusterSummary,
    HTCTaskSummary,
    _make_cluster_table,
    _make_tasks_table,
    read_condor_q,
)

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"


def test_deprecation_decorator():
    @deprecated("This is a test")
    def some_func(a, b):
        return a + b

    with pytest.warns(DeprecationWarning):
        some_func(1, 2)


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Windows is a shitshow for this.")
class TestCommandLine:
    def test_check_pid(self):
        assert CommandLine.check_pid_exists(os.getpid()) is True
        assert CommandLine.check_pid_exists(0) is True
        assert CommandLine.check_pid_exists(int(1e6)) is False  # default max PID is 32768 on linux, 99999 on macOS
        with pytest.raises(TypeError):
            CommandLine.check_pid_exists("not_an_integer")

    def test_run_cmd(self):
        assert isinstance(CommandLine.run("echo hello"), tuple)
        assert isinstance(CommandLine.run("echo hello")[1], bytes)
        assert CommandLine.run("echo hello") == (0, b"hello\n")
        modified_env = os.environ.copy()
        modified_env["TEST_VAR"] = "Check_me_string"
        assert CommandLine.run("echo $TEST_VAR", env=modified_env) == (0, b"Check_me_string\n")
        with pytest.raises(FileNotFoundError):
            CommandLine.run("echo hello", shell=False)

    @pytest.mark.parametrize("sleep_time", list(range(1, 15)))
    def test_run_cmd_timedout(self, sleep_time):
        with pytest.raises(subprocess.TimeoutExpired):
            CommandLine.run(f"sleep {sleep_time}", timeout=0.1)

    @pytest.mark.parametrize("pid", [random.randint(int(1e6), int(5e6)) for _ in range(10)])
    def test_terminate_nonexistent_pid(self, pid):
        """Default max PID is 32768 on linux, 99999 on macOS."""
        assert CommandLine.terminate(pid) is False

    @pytest.mark.parametrize("sleep_time", list(range(10, 60)))  # each one will spawn a different process
    def test_terminate_pid(self, sleep_time):
        sacrificed_process = subprocess.Popen(f"sleep {sleep_time}", shell=True)
        assert CommandLine.terminate(sacrificed_process.pid) is True


class TestHTCMonitor:
    def test_read_condor_q(self, _condor_q_output, _correct_user_tasks, _correct_cluster_summary):
        user_tasks, cluster_info = read_condor_q(_condor_q_output)
        assert isinstance(user_tasks, list)
        for task in user_tasks:
            assert isinstance(task, HTCTaskSummary)
        assert user_tasks == _correct_user_tasks

        assert isinstance(cluster_info, ClusterSummary)
        assert cluster_info == _correct_cluster_summary

    def test_read_taskless_condor_q(self, _taskless_condor_q_output, _correct_cluster_summary):
        user_tasks, cluster_info = read_condor_q(_taskless_condor_q_output)

        assert isinstance(user_tasks, list)
        assert user_tasks == []

        assert isinstance(cluster_info, ClusterSummary)
        assert cluster_info == _correct_cluster_summary

    def test_cluster_table_creation(self, _condor_q_output):
        user_tasks, cluster_info = read_condor_q(_condor_q_output)
        owner = user_tasks[0].owner if user_tasks else "User"

        cluster_table = _make_cluster_table(owner, cluster_info)
        assert isinstance(cluster_table, Table)

    def test_tasks_table_creation(self, _condor_q_output, _taskless_condor_q_output):
        user_tasks, cluster_info = read_condor_q(_condor_q_output)
        tasks_table = _make_tasks_table(user_tasks)
        assert isinstance(tasks_table, Table)

        user_tasks, cluster_info = read_condor_q(_taskless_condor_q_output)
        tasks_table = _make_tasks_table(user_tasks)
        assert isinstance(tasks_table, Table)


class TestLogging:
    def test_logger_config(self, capsys):
        logging.config_logger()
        message = "This should be in stdout now"
        logger.info(message)
        captured = capsys.readouterr()
        assert message in captured.out

        # This is to get it back as it is by defaults for other tests
        logger.remove()
        logger.add(sys.stderr)


class TestMisc:
    def test_log_runtime(self):
        _misc.log_runtime_versions()

    def test_query_betastar_from_opticsfile(self):
        assert _misc.get_betastar_from_opticsfile(INPUTS_DIR / "madx" / "opticsfile.22") == 0.3

    def test_query_betastar_from_opticsfile_raises_on_invalid_symmetry_if_required(self):
        with pytest.raises(
            AssertionError, match="The betastar values for IP1 and IP5 are not the same in both planes."
        ):
            _misc.get_betastar_from_opticsfile(INPUTS_DIR / "madx" / "opticsfile.asymmetric", check_symmetry=True)

    def test_colin_balance_applies(self, _non_matched_lhc_madx):
        madx = _non_matched_lhc_madx
        _misc.apply_colin_corrs_balance(madx)
        for side in "rl":
            for ip in (1, 2, 5, 8):
                assert madx.globals[f"kqsx3.{side}{ip}"] != 0
        assert "ir_quads_errors" in madx.table

    @pytest.mark.parametrize("drop", [True, False])
    def test_complex_columns_split(self, _complex_columns_df, drop):
        original = _complex_columns_df
        split = _misc.split_complex_columns(original, drop)

        for col in original.columns:
            assert f"{col}_REAL" in split.columns
            assert f"{col}_IMAG" in split.columns

            assert_array_equal(np.real(original[col]), split[f"{col}_REAL"].to_numpy())
            assert_array_equal(np.imag(original[col]), split[f"{col}_IMAG"].to_numpy())

            if drop is True:
                assert col not in split.columns

    def test_bpm_noise_addition(self, _rdts_df):
        original = tfs.read(_rdts_df)
        original = original.loc[original.index.str.contains("bpm", case=False)]

        ir_noisy = _misc.add_noise_to_ir_bpms(original, max_index=5, stdev=1e-2)
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(original, ir_noisy)

        arc_noisy = _misc.add_noise_to_arc_bpms(original, min_index=5, stdev=1e-2)
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(original, arc_noisy)


class TestJIT:
    def test_jit_works(self):
        # I use here the first example from the
        # numba jit documentation with larger array
        x = np.arange(10000).reshape(100, 100)

        # This is the function from the docs
        def go_fast(a: np.ndarray) -> np.ndarray:
            trace = 0.0
            for i in range(a.shape[0]):  # Numba likes loops
                trace += np.tanh(a[i, i])  # Numba likes NumPy functions
            return a + trace  # Numba likes NumPy broadcasting

        go_fast_jitted = maybe_jit(go_fast)
        go_fast_jitted(x)  # first call to compile

        # Determine time for initial function
        start1 = time.time()
        for _ in range(25_000):
            res1 = go_fast(x)
        end1 = time.time()
        time1 = end1 - start1

        # Determine time for jitted function
        start2 = time.time()
        for _ in range(25_000):
            res2 = go_fast_jitted(x)
        end2 = time.time()
        time2 = end2 - start2

        # Compare results validity and execution time
        assert np.allclose(res1, res2)
        assert time2 < time1


# ----- Fixtures ----- #


@pytest.fixture
def _condor_q_output() -> str:
    return """-- Schedd: bigbird08.cern.ch : <188.185.72.155:9618?... @ 04/22/21 12:26:02
OWNER    BATCH_NAME     SUBMITTED   DONE   RUN    IDLE  TOTAL JOB_IDS
fesoubel ID: 8489182   4/21 21:04      7     14      _     21 8489182.0-20
fesoubel ID: 8489183   4/21 21:04      2     19      _     21 8489183.0-20
fesoubel ID: 8489185   4/21 21:05      _     21      _     21 8489185.0-20
fesoubel ID: 8489185   4/21 21:05      _     18      3     21 8489187.0-20
fesoubel ID: 8489185   4/21 21:05      _     13      8     21 8489188.0-20
fesoubel ID: 8489185   4/21 21:06      _      8     13     21 8489191.0-20
fesoubel ID: 8489185   4/21 21:06      _      3     18     21 8489193.0-20

Total for query: 63 jobs; 0 completed, 0 removed, 1 idle, 62 running, 0 held, 0 suspended
Total for fesoubel: 63 jobs; 0 completed, 0 removed, 1 idle, 62 running, 0 held, 0 suspended
Total for all users: 7279 jobs; 1 completed, 1 removed, 3351 idle, 3724 running, 202 held, 0 suspended"""


@pytest.fixture
def _taskless_condor_q_output() -> str:
    return """-- Schedd: bigbird08.cern.ch : <188.185.72.155:9618?... @ 04/22/21 12:26:02
OWNER    BATCH_NAME     SUBMITTED   DONE   RUN    IDLE  TOTAL JOB_IDS

Total for query: 63 jobs; 0 completed, 0 removed, 1 idle, 62 running, 0 held, 0 suspended
Total for fesoubel: 63 jobs; 0 completed, 0 removed, 1 idle, 62 running, 0 held, 0 suspended
Total for all users: 7279 jobs; 1 completed, 1 removed, 3351 idle, 3724 running, 202 held, 0 suspended"""


@pytest.fixture
def _correct_user_tasks() -> list[HTCTaskSummary]:
    pickle_file_path = INPUTS_DIR / "utils" / "correct_user_tasks.pkl"
    with pickle_file_path.open("rb") as file:
        return pickle.load(file)


@pytest.fixture
def _correct_cluster_summary() -> ClusterSummary:
    pickle_file_path = INPUTS_DIR / "utils" / "correct_cluster_summary.pkl"
    with pickle_file_path.open("rb") as file:
        return pickle.load(file)


@pytest.fixture
def _complex_columns_df() -> pd.DataFrame:
    array = np.random.rand(50, 5) + 1j * np.random.rand(50, 5)
    return pd.DataFrame(data=array, columns=["A", "B", "C", "D", "E"])


@pytest.fixture
def _rdts_df() -> pathlib.Path:
    return INPUTS_DIR / "cpymadtools" / "lhc_coupling_bump.tfs"
