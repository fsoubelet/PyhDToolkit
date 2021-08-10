"""
Module cpymadtools.tune
-----------------------

Created on 2021.04.01
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to manipulate MAD-X functionality around the tune through a cpymad.madx.Madx
object.
"""
import math
import sys

from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.collections
import matplotlib.patches
import numpy as np
import tfs

from cpymad.madx import Madx
from loguru import logger


def make_footprint_table(
    madx: Madx, sigma: float = 5, dense: bool = False, file: str = None, cleanup: bool = True, **kwargs,
) -> tfs.TfsDataFrame:
    """
    Instantiates an ensemble of particles up to the desired bunch sigma amplitude to be tracked for the
    DYNAP command, letting MAD-X infer their tunes. Particules are instantiated for different angle
    variables for each amplitude, creating an ensemble able to represent the tune footprint.

    Beware: since the `DYNAP` command makes use of tracking, your sequence needs to be sliced before calling
    this function.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        sigma (float): the maximum amplitude of the tracked particles, in bunch sigma. Defaults to 5.
        dense (bool): if set to True, an increased number of particles will be tracked. Defaults to False.
        file (str): If given, the `dynaptune` table will be exported as a TFS file with the provided name.
        cleanup (bool): If True, the `fort.69` and `lyapunov.data` files are cleared before returning the
            dynap table. Defaults to True.

	Keyword Args:
		Any keyword argument that will be transmitted to the DYNAP command in MAD-X.

    Returns:
		The resulting `dynaptune` table, as a pandas DataFrame.
    """
    logger.info(f"Initiating particules up to {sigma:d} bunch sigma to create a tune footprint table")
    small, big = 0.05, math.sqrt(1 - 0.05 ** 2)
    sigma_multiplier, angle_multiplier = 0.1, 0

    logger.debug("Initializing particles")
    madx.command.track()
    madx.command.start(fx=small, fy=small)
    while sigma_multiplier <= sigma + 1:
        angle = 15 * angle_multiplier * math.pi / 180
        if angle_multiplier == 0:
            madx.command.start(fx=sigma_multiplier * big, fy=sigma_multiplier * small)
        elif angle_multiplier == 6:
            madx.command.start(fx=sigma_multiplier * small, fy=sigma_multiplier * big)
        else:
            madx.command.start(fx=sigma_multiplier * math.cos(angle), fy=sigma_multiplier * math.sin(angle))
        angle_multiplier += 0.5
        if int(angle_multiplier) == 7:
            angle_multiplier = 0
            sigma_multiplier += 1 if not dense else 0.5

    logger.debug("Starting DYNAP tracking with initialized particles")
    try:
        madx.command.dynap(fastune=True, turns=1024, **kwargs)
        madx.command.endtrack()
    except RuntimeError as madx_crash:
        logger.error(
            "Remote MAD-X process crashed, most likely because you did not slice the sequence "
            "before running DYNAP. Restart and slice before calling this function."
        )
        raise RuntimeError("DYNAP command crashed the MAD-X process") from madx_crash

    if cleanup and sys.platform not in ("win32", "cygwin"):
        # fails on Windows due to its I/O system, since MAD-X still has "control" of the files
        try:
            logger.debug("Cleaning up DYNAP output files `fort.69` and `lyapunov.data`")
            Path("fort.69").unlink()
            Path("lyapunov.data").unlink()
        except FileNotFoundError:
            logger.error("Could not cleanup DYNAP output files, they might have not been created")

    tfs_dframe = tfs.TfsDataFrame(
        data=madx.table.dynaptune.dframe(),
        headers=dict(
            NAME="DYNAPTUNE",
            TYPE="DYNAPTUNE",
            TITLE="FOOTPRINT TABLE",
            MADX_VERSION=str(madx.version).upper(),
            ORIGIN="pyhdtoolkit.cpymadtools.tune.make_footprint_table() function",
            ANGLE=7,  # default of the function
            AMPLITUDE=sigma,
            DSIGMA=1 if not dense else 0.5,
            ANGLE_MEANING="Number of different starting angles used for each starting amplitude",
            AMPLITUDE_MEANING="Up to which bunch sigma the starting amplitudes were ramped up",
            DSIGMA_MEANING="Increment value of AMPLITUDE at each new starting amplitude",
        ),
    )
    tfs_dframe = tfs_dframe.reset_index(drop=True)

    if file:
        tfs.write(Path(file).absolute(), tfs_dframe)

    return tfs_dframe


