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

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
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
    from rich.table import Table


# ----- CLI App ----- #

app: Typer = Typer(help="A script to monitor HTCondor queue status.")

# ----- Bread and Butter ----- #


def generate_renderable() -> Group:
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


# ----- Entrypoint ----- #


@app.command()
def main(
    wait: int = Option(300, "-w", "--wait", help="Seconds to wait between calls to `condor_q`."),
    refresh: float = Option(0.25, "-r", "--refresh", help="Display refreshes per second (higher means more CPU usage)."),
    log_level: str = Option("warning", help="Console logging level. Can be 'DEBUG', 'INFO', 'WARNING' and 'ERROR'."),
):
    """
    Parse the HTCondor queue and display
    the status in a nice way using `rich`.
    """
    # Configure our logger and level (only for functions, not rich Console)
    config_logger(level=log_level)

    # Directly use Live to update the display. The display build itself
    # is defined in the function above and takes care of the query etc.
    with Live(generate_renderable(), refresh_per_second=refresh) as live:
        live.console.log(f"Querying HTCondor Queue - Every {wait:d} Seconds\n")
        live.console.log(f"Display refresh rate: {refresh:.2f} per second")
        while True:
            try:  # query HTCondor queue, process, update display
                live.update(generate_renderable())
                time.sleep(wait)
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
