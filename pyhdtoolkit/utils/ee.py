from rich import pretty, traceback
from rich.console import Console, Measurement
from rich.table import Table

from pyhdtoolkit.utils.htc_monitor import EXAMPLE, make_tasks_table, read_condor_q

pretty.install()
traceback.install(show_locals=True)

tasks, cluster = read_condor_q(EXAMPLE)
tasks_table = make_tasks_table(tasks, cluster)

console = Console()
console.print(tasks_table)
