"""
.. _utils-htcondor:

HTCondor Monitoring Utilities
-----------------------------

A script to query the HTCondor queue and display
the status nicely with rich.

Note
----
    This module is meant to be called as a script. Utility
    functionality is provided in `pyhdtoolkit.utils.htcondor`.
    Some of it is made public API and one should be able to
    build a different monitor script from the functions there.
"""

import time
from typing import TYPE_CHECKING

from loguru import logger
from rich.console import Group
from rich.live import Live
from rich.panel import Panel

from pyhdtoolkit.utils.htcondor import _make_cluster_table, _make_tasks_table, query_condor_q, read_condor_q
from pyhdtoolkit.utils.logging import config_logger

if TYPE_CHECKING:
    from rich.table import Table

config_logger(level="ERROR")

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


@logger.catch()
def main():
    with Live(generate_renderable(), refresh_per_second=0.25) as live:
        live.console.log("Querying HTCondor Queue - Refreshed Every 5 Minutes\n")
        while True:
            try:
                live.update(generate_renderable())
                time.sleep(300)
            except KeyboardInterrupt:
                live.console.log("Exiting Program")
                break


# ----- Script Mode ----- #

if __name__ == "__main__":
    main()
