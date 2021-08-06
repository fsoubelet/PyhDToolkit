"""
TODO: create module docstring
"""
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from loguru import logger
from tfs import TfsDataFrame


def get_footprint_lines(dynap_dframe: TfsDataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Provided with the `TfsDataFrame` returned by `pyhdtoolkit.cpymadtools.tune.make_footprint_table()`,
    determines the various (Qx, Qy) points groups needed to plot the footprint data with lines representing
    the different amplitudes and angles from starting particles, and return these in plottable numpy arrays.

	WARNING: This function is some DARK MAGIC stuff I have taken out of very dusty drawers, and I cannot
	explain exactly how it works. I also do not know who wrote this initially.

    Args:
        dynap_dframe (TfsDataFrame): the dynap data frame returned by `make_footprint_table()`.

    Returns:
		A tuple of the Qx and Qy data points to plot directly.
    """
    logger.debug("Retrieving AMPLITUDE, ANGLE and DSIGMA data from TfsDataFrame headers")
    amplitude = dynap_dframe.headers["AMPLITUDE"]
    angle = dynap_dframe.headers["ANGLE"]
    dsigma = dynap_dframe.headers["DSIGMA"]
    _tunes = _make_tune_groups(dynap_string_rep=_get_dynap_string_rep(dynap_dframe), dsigma=dsigma)

    lines = [[], []]
    for i in np.arange(0, self._nampl - 1, 2):
        for j in np.arange(self._maxnangl):
            lines[0].append(self.getHTune(i, j))
            lines[1].append(self.getVTune(i, j))
        for j in np.arange(self._maxnangl - 1, -1, -1):
            lines[0].append(self.getHTune(i + 1, j))
            lines[1].append(self.getVTune(i + 1, j))
    if self._nampl % 2 == 0:
        for j in np.arange(0, self._maxnangl - 1, 2):
            for i in np.arange(self._nampl - 1, -1, -1):
                lines[0].append(self.getHTune(i, j))
                lines[1].append(self.getVTune(i, j))
            for i in np.arange(0, self._nampl, 1):
                lines[0].append(self.getHTune(i, j + 1))
                lines[1].append(self.getVTune(i, j + 1))
        if self._maxnangl % 2 != 0:
            for i in np.arange(self._nampl - 1, -1, -1):
                lines[0].append(self.getHTune(i, self._maxnangl - 1))
                lines[1].append(self.getVTune(i, self._maxnangl - 1))
            lines[0].append(self.getHTune(0, self._maxnangl - 2))
            lines[1].append(self.getVTune(0, self._maxnangl - 2))
    else:
        for j in np.arange(self._maxnangl):
            lines[0].append(self.getHTune(self._nampl - 1, j))
            lines[1].append(self.getVTune(self._nampl - 1, j))
        for j in np.arange(self._maxnangl - 1, -1, -2):
            for i in np.arange(self._nampl - 1, -1, -1):
                lines[0].append(self.getHTune(i, j))
                lines[1].append(self.getVTune(i, j))
            for i in np.arange(0, self._nampl, 1):
                lines[0].append(self.getHTune(i, j - 1))
                lines[1].append(self.getVTune(i, j - 1))
    return np.array(lines[0], dtype=float), np.array(lines[1], dtype=float)


# ----- Arcane Private Utilities ----- #


def _get_dynap_string_rep(dynap_dframe: TfsDataFrame) -> str:
    """
    This is a weird dusty function to get a specific useful string representation from the `TfsDataFrame`
    returned by `pyhdtoolkit.cpymadtools.tune.make_footprint_table()`. This specific dataframe contains
    important information.

    Args:
        dynap_dframe (TfsDataFrame): the dynap data frame returned by `make_footprint_table()`.

    Returns:
		A weird string representation gathering tune points split according to the number of angles and
		amplitudes used in `make_footprint_table()`.
    """
    logger.trace("Retrieving AMPLITUDE and ANGLE data from TfsDataFrame headers")
    amplitude = dynap_dframe.headers["AMPLITUDE"]
    angle = dynap_dframe.headers["ANGLE"]
    string_rep = (
        "TMPNAME,"
        + str(amplitude)
        + ",1,<"
        + str(dynap_dframe.tunx[0])
        + ";"
        + str(dynap_dframe.tuny[0])
        + ">"
    )
    for n in range(1, amplitude):
        string_rep = string_rep + "," + str(angle)
        for m in range(angle):
            string_rep = (
                string_rep
                + ",<"
                + str(dynap_dframe.tunx[1 + (n - 1) * angle + m])
                + ";"
                + str(dynap_dframe.tuny[1 + (n - 1) * angle + m])
                + ">"
            )
    return string_rep


def _make_tune_groups(dynap_string_rep: str, dsigma: float = 1.0) -> List[List[Dict[str, float]]]:
    """
    Creates appropriate tune points groups from the arcane string representation returned by
    `_get_dynap_string_rep` based on starting amplitude and angle for each particle.

    Args:
        dynap_string_rep (str): weird string representation of the `TfsDataFrame` returned by
        `pyhdtoolkit.cpymadtools.tune.make_footprint_table()` as given by `_get_dynap_string_rep()`.
        dsigma (float): The increment in amplitude between different starting amplitudes when starting
            particles for the `DYNAP` command in `MAD-X`. This information is in the headers of the
            `TfsDataFrame` returned by `pyhdtoolkit.cpymadtools.tune.make_footprint_table()`.

    Returns:
        A list of list of dictionaries containing horizontal and vertical tune points. The data is
        constructed such that one can access the data of a particle starting with 'amplitude' and 'angle'
        with data[amplitude][angle]["H"/"V"]. This function is only meant to be used internally by
        `get_footprint_lines()`
    """
    logger.debug("Constructing tune points groups based on starting amplitudes and angles")
    tune_groups = []
    items = dynap_string_rep.strip().split(",")
    amplitude = int(items[1])
    current = 2
    for i in np.arange(amplitude):
        tune_groups.append([])
        angle = int(items[current])
        current = current + 1
        for j in np.arange(angle):
            tune_groups[i].append([])
            tune_string = items[current].lstrip("<").rstrip(">").split(";")
            tune_groups[i][j] = {"H": float(tune_string[0]), "V": float(tune_string[1])}
            current = current + 1
    return tune_groups
