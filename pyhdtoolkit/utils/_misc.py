"""
Module utils.misc
-----------------

Private module that provides miscellaneous personnal utility functions.
"""
import shlex

from multiprocessing import cpu_count
from pathlib import Path
from typing import List

from loguru import logger

# ----- Constants ----- #

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
    """
    Returns Path objects to the opticsfiles from the appropriate location depending on where the program runs,
    either 'afs' or 'local'. Only the normal configuration opticsfiles are returned, so those ending with a
    special suffix such as `_ctpps1` are ignored.

    Raises:
        ValueError: If the program is running in an unknown location (neither 'afs' nor 'local').

    Returns:
        List[Path]: List of Path objects to the opticsfiles.
    """
    if RUN_LOCATION not in ("afs", "local"):
        logger.error("Unknown runtime location, exiting")
        raise ValueError("The 'RUN_LOCATION' variable should be either 'afs' or 'local'.")

    optics_dir: Path = PATHS["optics2018"] / "PROTON" if RUN_LOCATION == "afs" else PATHS["local"] / "optics"
    optics_files = list(optics_dir.iterdir())
    desired_files = [path for path in optics_files if len(path.suffix) <= 3 and path.name.startswith("opticsfile")]
    return sorted(desired_files, key=lambda x: float(x.suffix[1:]))  # sort by the number after 'opticsfile.'


# ----- Fetching Utilities ----- #


def get_betastar_from_opticsfile(opticsfile: Path) -> float:
    """
    Parses the betastar value from the opticsfile content, which is in the first lines. This contains a check
    that ensures the betastar is the same for IP1 and IP5. The values returned are in meters.

    Args:
        opticsfile (Path): Path object to the opticsfile.

    Raises:
        AssertionError: if the betastar value for IP1 and IP5 is not the same (in both planes too).

    Returns:
        The betastar value parsed from the file.
    """
    file_lines = opticsfile.read_text().split("\n")
    ip1_x_line, ip1_y_line, ip5_x_line, ip5_y_line = [line for line in file_lines if line.startswith("bet")]
    betastar_x_ip1 = float(shlex.split(ip1_x_line)[2])
    betastar_y_ip1 = float(shlex.split(ip1_y_line)[2])
    betastar_x_ip5 = float(shlex.split(ip5_x_line)[2])
    betastar_y_ip5 = float(shlex.split(ip5_y_line)[2])
    assert betastar_x_ip1 == betastar_y_ip1 == betastar_x_ip5 == betastar_y_ip5
    return betastar_x_ip1  # doesn't matter which plane, they're all the same
