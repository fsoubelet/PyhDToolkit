import time

from loguru import logger
from rich.console import Group
from rich.live import Live
from rich.panel import Panel

from pyhdtoolkit.utils.htc_monitor import _make_cluster_table, _make_tasks_table, query_condor_q, read_condor_q
from pyhdtoolkit.utils.logging import config_logger

config_logger(level="ERROR")

@logger.catch()
def main():
    def generate_renderable() -> Group:
        """
        .. versionadded:: 0.9.0

        Function called to update the live display,
        fetches data from htcondor, does the processing
        and returns a Group with both Panels.

        Returns
        -------
        rich.console.Group
            A `rich.console.Group` object with two
            `rich.panel.Panel` objects inside, one
            holding the tasks table and the other
            holding the cluster information.
        """
        condor_string = query_condor_q()
        user_tasks, cluster_info = read_condor_q(condor_string)
        owner = user_tasks[0].owner if user_tasks else "User"

        tasks_table = _make_tasks_table(user_tasks)
        cluster_table = _make_cluster_table(owner, cluster_info)
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

    with Live(generate_renderable(), refresh_per_second=0.25) as live:
        live.console.log("Querying HTCondor Queue - Refreshed Every 5 Minutes\n")
        while True:
            try:
                live.update(generate_renderable())
                time.sleep(300)
            except KeyboardInterrupt:
                live.console.log("Exiting Program")
                break


if __name__ == "__main__":
    main()
