"""
.. _utils-htcondor:

HTCondor Monitoring Utilities
-----------------------------

A module with utility to query the HTCondor queue, process
the returned data and display it nicely with rich. Only
the utility functions are included here, a callable script
is provided in `pyhdtoolkit.scripts.htc_monitor`.
"""

from __future__ import annotations

import re

import pendulum
from rich import box
from rich.table import Table

from pyhdtoolkit.models.htc import BaseSummary, ClusterSummary, HTCTaskSummary
from pyhdtoolkit.utils.cmdline import CommandLine

# ----- Caching ------ #

# We compile regex patterns once only
_SCHEDD_RE: re.Pattern[str] = re.compile(r"Schedd:\s+(?P<cluster>[^.]+)\.cern\.ch")

# This one needs to be formatted with the
# querying owner before it can be compiled
_CLUSTER_SUMMARY_RE_TEMPLATE: str = (
    r"Total for {query}: "
    r"(?P<jobs>\d+) jobs; "
    r"(?P<completed>\d+) completed, "
    r"(?P<removed>\d+) removed, "
    r"(?P<idle>\d+) idle, "
    r"(?P<running>\d+) running, "
    r"(?P<held>\d+) held, "
    r"(?P<suspended>\d+) suspended"
)

# ----- Settings ----- #

TASK_COLUMNS_SETTINGS: dict[str, dict[str, str | bool]] = {
    "OWNER": {"justify": "left", "header_style": "bold", "style": "bold", "no_wrap": True},
    "BATCH_NAME": {"justify": "center", "header_style": "magenta", "style": "magenta", "no_wrap": True},
    "SUBMITTED": {
        "justify": "center",
        "header_style": "medium_turquoise",
        "style": "medium_turquoise",
        "no_wrap": True,
    },
    "DONE": {"justify": "right", "header_style": "bold green3", "style": "bold green3", "no_wrap": True},
    "RUNNING": {
        "justify": "right",
        "header_style": "bold cornflower_blue",
        "style": "bold cornflower_blue",
        "no_wrap": True,
    },
    "IDLE": {"justify": "right", "header_style": "bold dark_orange3", "style": "bold dark_orange3", "no_wrap": True},
    "TOTAL": {"justify": "right", "style": "bold", "no_wrap": True},
    "JOB_IDS": {"justify": "right", "no_wrap": True},
}

CLUSTER_COLUMNS_SETTINGS: dict[str, dict[str, str | bool]] = {
    "SOURCE": {"justify": "left", "header_style": "bold", "style": "bold", "no_wrap": True},
    "JOBS": {"justify": "right", "header_style": "bold", "style": "bold", "no_wrap": True},
    "COMPLETED": {"justify": "right", "header_style": "bold green3", "style": "bold green3", "no_wrap": True},
    "RUNNING": {
        "justify": "right",
        "header_style": "bold cornflower_blue",
        "style": "bold cornflower_blue",
        "no_wrap": True,
    },
    "IDLE": {"justify": "right", "header_style": "bold dark_orange3", "style": "bold dark_orange3", "no_wrap": True},
    "HELD": {"justify": "right", "header_style": "bold gold1", "style": "bold gold1", "no_wrap": True},
    "SUSPENDED": {"justify": "right", "header_style": "bold slate_blue1", "style": "bold slate_blue1", "no_wrap": True},
    "REMOVED": {"justify": "right", "header_style": "bold red3", "style": "bold red3", "no_wrap": True},
}

# ----- Exceptions ----- #


class SchedulerInformationParseError(ValueError):
    """Raised when scheduler information line cannot be parsed properly."""

    def __init__(self, line: str) -> None:
        errmsg = f"Could not extract scheduler information from HTCondor output: {line!r}"
        super().__init__(errmsg)


class ClusterSummaryParseError(ValueError):
    """Raised when cluster summary line cannot be parsed properly."""

    def __init__(self, line: str) -> None:
        errmsg = f"Could not extract cluster summary information from HTCondor output: {line!r}"
        super().__init__(errmsg)


class CondorQError(ChildProcessError):
    """Raised when executing the 'condor_q' command fails."""

    def __init__(self) -> None:
        errmsg = "Checking htcondor status (condor_q) failed"
        super().__init__(errmsg)


# ----- HTCondor Querying / Processing ----- #


def query_condor_q() -> str:
    """
    .. versionadded:: 0.9.0

    Returns a decoded string with the result of the
    ``condor_q`` command, to get the status of the
    caller' jobs.

    Returns
    -------
    str
        The utf-8 decoded string returned by the
        ``condor_q`` command.

    Raises
    ------
    CondorQError
        If the ``condor_q`` command fails for any reason.
    """
    return_code, raw_result = CommandLine.run("condor_q")
    condor_status = raw_result.decode().strip()
    if return_code == 0:
        return condor_status

    # An issue occured, let's raise
    raise CondorQError()


