"""
.. _script-htcmonitor:

A script to query the HTCondor queue and display
the status nicely with rich.

Note
----
    This module is meant to be called as a script. Utility
    functionality is provided in `pyhdtoolkit.utils.htcondor`.
    Some of it is made public API and one should be able to
    build a different monitor script from the functions there.



TODO: document more this script.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from typer import Option, Typer

from pyhdtoolkit.utils.htcondor import (
    ClusterSummaryParseError,
    CondorQError,
    SchedulerInformationParseError,
    _make_cluster_table,
    _make_tasks_table,
    query_condor_q,
    read_condor_q,
)
from pyhdtoolkit.utils.logging import config_logger

if TYPE_CHECKING:
    from rich.progress import TaskID
    from rich.table import Table


# ----- CLI App ----- #

app: Typer = Typer(help="A script to monitor HTCondor queue status.")

# ----- Bread and Butter ----- #


def generate_tables_renderable() -> Group:
    """
    .. versionadded:: 0.9.0

    Function called to update the live display,
    fetches data from htcondor via 'condor_q',
    processes the response into tables and returns
    a `rich.console.Group` with Panels for both
    the tasks and cluster information.

    Returns
    -------
    rich.console.Group
        A `rich.console.Group` object with two
        `rich.panel.Panel` objects inside, one
        holding the tasks table and the other
        holding the cluster information.
    """
    condor_string: str = query_condor_q()
    user_tasks, cluster_info = read_condor_q(condor_string)
    owner: str = user_tasks[0].owner if user_tasks else "User"

    tasks_table: Table = _make_tasks_table(user_tasks)
    cluster_table: Table = _make_cluster_table(owner, cluster_info)
    return Group(
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


# ----- Progress + Layout helpers ----- #


def make_layout(progress: Progress, tables: Group, message: str = "") -> Layout:
    """
    Create the main UI layout with the progress bar above the table,
    dynamically matching the table width (or console width if resized).

    Parameters
    ----------
    progress : Progress
        The Rich Progress instance for the countdown.
    table_renderable : Group
        The Group containing the task and cluster panels.
    """
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=2),  # status message
        Layout(progress, size=2),  # Progress bar
        Layout(tables, ratio=1),  # Table panels
    )

    if message:
        layout["header"].update(Align.center(message))

    return layout


# ----- Entrypoint ----- #


@app.command()
def main(
    wait: int = Option(300, "-w", "--wait", min=1, help="Seconds to wait between calls to `condor_q`."),
    refresh: float = Option(1, "-r", "--refresh", min=0.1, help="Table display refreshes per second."),
    log_level: str = Option("warning", help="Console logging level. Can be 'debug', 'info', 'warning' and 'error'."),
):
    """
    Parse the HTCondor queue and display
    the status in a nice way using `rich`.
    """
    # Configure our logger and level (only for functions, not rich Console)
    config_logger(level=log_level)
    sleep_interval = float(max(0.1, 1 / refresh))

    # Create re-usable console and progress bar
    console: Console = Console()
    progress: Progress = Progress(
        TextColumn("Time to next HTCondor query: "),
        BarColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    task_id: TaskID = progress.add_task("waiting", total=wait)

    # Use an auto-updating live display. The display builds itself
    # from the created layout we will pass to it.
    with Live(console=console, refresh_per_second=refresh) as live:
        msg = f"[bold]Querying HTCondor queue every {wait:d} seconds (table display refreshes {refresh:.2f} times/second)[/bold]"

        while True:
            try:
                # Once per cycle, query HTCondor the process its output
                # and generate the table to be displayed
                tables: Group = generate_tables_renderable()

                # Reset the progress bar (we just queried HTCondor)
                progress.reset(task_id)
                progress.update(task_id, total=wait, completed=0)

                # We start rendering our layout with progress + table
                layout: Layout = make_layout(progress, tables, message=msg)
                live.update(layout)

                # Now we need to update the progress bar until
                # we have waited long enough for the next query
                start: float = time.monotonic()
                while not progress.finished:
                    elapsed: float = time.monotonic() - start
                    progress.update(task_id, completed=min(elapsed, wait))

                    # Refresh the live display for the progress bar and sleep
                    live.refresh()
                    time.sleep(sleep_interval)

                # This is to force a clean 100% completion render before resetting
                progress.update(task_id, completed=wait)
                live.refresh()

            # In case the 'condor_q' command failed
            except CondorQError as err:
                live.console.log(f"[red]Error querying HTCondor:[/red]\n {err}")
                live.console.print_exception()
                break  # exits

            # In case parsing the output of 'condor_q' failed
            except (ClusterSummaryParseError, SchedulerInformationParseError) as err:
                live.console.log(f"[red]Error parsing HTCondor output:[/red]\n {err}")
                live.console.print_exception()
                break  # exits

            # Allow user to exit cleanly
            except KeyboardInterrupt:
                live.console.log("Exiting Program")
                break  # exits


# ----- Script Mode ----- #

if __name__ == "__main__":
    app()
