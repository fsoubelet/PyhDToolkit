"""
Module optics.amplitude_detuning
--------------------------------

Created on 2020.08.13
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 module implementing classes for amplitude detuning calculations after loading
twiss output files from MAD.

This module is a heavy refactor of initial code & formulas by @leonvanriesen

Example usage:
    hor_amp_det = HorizontalAmplitudeDetuning(twiss_filename="mad_twiss_output.tfs")
    hor_amp_det.d2qx_djx2()
    hor_amp_det.dqx_from_skew_quadrupoles()
"""
from pathlib import Path
from typing import Union

import numba
import numpy as np
import tfs

from loguru import logger


class HorizontalAmplitudeDetuning:
    """
    Class to compute different orders of amplitude detuning for the horizontal plane.
    """

    __slots__ = {
        "twiss_file": "PosixPath object to the twiss output tfs file",
        "twiss_df": "TfsDataFrame loaded from twiss_file",
        "qx": "Horizontal tune extracted from twiss_df",
        "qy": "Vertical tune extracted from twiss_df",
        "quadrupoles_twiss_df": "Twiss dataframe for normal quadrupoles",
        "skew_quadrupoles_twiss_df": "Twiss dataframe for skew quadrupoles",
        "sextupoles_twiss_df": "Twiss dataframe for normal sextupoles",
        "skew_sextupoles_twiss_df": "Twiss dataframe for skew sextupoles",
        "octupoles_twiss_df": "Twiss dataframe for normal octupoles",
        "skew_octupoles_twiss_df": "Twiss dataframe for skew octupoles",
    }

    def __init__(self, twiss_filename: Union[Path, str]) -> None:
        """
        Load external twiss file and extract relevant values and dataframes.

        Args:
            twiss_filename (Union[Path, str]): location to the twiss file output by MAD, in
                the tfs format, to be read by the tfs package, which accepts either a Path or
                a string.
        """
        logger.debug("Loading twiss file into memory and extracting sub-dataframes")
        self.twiss_file: Path = Path(twiss_filename)
        self.twiss_df: tfs.TfsDataFrame = tfs.read(twiss_filename)
        self.qx: float = self.twiss_df["MUX"].values[-1]
        self.qy: float = self.twiss_df["MUY"].values[-1]

        logger.trace("Extracting quadrupoles dataframe")
        self.quadrupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K1L"] != 0]
        logger.trace("Extracting skew quadrupoles dataframe")
        self.skew_quadrupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K1SL"] != 0]
        logger.trace("Extracting sextupoles dataframe")
        self.sextupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K2L"] != 0]
        logger.trace("Extracting skew sextupoles dataframe")
        self.skew_sextupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K2SL"] != 0]
        logger.trace("Extracting octupoles dataframe")
        self.octupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K3L"] != 0]
        logger.trace("Extracting skew octupoles dataframe")
        self.skew_octupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K3SL"] != 0]

    def __str__(self):
        """Simple str method indicates the name"""
        return f"HorAmpDet['{self.twiss_file.name}']"

    def __repr__(self):
        """The repr method indicates tunes"""
        return (
            f"'HorizontalAmplitudeDetuning[{self.twiss_file.absolute()}' | "
            f"Qx = {self.qx:.4f} | Qy = {self.qy:.4f}]"
        )

    def dqx_djx_from_skew_sextupoles(self) -> float:
        """
        Get the first order horizontal direct-term amplitude detuning from skew sextupoles.

        Returns:
            The first order horizontal direct-term amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_sextupoles_twiss_df["MUY"].values
        a2: np.ndarray = self.skew_sextupoles_twiss_df["K2SL"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -4
                        * betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(2, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(2, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_djx_from_sextupoles(self) -> float:
        """
        Get the first order horizontal direct-term amplitude detuning from skew sextupoles.

        Returns:
            The first order horizontal direct-term amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.sextupoles_twiss_df["MUY"].values
        b2: np.ndarray = self.sextupoles_twiss_df["K2L"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -3
                        * betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * 1
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * 1
                        * T(3, 0, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_djx(self) -> float:
        """
        Returns the first order horizontal direct-term amplitude detuning.

        Returns:
            The first order horizontal direct-term amplitude detuning.
        """
        return self.dqx_djx_from_skew_sextupoles() + self.dqx_djx_from_sextupoles()

    def d2qx_djx2_from_skew_octupoles(self) -> float:
        """
        Get the second order horizontal direct-term amplitude detuning from skew octupoles.

        Returns:
            The second order horizontal direct-term amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * (2 * 1)
                        * T(3, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        +3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * (2 * 1)
                        * T(3, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def d2qx_djx2_from_octupoles(self) -> float:
        """
        Get the second order horizontal direct-term amplitude detuning from octupoles.

        Returns:
            The second order horizontal direct-term amplitude detuning from sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -3
                        * betas_x[j]
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(4, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -24
                        * betas_x[j]
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def d2qx_djx2(self) -> float:
        """
        Returns the second order horizontal direct-term amplitude detuning.

        Returns:
            The second order horizontal direct-term amplitude detuning.
        """
        return self.d2qx_djx2_from_skew_octupoles() + self.d2qx_djx2_from_octupoles()

    def dqx_djy_from_skew_sextupoles(self) -> float:
        """
        Get the first order horizontal cross-term amplitude detuning from skew sextupoles.

        Returns:
            The first order horizontal cross-term amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_sextupoles_twiss_df["MUY"].values
        a2: np.ndarray = self.skew_sextupoles_twiss_df["K2SL"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        4
                        * betas_x[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * (2 * 1)
                        * T(2, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * (-2 * 1)
                        * T(2, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_djy_from_sextupoles(self) -> float:
        """
        Get the first order horizontal cross-term amplitude detuning from sextupoles.

        Returns:
            The first order horizontal cross-term amplitude detuning from sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.sextupoles_twiss_df["MUY"].values
        b2: np.ndarray = self.sextupoles_twiss_df["K2L"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        4
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        2
                        * betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * 1
                        * (T(1, -2, dmux, dmuy, qx, qy) - T(1, 2, dmux, dmuy, qx, qy))
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_djy(self) -> float:
        """
        Returns the first order horizontal cross-term amplitude detuning.

        Returns:
            The first order horizontal cross-term amplitude detuning.
        """
        return self.dqx_djy_from_skew_sextupoles() + self.dqx_djy_from_sextupoles()

    def d2qx_djy2_from_skew_octupoles(self) -> float:
        """
        Get the second order horizontal cross-term amplitude detuning from skew octupoles.

        Returns:
            The second order horizontal cross-term amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        9
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * 2
                        * 1
                        * (T(1, -3, dmux, dmuy, qx, qy) - T(1, 3, dmux, dmuy, qx, qy))
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 2
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 2
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def d2qx_djy2_from_octupoles(self) -> float:
        """
        Get the second order horizontal cross-term amplitude detuning from octupoles.

        Returns:
            The second order horizontal cross-term amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1)
                        * T(2, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (-2 * 1)
                        * T(2, -2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        36
                        * betas_x[j]
                        * betas_y[j]
                        * betas_y[k]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -36
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def d2qx_djy2(self) -> float:
        """
        Returns the second order horizontal cross-term amplitude detuning.

        Returns:
            The second order horizontal cross-term amplitude detuning.
        """
        return self.d2qx_djy2_from_skew_octupoles() + self.d2qx_djy2_from_octupoles()

    def d2qx_djxdjy_from_skew_octupoles(self) -> float:
        """
        Get the second order horizontal mixed-term amplitude detuning from skew octupoles.

        Returns:
            The second order horizontal mixed-term amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * (6 * 1 * 1)
                        * T(3, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        +3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * (-6 * 1 * 1)
                        * T(3, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 1
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )

                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 1
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def d2qx_djxdjy_from_octupoles(self) -> float:
        """
        Get the second order horizontal mixed-term amplitude detuning from octupoles.

        Returns:
            The second order horizontal mixed-term amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1 * 1)
                        * T(2, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1 * 1)
                        * T(2, -2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        72
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -72
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * 1
                        * 1
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def d2qx_djxdjy(self) -> float:
        """
        Returns the second order horizontal mixed-term amplitude detuning.

        Returns:
            The second order horizontal mixed-term amplitude detuning.
        """
        return self.d2qx_djxdjy_from_skew_octupoles() + self.d2qx_djxdjy_from_octupoles()

    def dqx_from_skew_quadrupoles(self) -> float:
        """
        Get the horizontal amplitude detuning from skew quadrupoles.

        Returns:
            The horizontals amplitude detuning from skew quadrupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0

        betas_x: np.ndarray = self.skew_quadrupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_quadrupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_quadrupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_quadrupoles_twiss_df["MUY"].values
        a1: np.ndarray = self.skew_quadrupoles_twiss_df["K1SL"].values

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * a1[j]
                    * a1[k]
                    * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                    * (T(1, -1, dmux, dmuy, qx, qy) - T(1, 1, dmux, dmuy, qx, qy))
                )

        return dvx / (2 * np.pi)

    def dqx_from_skew_sextupoles(self, jx: float, jy: float) -> float:
        """
        Get the horizontal amplitude detuning from skew sextupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The horizontal amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_sextupoles_twiss_df["MUY"].values
        a2: np.ndarray = self.skew_sextupoles_twiss_df["K2SL"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -4
                        * betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * jx
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        4
                        * betas_x[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * jy
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * (jx + 2 * jy)
                        * T(2, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * (jx - 2 * jy)
                        * T(2, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_from_sextupoles(self, jx: float, jy: float) -> float:
        """
        Get the horizontal amplitude detuning from sextupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The horizontal amplitude detuning from sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.sextupoles_twiss_df["MUY"].values
        b2: np.ndarray = self.sextupoles_twiss_df["K2L"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -3
                        * betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * jx
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        4
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jy
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * jx
                        * T(3, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        2
                        * betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * jy
                        * (T(1, -2, dmux, dmuy, qx, qy) - T(1, 2, dmux, dmuy, qx, qy))
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_from_skew_octupoles(self, jx: float, jy: float) -> float:
        """
        Get the horizontal amplitude detuning from skew octupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The horizontal amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        9
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * jy
                        * jy
                        * (T(1, -3, dmux, dmuy, qx, qy) - T(1, 3, dmux, dmuy, qx, qy))
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * (jx * jx + 6 * jx * jy)
                        * T(3, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        +3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * (jx * jx - 6 * jx * jy)
                        * T(3, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jy
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jy
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def dqx_from_octupoles(self, jx: float, jy: float) -> float:
        """
        Get the horizontal amplitude detuning from octupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The horizontal amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvx: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * jx * jy + jy * jy)
                        * T(2, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * jx * jy - jy * jy)
                        * T(2, -2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -3
                        * betas_x[j]
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(4, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        36
                        * betas_x[j]
                        * betas_y[j]
                        * betas_y[k]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -36
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        72
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -72
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * jx
                        * jy
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvx += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -24
                        * betas_x[j]
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )

        return dvx / (2 * np.pi)

    def dqx(self, jx: float, jy: float) -> float:
        """
        Returns the horizontal amplitude detuning.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The horizontal amplitude detuning.
        """
        return (
            self.dqx_from_skew_quadrupoles()
            + self.dqx_from_skew_sextupoles(jx, jy)
            + self.dqx_from_sextupoles(jx, jy)
            + self.dqx_from_skew_octupoles(jx, jy)
            + self.dqx_from_octupoles(jx, jy)
        )


class VerticalAmplitudeDetuning:
    """
    Class to compute different orders of amplitude detuning for the vertical plane.
    """

    __slots__ = {
        "twiss_file": "PosixPath object to the twiss output tfs file",
        "twiss_df": "TfsDataFrame loaded from twiss_file",
        "qx": "Horizontal tune extracted from twiss_df",
        "qy": "Vertical tune extracted from twiss_df",
        "quadrupoles_twiss_df": "Twiss dataframe for normal quadrupoles",
        "skew_quadrupoles_twiss_df": "Twiss dataframe for skew quadrupoles",
        "sextupoles_twiss_df": "Twiss dataframe for normal sextupoles",
        "skew_sextupoles_twiss_df": "Twiss dataframe for skew sextupoles",
        "octupoles_twiss_df": "Twiss dataframe for normal octupoles",
        "skew_octupoles_twiss_df": "Twiss dataframe for skew octupoles",
    }

    def __init__(self, twiss_filename: Union[Path, str]) -> None:
        """
        Load external twiss file and extract relevant values and dataframes.

        Args:
            twiss_filename (Union[Path, str]): location to the twiss file output by MAD,
            in the tfs format, to be read by the tfs package, which accepts either a Path or a
            string.
        """
        logger.debug("Loading twiss file into memory and extracting sub-dataframes")
        self.twiss_file: Path = Path(twiss_filename)
        self.twiss_df: tfs.TfsDataFrame = tfs.read(twiss_filename)
        self.qx: float = self.twiss_df["MUX"].values[-1]
        self.qy: float = self.twiss_df["MUY"].values[-1]

        logger.trace("Extracting quadrupoles dataframe")
        self.quadrupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K1L"] != 0]
        logger.trace("Extracting skew quadrupoles dataframe")
        self.skew_quadrupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K1SL"] != 0]
        logger.trace("Extracting sextupoles dataframe")
        self.sextupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K2L"] != 0]
        logger.trace("Extracting skew sextupoles dataframe")
        self.skew_sextupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K2SL"] != 0]
        logger.trace("Extracting octupoles dataframe")
        self.octupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K3L"] != 0]
        logger.trace("Extracting skew octupoles dataframe")
        self.skew_octupoles_twiss_df: tfs.TfsDataFrame = self.twiss_df[self.twiss_df["K3SL"] != 0]

    def __str__(self):
        """Simple str method indicates the name"""
        return f"VertAmpDet['{self.twiss_file.name}']"

    def __repr__(self):
        """The repr method indicates tunes"""
        return (
            f"'VerticalAmplitudeDetuning[{self.twiss_file.absolute()}' | "
            f"Qx = {self.qx:.4f} | Qy = {self.qy:.4f}]"
        )

    def dqy_djx_from_skew_sextupoles(self) -> float:
        """
        Get the first order vertical cross-term amplitude detuning from skew sextupoles.

        Returns:
            The first order vertical cross-term amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_sextupoles_twiss_df["MUY"].values
        a2: np.ndarray = self.skew_sextupoles_twiss_df["K2SL"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        4
                        * betas_x[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        2
                        * betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * (T(2, -1, dmux, dmuy, qx, qy) - T(2, 1, dmux, dmuy, qx, qy))
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_djx_from_sextupoles(self) -> float:
        """
        Get the first order vertical cross-term amplitude detuning from sextupoles.

        Returns:
            The first order vertical cross-term amplitude detuning from sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.sextupoles_twiss_df["MUY"].values
        b2: np.ndarray = self.sextupoles_twiss_df["K2L"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        4
                        * betas_x[k]
                        * betas_y[j]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * 1
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * (2 * 1)
                        * T(1, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * (2 * 1)
                        * (T(1, -2, dmux, dmuy, qx, qy) - T(1, 2, dmux, dmuy, qx, qy))
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_djx(self) -> float:
        """
        Returns the first order vertical cross-term amplitude detuning.

        Returns:
            The first order vertical cross-term amplitude detuning.
        """
        return self.dqy_djx_from_skew_sextupoles() + self.dqy_djx_from_sextupoles()

    def d2qy_djx2_from_skew_octupoles(self) -> float:
        """
        Get the second order vertical cross-term amplitude detuning from skew octupoles.

        Returns:
            The second order vertical cross-term amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETy"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -9
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * (T(3, -1, dmux, dmuy, qx, qy) + T(3, 1, dmux, dmuy, qx, qy))
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 2
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def d2qy_djx2_from_octupoles(self) -> float:
        """
        Get the second order vertical cross-term amplitude detuning from octupoles.

        Returns:
            The second order vertical cross-term amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1)
                        * T(2, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (-2 * 1)
                        * T(2, -2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        36
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -36
                        * betas_x[j]
                        * betas_y[j]
                        * betas_x[k]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def d2qy_djx2(self) -> float:
        """
        Returns the first order vertical cross-term amplitude detuning.

        Returns:
            The first order vertical cross-term amplitude detuning.
        """
        return self.d2qy_djx2_from_skew_octupoles() + self.d2qy_djx2_from_octupoles()

    def dqy_djy_skew_sextupoles(self) -> float:
        """
        Get the first order vertical direct-term amplitude detuning from skew sextupoles.

        Returns:
            The first order vertical direct-term amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_sextupoles_twiss_df["MUY"].values
        a2: np.ndarray = self.skew_sextupoles_twiss_df["K2SL"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -3
                        * betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * 1
                        * T(0, 3, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_djy_from_sextupoles(self) -> float:
        """
        Get the first order vertical direct-term amplitude detuning from sextupoles.

        Returns:
            The first order vertical direct-term amplitude detuning from sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.sextupoles_twiss_df["MUY"].values
        b2: np.ndarray = self.sextupoles_twiss_df["K2L"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -4
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * betas_y[k]
                        * betas_y[j]
                        * 1
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * 1
                        * T(1, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * (-1)
                        * (T(1, -2, dmux, dmuy, qx, qy) - T(1, 2, dmux, dmuy, qx, qy))
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_djy(self) -> float:
        """
        Returns the first order vertical direct-term amplitude detuning.

        Returns:
            The first order vertical direct-term amplitude detuning.
        """
        return self.dqy_djy_skew_sextupoles() + self.dqy_djy_from_sextupoles()

    def d2qy_djy2_from_skew_octupoles(self) -> float:
        """
        Get the second order vertical direct-term amplitude detuning from skew octupoles.

        Returns:
            The second order vertical direct-term amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1)
                        * T(1, -3, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * (-2 * 1)
                        * T(1, 3, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def d2qy_djy2_from_octupoles(self) -> float:
        """
        Get the second order vertical direct-term amplitude detuning from octupoles.

        Returns:
            The second order vertical direct-term amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -3
                        * betas_x[j]
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * 2
                        * 1
                        * T(0, 4, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -24
                        * betas_y[j]
                        * betas_y[j]
                        * betas_y[k]
                        * betas_y[k]
                        * 2
                        * 1
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def d2qy_djy2(self) -> float:
        """
        Returns the second order vertical direct-term amplitude detuning.

        Returns:
            The second order vertical direct-term amplitude detuning.
        """
        return self.d2qy_djy2_from_skew_octupoles() + self.d2qy_djy2_from_octupoles()

    def d2qy_djxdjy_from_skew_octupoles(self) -> float:
        """
        Get the second order vertical mixed-term amplitude detuning from skew octupoles.

        Returns:
            The second order vertical mixed-term amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * (6 * 1 * 1)
                        * T(1, -3, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * (6 * 1 * 1)
                        * T(1, 3, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def d2qy_djxdjy_from_octupoles(self) -> float:
        """
        Get the second order vertical mixed-term amplitude detuning from octupoles.

        Returns:
            The second order vertical mixed-term amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1 * 1)
                        * T(2, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * 1 * 1)
                        * T(2, -2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        72
                        * betas_x[j]
                        * betas_y[k]
                        * betas_y[j]
                        * betas_y[k]
                        * 1
                        * 1
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -72
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * betas_y[j]
                        * 1
                        * 1
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def d2qy_djxdjy(self) -> float:
        """
        Returns the second order vertical mixed-term amplitude detuning.

        Returns:
            The second order vertical mixed-term amplitude detuning.
        """
        return self.d2qy_djxdjy_from_skew_octupoles() + self.d2qy_djxdjy_from_octupoles()

    def dqy_from_skew_quadrupoles(self) -> float:
        """
        Get the vertical amplitude detuning from skew quadrupoles.

        Returns:
            The vertical amplitude detuning from skew quadrupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_quadrupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_quadrupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_quadrupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_quadrupoles_twiss_df["MUY"].values
        a1: np.ndarray = self.skew_quadrupoles_twiss_df["K1SL"].values

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * a1[j]
                    * a1[k]
                    * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                    * (T(1, -1, dmux, dmuy, qx, qy) + T(1, 1, dmux, dmuy, qx, qy))
                )

        return dvy / (2 * np.pi)

    def dqy_from_skew_sextupoles(self, jx: float, jy: float) -> float:
        """
        Get the vertical amplitude detuning from skew sextupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The vertical amplitude detuning from skew sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_sextupoles_twiss_df["MUY"].values
        a2: np.ndarray = self.skew_sextupoles_twiss_df["K2SL"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        4
                        * betas_x[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * jx
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        -3
                        * betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * jy
                        * T(0, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        2
                        * betas_x[j]
                        * betas_x[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * jx
                        * (T(2, -1, dmux, dmuy, qx, qy) - T(2, 1, dmux, dmuy, qx, qy))
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * a2[j]
                    * a2[k]
                    * (
                        betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_y[j] * betas_y[k])
                        * jy
                        * T(0, 3, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_from_sextupoles(self, jx: float, jy: float) -> float:
        """
        Get the vertical amplitude detuning from sextupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The vertical amplitude detuning from sextupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.sextupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.sextupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.sextupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.sextupoles_twiss_df["MUY"].values
        b2: np.ndarray = self.sextupoles_twiss_df["K2L"].values * 2

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        4
                        * betas_x[k]
                        * betas_y[j]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * jx
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -4
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * betas_y[k]
                        * betas_y[j]
                        * jy
                        * T(1, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * (2 * jx + jy)
                        * T(1, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 8)
                    * b2[j]
                    * b2[k]
                    * (
                        -betas_y[j]
                        * betas_y[k]
                        * np.sqrt(betas_x[j] * betas_x[k])
                        * (2 * jx - jy)
                        * (T(1, -2, dmux, dmuy, qx, qy) - T(1, 2, dmux, dmuy, qx, qy))
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_from_skew_octupoles(self, jx: float, jy: float) -> float:
        """
        Get the vertical amplitude detuning from skew octupoles.

            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The vertical amplitude detuning from skew octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.skew_octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.skew_octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.skew_octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.skew_octupoles_twiss_df["MUY"].values
        a3: np.ndarray = self.skew_octupoles_twiss_df["K3SL"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -9
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * (T(3, -1, dmux, dmuy, qx, qy) + T(3, 1, dmux, dmuy, qx, qy))
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * (6 * jx * jy + jy * jy)
                        * T(1, -3, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -3
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * (6 * jx * jy - jy * jy)
                        * T(1, 3, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(1, 1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[j]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        54
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_y[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        72
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -27
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * a3[j]
                    * a3[k]
                    * (
                        -36
                        * np.sqrt(betas_x[j] * betas_x[k] * betas_y[j] * betas_y[k])
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jx
                        * T(1, -1, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def dqy_from_octupoles(self, jx: float, jy: float) -> float:
        """
        Get the vertical amplitude detuning from octupoles.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The vertical amplitude detuning from octupoles.
        """
        qx: float = self.qx
        qy: float = self.qy
        dvy: float = 0  # accumulator for final result

        betas_x: np.ndarray = self.octupoles_twiss_df["BETX"].values
        betas_y: np.ndarray = self.octupoles_twiss_df["BETY"].values
        mu_x: np.ndarray = self.octupoles_twiss_df["MUX"].values
        mu_y: np.ndarray = self.octupoles_twiss_df["MUY"].values
        b3: np.ndarray = self.octupoles_twiss_df["K3L"].values * 6

        for j in range(betas_x.size):
            for k in range(betas_y.size):
                dmux: float = mu_x[j] - mu_x[k]  # horizontal phase advance between those indices
                dmuy: float = mu_y[j] - mu_y[k]  # vertical phase advance between those indices

                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * jx * jy + jx * jx)
                        * T(2, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -9
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_y[k]
                        * (2 * jx * jy - jx * jx)
                        * T(2, -2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -3
                        * betas_x[j]
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * jy
                        * jy
                        * T(0, 4, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -24
                        * betas_y[j]
                        * betas_y[j]
                        * betas_y[k]
                        * betas_y[k]
                        * jy
                        * jy
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        72
                        * betas_x[j]
                        * betas_y[k]
                        * betas_y[j]
                        * betas_y[k]
                        * jx
                        * jy
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -72
                        * betas_x[j]
                        * betas_x[k]
                        * betas_x[k]
                        * betas_y[j]
                        * jx
                        * jy
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        36
                        * betas_x[j]
                        * betas_x[k]
                        * betas_y[j]
                        * betas_x[k]
                        * jx
                        * jx
                        * T(2, 0, dmux, dmuy, qx, qy)
                    )
                )
                dvy += (
                    (1.0 / 32)
                    * b3[j]
                    * b3[k]
                    * (
                        -36
                        * betas_x[j]
                        * betas_y[j]
                        * betas_x[k]
                        * betas_y[k]
                        * jx
                        * jx
                        * T(0, 2, dmux, dmuy, qx, qy)
                    )
                )

        return dvy / (2 * np.pi)

    def dqy(self, jx: float, jy: float) -> float:
        """
        Returns the vertical amplitude detuning.

        Args:
            jx (float): horizontal action variable.
            jy (float): vertical action variable.

        Returns:
            The vertical amplitude detuning.
        """
        return (
            self.dqy_from_skew_quadrupoles()
            + self.dqy_from_skew_sextupoles(jx, jy)
            + self.dqy_from_sextupoles(jx, jy)
            + self.dqy_from_skew_octupoles(jx, jy)
            + self.dqy_from_octupoles(jx, jy)
        )


# -------- Math function -------- #


@numba.njit()
def T(nx, ny, dmux: float, dmuy: float, qx: float, qy: float) -> float:
    """
    The T-function defined in eq. 3.55 of the 'Analytical Calculations of Smear and Tune Shift'
    paper (https://lss.fnal.gov/archive/other/ssc/ssc-232.pdf)

    Args:
        nx (int): first element of the T function's power.
        ny (int): second element of the T function's power.
        dmux (float): horizontal phase advance.
        dmuy (float): vertical phase advance.
        qx (float): horizontal tune.
        qy (float): vertical tune.

    Returns:
        T parameter.
    """
    return np.cos(
        2 * np.pi * (nx * (np.abs(dmux) - qx / 2) + ny * (np.abs(dmuy) - qy / 2))
    ) / np.sin(np.pi * (nx * qx + ny * qy))