def read_condor_q(report: str) -> tuple[list[HTCTaskSummary], ClusterSummary]:
    """
    .. versionadded:: 0.9.0

    Splits information from different parts of the ``condor_q``
    command's output into one clean, validated data structures.

    Parameters
    ----------
    report : str
        The utf-8 decoded string returned by the ``condor_q``
        command, as returned by `query_condor_q` .

    Returns
    -------
    tuple[list[HTCTaskSummary], ClusterSummary]
        A tuple with two elements. The first element is a list of
        each task summary given by ``condor_q``, as a validated
        `~.models.htc.HTCTaskSummary`. The second element is a
        validated `~.models.htc.ClusterSummary` object with the
        scheduler identification and summaries of the user as well
        as all users' statistics on this scheduler cluster.

    Example
    -------
        .. code-block:: python

            condor_q_output = get_the_string_as_you_wish(...)
            tasks, cluster = read_condor_q(condor_q_output)
    """
    tasks: list[HTCTaskSummary] = []
    next_line_is_task_report = False

    for line in report.splitlines():
        if line.startswith("-- Schedd:"):  # extract scheduler information
            scheduler_id = _process_scheduler_information_line(line)

        elif line.startswith("OWNER"):  # headers line before we get task reports
            next_line_is_task_report = True

        elif next_line_is_task_report:  # extract task report information
            if line not in ("\n", ""):
                tasks.append(_process_task_summary_line(line))
            else:  # an empty line denotes the end of the task report(s)
                next_line_is_task_report = False

        else:  # extract cluster information, only 3 lines here
            # Try to see if we get the owner from the tasks
            querying_owner: str | None = tasks[0].owner if tasks else None
            if "query" in line:  # first line
                query_summary: BaseSummary = _process_cluster_summary_line(line, "query")
            elif "all users" in line:  # last line
                full_summary: BaseSummary = _process_cluster_summary_line(line, "all users")
            elif line not in ("\n", ""):  # user line, whoever the user is (e.g. me, fesoubel)
                # If there were no tasks, we provide None and let the function default to
                # a wildcard in the regex which will match anything up to the colon
                owner_summary: BaseSummary = _process_cluster_summary_line(line, querying_owner)

    cluster_summary = ClusterSummary(
        scheduler_id=scheduler_id, query=query_summary, user=owner_summary, cluster=full_summary
    )
    return tasks, cluster_summary


# ----- Output Formating ----- #


def _make_tasks_table(tasks: list[HTCTaskSummary]) -> Table:
    """
    Takes the list of `~.models.htc.HTCTaskSummary` models
    as returned by `read_condor_q` and from the information
    within creates a `rich.table.Table`. Each row of the
    table represents one `HTCTaskSummary` from the input.
    The returned object is ready to be displayed by `rich`.

    Parameters
    ----------
    tasks : list[HTCTaskSummary]
        A list of `~.models.htc.HTCTaskSummary` models, as
        parsed from the output of the ``condor_q`` command.

    Returns
    -------
    rich.table.Table
        A `rich.table.Table` object with the tasks information
        formatted and ready to be displayed by `rich`.
    """
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


def _make_cluster_table(owner_name: str, cluster: ClusterSummary) -> Table:
    """
    Takes a `~.models.htc.ClusterSummary` model as returned by
    `read_condor_q` and from the information within creates a
    `rich.table.Table`. The returned object is ready to be
    displayed by `rich`.

    Parameters
    ----------
    owner_name : str
        The name of the user who queried the HTCondor queue.
    cluster : ClusterSummary
        A `~.models.htc.ClusterSummary` model, as parsed from
        the output of the ``condor_q`` command.

    Returns
    -------
    rich.table.Table
        A `rich.table.Table` object with the cluster information
        formatted and ready to be displayed by `rich`.
    """
    table = _default_cluster_table()
    for i, source in enumerate(["query", "user", "cluster"]):
        table.add_row(
            "Query" if i == 0 else ("All Users" if i == 2 else owner_name),  # noqa: PLR2004
            str(cluster.model_dump()[source]["jobs"]),
            str(cluster.model_dump()[source]["completed"]),
            str(cluster.model_dump()[source]["running"]),
            str(cluster.model_dump()[source]["idle"]),
            str(cluster.model_dump()[source]["held"]),
            str(cluster.model_dump()[source]["suspended"]),
            str(cluster.model_dump()[source]["removed"]),
        )
    return table


# ----- Helpers ----- #


