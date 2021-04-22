import re

from typing import List, Union, Tuple

from pydantic import BaseModel

from pyhdtoolkit.utils import defaults
from pyhdtoolkit.utils.cmdline import CommandLine
from rich.table import Table
defaults.config_logger()

# ----- Data ----- #

HTC_TASK_HEADERS: List[str] = ["OWNER", "BATCH_NAME", "SUBMITTED", "DONE", "RUN", "IDLE", "TOTAL", "JOB_IDS"]
HTC_CLUSTER_HEADERS: List[str] = ["JOBS", "COMPLETED", "REMOVED", "IDLE", "RUNNING", "HELD", "SUSPENDED"]


class BaseSummary(BaseModel):
    jobs: int
    completed: int
    removed: int
    idle: int
    running: int
    held: int
    suspended: int


class ClusterSummary(BaseModel):
    scheduler_id: str
    owner: BaseSummary
    cluster: BaseSummary


class HTCTaskSummary(BaseModel):
    owner: str
    batch_name: int
    submitted: str
    done: Union[int, str]
    run: Union[int, str]
    idle: Union[int, str]
    total: int
    job_ids: str


# ----- HTCondor Querying / Processing ----- #


def query_condor_q() -> str:
    """
    Returns a decoded string with the result of the 'condor_q' command, to get status on your jobs.
    """
    return_code, raw_result = CommandLine.run("condor_q")
    condor_status = raw_result.decode()
    if return_code == 0:
        return condor_status
    else:
        raise ChildProcessError("Checking htcondor status failed")


def read_condor_q(report: str) -> Tuple[List[HTCTaskSummary], ClusterSummary]:
    """
    Split information from different parts of the condor_q output into one data structure.

    Args:
        report (str): the utf-8 decoded string returned by the 'condor_q' command.

    Returns:
        A tuple of:
            - A list of each task summary given by 'condor_q', each as a validated HTCTaskSummary object,
            - A validated ClusterSummary object with scheduler identification and summaries of the owner
                as well as all users' statistics on this scheduler cluster.

    Example Usage:
        condor_q_output = get_the_string_as_you_wish(...)
        tasks, cluster = read_condor_q(condor_q_outout)
    """
    tasks: List[HTCTaskSummary] = []
    next_line_is_task_report = False

    for line in report.split("\n"):
        if line.startswith("-- Schedd:"):  # extract scheduler information
            scheduler_id = _process_scheduler_information_line(line)

        elif line.startswith("OWNER"):  # headers line before we get task reports
            next_line_is_task_report = True

        elif next_line_is_task_report:  # extract task report information
            if line != "\n" and line != "":
                tasks.append(_process_task_summary_line(line))
            else:  # an empty line denotes the end of the task report(s)
                next_line_is_task_report = False

        else:  # extract cluster information
            querying_owner = tasks[0].owner
            if querying_owner in line:
                owner_summary = _process_cluster_summary_line(line, querying_owner)
            elif "all users" in line:
                full_summary = _process_cluster_summary_line(line)
    return tasks, ClusterSummary(scheduler_id=scheduler_id, owner=owner_summary, cluster=full_summary)


# ----- Output Formating ----- #


def make_tasks_table(tasks: List[HTCTaskSummary], cluster_info: ClusterSummary) -> Table:
    pass


# ----- Helpers ----- #


def _process_scheduler_information_line(line: str) -> str:
    """Extract only the 'Schedd: <cluster>.cern.ch' part oof the scheduler information line"""
    result = re.search(r"Schedd: (.*).cern.ch", line)
    return result.group(0)


def _process_task_summary_line(line: str) -> HTCTaskSummary:
    """
    Extract the various information in a task summary line, validated and returned as an HTCTaskSummary
    object.
    """
    line_elements = line.split()
    return HTCTaskSummary(
        owner=line_elements[0],
        batch_name=line_elements[2],  # line_elements[1] is the 'ID:' part, we don't need it
        submitted=f"{line_elements[3]} {line_elements[4]}",  # 'day/month' and 'hour:minute'
        done=line_elements[5],
        run=line_elements[6],
        idle=line_elements[7],
        total=line_elements[8],
        job_ids=line_elements[9],
    )


def _process_cluster_summary_line(line: str, querying_owner: str = None) -> BaseSummary:
    result = re.search(
        rf"Total for {querying_owner if querying_owner else 'all users'}: (\d+) jobs; (\d+) completed, "
        "(\d+) removed, (\d+) idle, (\d+) running, (\d+) held, (\d+) suspended",
        line,
    )
    return BaseSummary(
        jobs=result.group(1),
        completed=result.group(2),
        removed=result.group(3),
        idle=result.group(4),
        running=result.group(5),
        held=result.group(6),
        suspended=result.group(7),
    )


# ----- Executable ----- #

def main() -> None:
    """Query 'condor_q', process the output and nicely format it to the terminal."""











# ----- Storage ----- #


EXAMPLE = """-- Schedd: bigbird08.cern.ch : <188.185.72.155:9618?... @ 04/22/21 12:26:02
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
Total for all users: 7279 jobs; 1 completed, 1 removed, 3351 idle, 3724 running, 202 held, 0 suspended
"""
