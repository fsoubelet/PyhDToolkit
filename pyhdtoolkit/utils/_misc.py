"""
.. _utils-misc:

Miscellanous Personnal Utilities
--------------------------------

Private module that provides miscellaneous personnal utility functions.

.. warning::
    The functions in here are intented for personal use, and will most likely 
    **not** work on other people's machines.
"""
import shlex

from multiprocessing import cpu_count
from pathlib import Path
from typing import List

import cpymad

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit import __version__
from pyhdtoolkit.cpymadtools import lhc

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
    """Returns the full string path to the provided *filepath*, which is necessary for ``AFS`` paths."""
    return str(filepath.absolute())


def get_opticsfiles_paths() -> List[Path]:
    """
    Returns `pathlib.Path` objects to the **opticsfiles** from the appropriate location,
    depending on where the program is running, either on ``AFS`` or locally.

    .. note::
        Only the "normal" configuration **opticsfiles** are returned, so those ending with
        a special suffix such as **_ctpps1** are ignored.

    Returns:
        A `list` of `~pathlib.Path` objects to the opticsfiles.

    Raises:
        ValueError: If the program is running in an unknown location (neither `afs` nor `local`).
    """
    if RUN_LOCATION not in ("afs", "local"):
        logger.error("Unknown runtime location, exiting")
        raise ValueError("The 'RUN_LOCATION' variable should be either 'afs' or 'local'.")

    optics_dir: Path = PATHS["optics2018"] / "PROTON" if RUN_LOCATION == "afs" else PATHS["local"] / "optics"
    optics_files = list(optics_dir.iterdir())
    desired_files = [path for path in optics_files if len(path.suffix) <= 3 and path.name.startswith("opticsfile")]
    return sorted(desired_files, key=lambda x: float(x.suffix[1:]))  # sort by the number after 'opticsfile.'


def log_runtime_versions() -> None:
    """Issues a ``CRITICAL``-level log stating the runtime versions of both `~pyhdtoolkit`, `cpymad` and ``MAD-X``."""
    with Madx(stdout=False) as mad:
        logger.critical(f"Using: pyhdtoolkit {__version__} | cpymad {cpymad.__version__}  | {mad.version}")


# ----- MAD-X Setup Utilities ----- #


def call_lhc_sequence_and_optics(madx: Madx, opticsfile: str = "opticsfile.22") -> None:
    """
    Issues a ``CALL`` to the ``LHC`` sequence and the desired opticsfile, from the appropriate
    location (either on ``AFS`` or locally), based on the runtime location of the code.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        opticsfile (str): name of the optics file to call. Defaults to **opticsfile.22**, which
            holds ``LHC`` collisions optics configuration (`beta*_IP1/2/5/8=  0.300/10.000/0.300/3.000 ;
            ! Telescopic squeeze (with Q6@300A)`).

    Raises:
        ValueError: If the program is running in an unknown location  (neither `afs` nor `local`), and the
            files cannot be found in the expected directories.
    """
    logger.debug("Calling optics")
    if RUN_LOCATION == "afs":
        madx.call(fullpath(PATHS["optics2018"] / "lhc_as-built.seq"))
        madx.call(fullpath(PATHS["optics2018"] / "PROTON" / opticsfile))
    elif RUN_LOCATION == "local":
        madx.call(fullpath(PATHS["local"] / "sequences" / "lhc_as-built.seq"))
        madx.call(fullpath(PATHS["local"] / "optics" / opticsfile))
    else:
        logger.error("Unknown runtime location, exiting")
        raise ValueError("The 'RUN_LOCATION' variable should be either 'afs' or 'local'.")


def prepare_lhc_setup(opticsfile: str = "opticsfile.22", stdout: bool = False, stderr: bool = False, **kwargs) -> Madx:
    """
    Returns a prepared default ``LHC`` setup for the given *opticsfile*. Both beams are made with a default Run III
    configuration, and the ``lhcb1`` sequence is re-cycled from ``MSIA.EXIT.B1`` as in the ``OMC`` model_creator, and
    then ``USE``-d. Specific variable settings can be given as keyword arguments.

    .. important::
        Matching is **not** performed by this function and should be taken care of by the user, but the working point
        should be set by the definitions in the *opticsfile*. Beware that passing specific variables as keyword arguments
        might change that working point.

    Args:
        opticsfile (str): name of the optics file to be used. Defaults to **opticsfile.22**.
        **kwargs: any keyword argument pair will be used to update the ``MAD-X`` globals.

    Returns:
        An instanciated `~cpymad.madx.Madx` object with the required configuration.
    """
    madx = Madx(stdout=stdout, stderr=stderr)
    madx.option(echo=False, warn=False)
    call_lhc_sequence_and_optics(madx, opticsfile)
    lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
    lhc.make_lhc_beams(madx, energy=7000, emittance=3.75e-6)
    madx.command.use(sequence="lhcb1")
    madx.globals.update(kwargs)
    return madx


# ----- Fetching Utilities ----- #


def get_betastar_from_opticsfile(opticsfile: Path) -> float:
    """
    Parses the :math:`\\beta^{*}` value from the *opticsfile* content,
    which is in the first lines. This contains a check that ensures the betastar
    is the same for IP1 and IP5. The values returned are in meters.

    Args:
        opticsfile (Path): `pathlib.Path` object to the optics file.

    Returns:
        The :math:`\\beta^{*}` value parsed from the file.

    Raises:
        AssertionError: if the :math:`\\beta^{*}` value for IP1 and IP5 is not
            the same (in both planes too).
    """
    file_lines = opticsfile.read_text().split("\n")
    ip1_x_line, ip1_y_line, ip5_x_line, ip5_y_line = [line for line in file_lines if line.startswith("bet")]
    betastar_x_ip1 = float(shlex.split(ip1_x_line)[2])
    betastar_y_ip1 = float(shlex.split(ip1_y_line)[2])
    betastar_x_ip5 = float(shlex.split(ip5_x_line)[2])
    betastar_y_ip5 = float(shlex.split(ip5_y_line)[2])
    assert betastar_x_ip1 == betastar_y_ip1 == betastar_x_ip5 == betastar_y_ip5
    return betastar_x_ip1  # doesn't matter which plane, they're all the same