def get_footprint_lines(dynap_dframe: tfs.TfsDataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Provided with the `TfsDataFrame` returned by `make_footprint_table()`, determines the various (Qx, Qy)
    points needed to plot the footprint data with lines representing the different amplitudes and angles
    from starting particles, and returns these in immediately plottable numpy arrays.

	WARNING: This function is some DARK MAGIC stuff I have taken out of very dusty drawers, and I cannot
	explain exactly how it works. I also do not know who wrote this initially. Results are not guaranteed
	to be correct and should be checked with a quick plot.

    Usage:
        ```python
        dynap_tfs = make_footprint_table(madx)
        qxs, qys = get_footprint_lines(dynap_tfs)
        plt.plot(qxs, qys, "o--", label="Tune Footprint from DYNAP Table")
        ```

    Args:
        dynap_dframe (tfs.TfsDataFrame): the dynap data frame returned by `make_footprint_table()`.

    Returns:
		The Qx and Qy data points to plot directly, both as numpy.ndarrays.
    """
    logger.info("Determining footprint plottable")
    logger.debug("Retrieving AMPLITUDE, ANGLE and DSIGMA data from TfsDataFrame headers")
    amplitude = dynap_dframe.headers["AMPLITUDE"]
    angle = dynap_dframe.headers["ANGLE"]
    dsigma = dynap_dframe.headers["DSIGMA"]

    tune_groups = _make_tune_groups(dynap_string_rep=_get_dynap_string_rep(dynap_dframe), dsigma=dsigma)
    footprint = _Footprint(tune_groups, amplitude, angle, dsigma)
    qxs, qys = footprint.get_plottable()
    return np.array(qxs, dtype=float), np.array(qys, dtype=float)


def get_footprint_patches(dynap_dframe: tfs.TfsDataFrame,) -> matplotlib.collections.PatchCollection:
    """
    INITIAL IMPLEMENTATION CREDITS GO TO KONSTANTINOS PARASCHOU (@kparasch).
	Provided with the `TfsDataFrame` returned by `make_footprint_table()`, computes the polygon patches
	needed to plot the footprint data, with lines representing the different amplitudes and angles
	from starting particles, and returns the `PatchCollection` with the computed polygons.

    The polygons will have blue edges, except the ones corresponding to the last starting angle particles (
    in red) and the last starting amplitude particles (in green).

	WARNING: The internal construction of polygons can be tricky, and you might need to change the `ANGLE`
	or `AMPLITUDE` values in `dynap_dframe`'s headers.

	Usage:
		```python
		fig, axis = plt.subplots()
		dynap_tfs = make_footprint_table(madx)
		footprint_polygons = get_footprint_patches(dynap_tfs)
		axis.add_collection(footprint_polygons)
		```

    Args:
		dynap_dframe (tfs.TfsDataFrame): the dynap data frame returned by `make_footprint_table()`.

    Returns:
		The `matplotlib.collections.PatchCollection` with the created polygons.
	"""
    logger.info("Determining footprint polygons")
    angle = dynap_dframe.headers["ANGLE"]
    amplitude = dynap_dframe.headers["AMPLITUDE"]

    logger.debug("Grouping tune points according to starting angles and amplitudes")
    try:
        A = np.zeros([amplitude, angle, 2])
        A[0, :, 0] = dynap_dframe["tunx"].to_numpy()[0]
        A[0, :, 1] = dynap_dframe["tuny"].to_numpy()[0]
        A[1:, :, 0] = dynap_dframe["tunx"].to_numpy()[1:].reshape(-1, angle)
        A[1:, :, 1] = dynap_dframe["tuny"].to_numpy()[1:].reshape(-1, angle)
    except ValueError as tune_grouping_error:
        logger.error(
            "Cannot group tune points according to starting angles and amplitudes. Try changing "
            "the 'AMPLITUDE' value in the provided TfsDataFrame's headers."
        )
        raise tune_grouping_error

    logger.debug("Determining polygon vertices")
    sx = A.shape[0] - 1
    sy = A.shape[1] - 1
    p1 = A[:-1, :-1, :].reshape(sx * sy, 2)[:, :]
    p2 = A[1:, :-1, :].reshape(sx * sy, 2)[:]
    p3 = A[1:, 1:, :].reshape(sx * sy, 2)[:]
    p4 = A[:-1, 1:, :].reshape(sx * sy, 2)[:]
    polygons = np.stack((p1, p2, p3, p4))  # Stack endpoints to form polygons
    polygons = np.transpose(polygons, (1, 0, 2))  # transpose polygons

    logger.debug("Creating PatchCollection of Polygons")
    patches = list(map(matplotlib.patches.Polygon, polygons))
    patch_colors = [(0, 0, 1) for _ in polygons]
    patch_colors[(sx - 1) * sy :] = [(0, 1, 0)] * sy  # differentiate first angle in green
    patch_colors[(sy - 1) :: sy] = [(1, 0, 0)] * sx  # differentiate last amplitude in red
    return matplotlib.collections.PatchCollection(patches, facecolors=[], edgecolor=patch_colors)


# ----- Arcane Private Utilities ----- #


def _get_dynap_string_rep(dynap_dframe: tfs.TfsDataFrame) -> str:
    """
    This is a weird dusty function to get a specific useful string representation from the `TfsDataFrame`
    returned by `make_footprint_table()`. This specific dataframe contains important information.

    Args:
        dynap_dframe (tfs.TfsDataFrame): the dynap data frame returned by `make_footprint_table()`.

    Returns:
		A weird string representation gathering tune points split according to the number of angles and
		amplitudes used in `make_footprint_table()`.
    """
    logger.trace("Retrieving AMPLITUDE and ANGLE data from TfsDataFrame headers")
    amplitude = dynap_dframe.headers["AMPLITUDE"]
    angle = dynap_dframe.headers["ANGLE"]
    string_rep = f"TMPNAME,{amplitude},1,<{dynap_dframe.tunx[0]};{dynap_dframe.tuny[0]}>"
    for n in range(1, amplitude):
        string_rep += f",{angle}"
        for m in range(angle):
            string_rep += f",<{dynap_dframe.tunx[1 + (n - 1) * angle + m]};{dynap_dframe.tuny[1 + (n - 1) * angle + m]}>"
    return string_rep


def _make_tune_groups(dynap_string_rep: str, dsigma: float = 1.0) -> List[List[Dict[str, float]]]:
    """
    Creates appropriate tune points groups from the arcane string representation returned by
    `_get_dynap_string_rep` based on starting amplitude and angle for each particle.

    Args:
        dynap_string_rep (str): weird string representation of the `TfsDataFrame` returned by
        `make_footprint_table()` and as given by `_get_dynap_string_rep()`.
        dsigma (float): The increment in amplitude between different starting amplitudes when starting
            particles for the `DYNAP` command in `MAD-X`. This information is in the headers of the
            `TfsDataFrame` returned by `make_footprint_table()`.

    Returns:
        A list of list of dictionaries containing horizontal and vertical tune points. The data is
        constructed such that one can access the data of a particle starting with 'amplitude' and 'angle'
        with data[amplitude][angle]["H"/"V"]. This function is only meant to be used internally by
        `get_footprint_lines()`.
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


class _Footprint:
    """More dark magic from the past here, close your eyes my friends."""

    def __init__(self, tune_groups: List[List[Dict[str, float]]], amplitude: int, angle: int, dsigma: float):
        self._tunes = tune_groups
        self._maxnangl = angle
        self._nampl = amplitude
        self._dSigma = dsigma

    def get_h_tune(self, ampl, angl):
        if len(self._tunes[ampl]) <= angl < self._maxnangl:
            return self._tunes[ampl][len(self._tunes[ampl]) - 1]["H"]
        else:
            return self._tunes[ampl][angl]["H"]

    def get_v_tune(self, ampl, angl):
        if len(self._tunes[ampl]) <= angl < self._maxnangl:
            return self._tunes[ampl][len(self._tunes[ampl]) - 1]["V"]
        else:
            return self._tunes[ampl][angl]["V"]

    def get_plottable(self) -> Tuple[List[float], List[float]]:
        qxs, qys = [], []
        for i in np.arange(0, self._nampl - 1, 2):
            for j in np.arange(self._maxnangl):
                qxs.append(self.get_h_tune(i, j))
                qys.append(self.get_v_tune(i, j))
            for j in np.arange(self._maxnangl - 1, -1, -1):
                qxs.append(self.get_h_tune(i + 1, j))
                qys.append(self.get_v_tune(i + 1, j))
        if self._nampl % 2 == 0:
            for j in np.arange(0, self._maxnangl - 1, 2):
                for i in np.arange(self._nampl - 1, -1, -1):
                    qxs.append(self.get_h_tune(i, j))
                    qys.append(self.get_v_tune(i, j))
                for i in np.arange(0, self._nampl, 1):
                    qxs.append(self.get_h_tune(i, j + 1))
                    qys.append(self.get_v_tune(i, j + 1))
            if self._maxnangl % 2 != 0:
                for i in np.arange(self._nampl - 1, -1, -1):
                    qxs.append(self.get_h_tune(i, self._maxnangl - 1))
                    qys.append(self.get_v_tune(i, self._maxnangl - 1))
                qxs.append(self.get_h_tune(0, self._maxnangl - 2))
                qys.append(self.get_v_tune(0, self._maxnangl - 2))
        else:
            for j in np.arange(self._maxnangl):
                qxs.append(self.get_h_tune(self._nampl - 1, j))
                qys.append(self.get_v_tune(self._nampl - 1, j))
            for j in np.arange(self._maxnangl - 1, -1, -2):
                for i in np.arange(self._nampl - 1, -1, -1):
                    qxs.append(self.get_h_tune(i, j))
                    qys.append(self.get_v_tune(i, j))
                for i in np.arange(0, self._nampl, 1):
                    qxs.append(self.get_h_tune(i, j - 1))
                    qys.append(self.get_v_tune(i, j - 1))
        return qxs, qys
