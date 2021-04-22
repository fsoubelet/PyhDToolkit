"""
Module utils.htc_monitor
------------------------

Created on 2021.04.22
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with utility to query the HTCondor queue, process the returned data and display it nicely.
"""
import re
import time

from typing import List, Tuple, Union

import pendulum

from pendulum import DateTime
from pydantic import BaseModel
from rich import box
from rich.console import Console, RenderGroup
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from pyhdtoolkit.utils import defaults
from pyhdtoolkit.utils.cmdline import CommandLine

defaults.config_logger(level="ERROR")

# ----- Data ----- #

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

TASK_COLUMNS_SETTINGS = {
    "OWNER": dict(justify="left", header_style="bold", style="bold", no_wrap=True),
    "BATCH_NAME": dict(justify="center", header_style="magenta", style="magenta", no_wrap=True),
    "SUBMITTED": dict(
        justify="center", header_style="medium_turquoise", style="medium_turquoise", no_wrap=True
    ),
    "DONE": dict(justify="right", header_style="bold green3", style="bold green3", no_wrap=True),
    "RUNNING": dict(
        justify="right", header_style="bold cornflower_blue", style="bold cornflower_blue", no_wrap=True
    ),
    "IDLE": dict(justify="right", header_style="bold dark_orange3", style="bold dark_orange3", no_wrap=True),
    "TOTAL": dict(justify="right", style="bold", no_wrap=True),
    "JOB_IDS": dict(justify="right", no_wrap=True),
}

CLUSTER_COLUMNS_SETTINGS = {
    "SOURCE": dict(justify="left", header_style="bold", style="bold", no_wrap=True),
    "JOBS": dict(justify="right", header_style="bold", style="bold", no_wrap=True),
    "COMPLETED": dict(justify="right", header_style="bold green3", style="bold green3", no_wrap=True),
    "RUNNING": dict(
        justify="right", header_style="bold cornflower_blue", style="bold cornflower_blue", no_wrap=True
    ),
    "IDLE": dict(justify="right", header_style="bold dark_orange3", style="bold dark_orange3", no_wrap=True),
    "HELD": dict(justify="right", header_style="bold gold1", style="bold gold1", no_wrap=True),
    "SUSPENDED": dict(
        justify="right", header_style="bold slate_blue1", style="bold slate_blue1", no_wrap=True
    ),
    "REMOVED": dict(justify="right", header_style="bold red3", style="bold red3", no_wrap=True),
}


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
    user: BaseSummary
    cluster: BaseSummary


class HTCTaskSummary(BaseModel):
    owner: str
    batch_name: int
    submitted: DateTime
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
            - A validated ClusterSummary object with scheduler identification and summaries of the user
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
            querying_owner = tasks[0].owner if tasks else ""
            if querying_owner in line:
                owner_summary = _process_cluster_summary_line(line, querying_owner)
            elif "all users" in line:
                full_summary = _process_cluster_summary_line(line)
    return tasks, ClusterSummary(scheduler_id=scheduler_id, user=owner_summary, cluster=full_summary)


# ----- Output Formating ----- #


def make_tasks_table(tasks: List[HTCTaskSummary]) -> Table:
    table = _default_tasks_table()
    date_display_format = "dddd, D MMM YY at LT (zz)"  # example: Wednesday, 21 Apr 21 9:04 PM (CEST)
    for task in tasks:
        table.add_row(
            task.owner,
            str(task.batch_name),
            task.submitted.format(fmt=date_display_format),
            str(task.done),
            str(task.run),
            str(task.idle),
            str(task.total),
            task.job_ids,
        )
    return table


def make_cluster_table(owner_name: str, cluster: ClusterSummary) -> Table:
    table = _default_cluster_table()
    table.add_row(
        owner_name,
        str(cluster.user.jobs),
        str(cluster.user.completed),
        str(cluster.user.running),
        str(cluster.user.idle),
        str(cluster.user.held),
        str(cluster.user.suspended),
        str(cluster.user.removed),
    )
    table.add_row(
        "All Users",
        str(cluster.cluster.jobs),
        str(cluster.cluster.completed),
        str(cluster.cluster.running),
        str(cluster.cluster.idle),
        str(cluster.cluster.held),
        str(cluster.cluster.suspended),
        str(cluster.cluster.removed),
    )
    return table


# ----- Helpers ----- #


def _process_scheduler_information_line(line: str) -> str:
    """Extract only the 'Schedd: <cluster>.cern.ch' part oof the scheduler information line"""
    result = re.search(r"Schedd: (.*).cern.ch", line)
    return result.group(1)


def _process_task_summary_line(line: str) -> HTCTaskSummary:
    """
    Extract the various information in a task summary line, validated and returned as an HTCTaskSummary
    object.
    """
    line_elements = line.split()
    return HTCTaskSummary(
        owner=line_elements[0],
        batch_name=line_elements[2],  # line_elements[1] is the 'ID:' part, we don't need it
        submitted=pendulum.from_format(
            f"{line_elements[3]} {line_elements[4]}", fmt="MM/D HH:mm", tz="Europe/Paris"
        ),  # Geneva timezone is Paris timezone,
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


def _default_tasks_table() -> Table:
    """Create the default structure for the Tasks Table, hard coded columns and no rows added."""
    table = Table(width=120, box=box.SIMPLE_HEAVY)
    for header, header_col_settings in TASK_COLUMNS_SETTINGS.items():
        table.add_column(header, **header_col_settings)
    return table


def _default_cluster_table() -> Table:
    """Create the default structure for the Cluster Table, hard coded columns and no rows added."""
    table = Table(width=120, box=box.HORIZONTALS)
    for header, header_col_settings in CLUSTER_COLUMNS_SETTINGS.items():
        table.add_column(header, **header_col_settings)
    return table


# ----- Executable ----- #


if __name__ == "__main__":

    def generate_renderable() -> RenderGroup:
        """
        Function called to update the live display, fetches data from htcondor, does the processing and
        returns a RenderGroup with both Panels.
        """
        # condor_string = query_condor_q()
        user_tasks, cluster_info = read_condor_q(EXAMPLE)  # TODO: replace with condor_string
        # TODO: handle crash case where there are no tasks, and we can't get owner
        owner = user_tasks[0].owner if user_tasks else "User"

        tasks_table = make_tasks_table(user_tasks)
        cluster_table = make_cluster_table(owner, cluster_info)
        return RenderGroup(
            Panel(
                tasks_table,
                title=f"Scheduler: {cluster_info.scheduler_id}.cern.ch",
                expand=False,
                border_style="scope.border",
            ),
            Panel(
                cluster_table,
                title=f"{cluster_info.scheduler_id} Statistics",
                expand=False,
                border_style="scope.border",
            ),
        )

    with Live(generate_renderable(), refresh_per_second=1) as live:
        while True:
            live.console.log("Querying HTCondor Queue")
            live.update(generate_renderable())
            time.sleep(60)