def _process_scheduler_information_line(line: str) -> str:
    """
    Extract only the 'Schedd: <cluster>.cern.ch' part
    of the scheduler information line.

    Parameters
    ----------
    line : str
        The line containing the scheduler information.

    Returns
    -------
    str
        The scheduler name extracted from the input line.

    Raises
    ------
    SchedulerInformationError
        If the scheduler information could not be extracted
        from the input line. This typically happens when no
        jobs are present in the HTCondor queue and condor_q
        returns empty lines.
    """
    match: re.Match[str] | None = _SCHEDD_RE.search(line)
    if match is None:
        raise SchedulerInformationParseError(line)
    return match["cluster"]


def _process_task_summary_line(line: str) -> HTCTaskSummary:
    """
    Extract the various information in a task summary line,
    validated and returned as an `HTCTaskSummary` object.

    Parameters
    ----------
    line : str
        The line containing the task summary information.

    Returns
    -------
    pyhdtoolkit.models.htc.HTCTaskSummary
        The task summary information as a validated
        `~.models.htc.HTCTaskSummary` object.
    """
    line_elements = line.split()
    return HTCTaskSummary(
        owner=line_elements[0],
        batch_name=int(line_elements[2]),  # line_elements[1] is the 'ID:' part, we don't need it
        submitted=pendulum.from_format(
            f"{line_elements[3]} {line_elements[4]}", fmt="MM/D HH:mm", tz="Europe/Paris"
        ),  # Geneva timezone is Paris timezone,
        done=line_elements[5],
        run=line_elements[6],
        idle=line_elements[7],
        total=int(line_elements[8]),
        job_ids=line_elements[9],
    )


def _process_cluster_summary_line(line: str, query: str | None = None) -> BaseSummary:
    r"""
    Extract the various information in a cluster summary line,
    validated and returned as a `~.models.htc.BaseSummary`.

    Note
    ----
        A typical block to parse lines from looks like this:

        .. code-block:: bash

            Total for query: 63 jobs; 0 completed, 0 removed, 1 idle, 62 running, 0 held, 0 suspended
            Total for fesoubel: 63 jobs; 0 completed, 0 removed, 1 idle, 62 running, 0 held, 0 suspended
            Total for all users: 7279 jobs; 1 completed, 1 removed, 3351 idle, 3724 running, 202 held, 0 suspended

        Beware that if no jobs are running for the querying user (calling
        'condor_q') the calling function (read_condor_q) will not have been
        able to determine the `owner` info from the tasks summaries. In this
        case, the line for the user (i.e. fesoubel in the example above) will
        need to be parsed with a wildcard instead of the actual user name. For
        this we use r"[^:]+" which will match anything up to the colon.

    Parameters
    ----------
    line : str
        The line containing the cluster summary information.
    query : str, optional
        The name of the user who queried the HTCondor queue.

    Returns
    -------
    pyhdtoolkit.models.htc.BaseSummary
        The cluster summary information as a validated
        `~.models.htc.BaseSummary` object.
    """
    # We prepare the regex pattern with the proper query - if no query is given
    # by caller (i.e. read_condor_q), we use a wildcard (see docstring note)
    query_pattern: str = re.escape(query) if query is not None else r"[^:]+"
    pattern: re.Pattern[str] = re.compile(_CLUSTER_SUMMARY_RE_TEMPLATE.format(query=query_pattern))

    # Parse and search the line, exit early if no match
    match: re.Match[str] | None = pattern.search(line)
    if match is None:
        raise ClusterSummaryParseError(line)

    return BaseSummary(
        jobs=int(match["jobs"]),
        completed=int(match["completed"]),
        removed=int(match["removed"]),
        idle=int(match["idle"]),
        running=int(match["running"]),
        held=int(match["held"]),
        suspended=int(match["suspended"]),
    )


def _default_tasks_table() -> Table:
    """
    Create the default structure for the Tasks
    Table, hard coded columns and no rows added.

    Returns
    -------
    rich.table.Table
        A `rich.table.Table` object with the
        default structure for the Tasks Table.
    """
    table = Table(width=120, box=box.SIMPLE_HEAVY)
    for header, header_col_settings in TASK_COLUMNS_SETTINGS.items():
        table.add_column(header, **header_col_settings)  # ty:ignore[invalid-argument-type]
    return table


def _default_cluster_table() -> Table:
    """
    Create the default structure for the Cluster
    Table, hard coded columns and no rows added.

    Returns
    -------
    rich.table.Table
        A `rich.table.Table` object with the
        default structure for the Cluster Table.
    """
    table = Table(width=120, box=box.HORIZONTALS)
    for header, header_col_settings in CLUSTER_COLUMNS_SETTINGS.items():
        table.add_column(header, **header_col_settings)  # ty:ignore[invalid-argument-type]
    return table
