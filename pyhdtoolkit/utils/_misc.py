"""
Module utils.misc
-----------------

Private module that provides miscellaneous personnal utility functions.
"""

from multiprocessing import cpu_count
from pathlib import Path
from typing import List

from loguru import logger

CPUS = cpu_count()
HOME = str(Path.home())

# Determine if running on afs or laptop / desktop
RUN_LOCATION = (
    "afs" if "cern.ch" in HOME or "fesoubel" in HOME else ("local" if "Users" in HOME or "/home" in HOME else None)
)

PATHS = {
    "optics2018": Path("/afs/cern.ch/eng/lhc/optics/runII/2018"),
    "local": Path.home() / "cernbox" / "OMC" / "MADX_scripts" / "Local_Coupling",
    "htc_outputdir": Path("Outputdata"),
}


# ----- Path and Runtime Utilities ----- #


def fullpath(filepath: Path) -> str:
    """Necessary for AFS paths."""
    return str(filepath.absolute())


def get_opticsfiles_paths() -> List[Path]:
    """Call optics from the appropriate location depending on where the program runs, either 'afs' or 'local'."""
    if RUN_LOCATION not in ("afs", "local"):
        logger.error("Unknown runtime location, exiting")
        raise ValueError("The 'RUN_LOCATION' variable should be either 'afs' or 'local'.")

    optics_dir: Path = PATHS["optics2018"] / "PROTON" if RUN_LOCATION == "afs" else PATHS["local"] / "optics"
    optics_files = list(optics_dir.iterdir())
    desired_files = [path for path in optics_files if len(path.suffix) <= 3 and path.name.startswith("opticsfile")]
    return sorted(optics_files, key=lambda x: float(x.suffix[1:]))  # sort by the number after 'opticsfile.'


# ----- Fetching Utilities ----- #


def get_betastar_from_opticsfile(opticsfile: Path) -> float:
    """Parses the betastar value from the opticsfile content, which is in the first lines."""
    file_lines = opticsfile.read_text().split("\n")
    ip1_line, ip5_line = [
        line for line in file_lines if line.startswith("betx_")
    ]  # these are for betxstar, symmetry makes it ok
    betastar_ip1 = float(shlex.split(ip1_line)[2])
    betastar_ip5 = float(shlex.split(ip5_line)[2])
    assert betastar_ip1 == betastar_ip5
    return betastar_ip1
