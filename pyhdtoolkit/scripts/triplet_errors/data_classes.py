"""
Module scripts.triplet_errors.data_classes
------------------------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A few classes that will be useful to store values calculated from the results of the GridCompute
Algorithm.
"""

from typing import List

import numpy as np
import pandas as pd

from loguru import logger


class BetaBeatValues:
    """
    Simple class to store and transfer beta-beating values.
    """

    __slots__ = {
        "tferror_bbx": "Horizontal beta-beating values from field errors",
        "tferror_bby": "Vertical beta-beating values from field errors",
        "ip1_tferror_bbx": "Horizontal beta-beating values from field errors at IP1",
        "ip1_tferror_bby": "Vertical beta-beating values from field errors at IP1",
        "ip5_tferror_bbx": "Horizontal beta-beating values from field errors at IP5",
        "ip5_tferror_bby": "Vertical beta-beating values from field errors at IP5",
        "max_tferror_bbx": "Maximal horizontal beta-beating values from field errors",
        "max_tferror_bby": "Maximal vertical beta-beating values from field errors",
        "misserror_bbx": "Horizontal beta-beating values from misalignment errors",
        "misserror_bby": "Horizontal beta-beating values from misalignment errors",
        "ip1_misserror_bbx": "Horizontal beta-beating values from misalignment errors at IP1",
        "ip1_misserror_bby": "Vertical beta-beating values from misalignment errors at IP1",
        "ip5_misserror_bbx": "Horizontal beta-beating values from misalignment errors at IP5",
        "ip5_misserror_bby": "Vertical beta-beating values from misalignment errors at IP5",
        "max_misserror_bbx": "Maximal horizontal beta-beating values from misalignment errors",
        "max_misserror_bby": "Maximal vertical beta-beating values from misalignment errors",
    }

    def __init__(self) -> None:
        self.tferror_bbx: List[float] = []
        self.tferror_bby: List[float] = []
        self.ip1_tferror_bbx: List[float] = []
        self.ip1_tferror_bby: List[float] = []
        self.ip5_tferror_bbx: List[float] = []
        self.ip5_tferror_bby: List[float] = []
        self.max_tferror_bbx: List[float] = []
        self.max_tferror_bby: List[float] = []
        self.misserror_bbx: List[float] = []
        self.misserror_bby: List[float] = []
        self.ip1_misserror_bbx: List[float] = []
        self.ip1_misserror_bby: List[float] = []
        self.ip5_misserror_bbx: List[float] = []
        self.ip5_misserror_bby: List[float] = []
        self.max_misserror_bbx: List[float] = []
        self.max_misserror_bby: List[float] = []

    def describe(self) -> None:
        """
        Simple print statement of instance attributes.
        """
        for attribute, value in self.__dict__.items():
            print(f"{attribute:<20} {value}")

    def update_tf_from_cpymad(self, cpymad_betabeatings: pd.DataFrame) -> None:
        """
        This is to update a temporary BetaBeatValues after having ran a simulation for a specific
        seed. Appends relevant values to the instance's attributes.

        Args:
            cpymad_betabeatings (pd.DataFrame): the beta-beatings from the simulation, compared to
            the nominal twiss from a reference run.

        Returns:
            Nothing, updates inplace.
        """
        self.tferror_bbx.append(_get_rms(cpymad_betabeatings.BETX))
        self.tferror_bby.append(_get_rms(cpymad_betabeatings.BETY))
        self.max_tferror_bbx.append(cpymad_betabeatings.BETX.max())
        self.max_tferror_bby.append(cpymad_betabeatings.BETY.max())
        # cpymad naming: lowercase and appended with :beam_number
        self.ip1_tferror_bbx.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip1:1", "BETX"]
        ).iloc[0]
        self.ip1_tferror_bby.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip1:1", "BETY"]
        ).iloc[0]
        self.ip5_tferror_bbx.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip5:1", "BETX"]
        ).iloc[0]
        self.ip5_tferror_bby.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip5:1", "BETY"]
        ).iloc[0]

    def update_tf_from_seeds(self, temp_data) -> None:
        """
        Updates the error's beta-beatings values after having ran simulations for all seeds.
        Append computed rms values for a group of seeds, to field errors result values.

        Args:
            temp_data: a `BetaBeatValues` object with the seeds' results.

        Returns:
            Nothing, updates inplace.
        """
        self.tferror_bbx.append(_get_rms(temp_data.tferror_bbx))
        self.tferror_bby.append(_get_rms(temp_data.tferror_bby))
        self.max_tferror_bbx.append(_get_rms(temp_data.max_tferror_bbx))
        self.max_tferror_bby.append(_get_rms(temp_data.max_tferror_bby))
        self.ip1_tferror_bbx.append(_get_rms(temp_data.ip1_tferror_bbx))
        self.ip1_tferror_bby.append(_get_rms(temp_data.ip1_tferror_bby))
        self.ip5_tferror_bbx.append(_get_rms(temp_data.ip5_tferror_bbx))
        self.ip5_tferror_bby.append(_get_rms(temp_data.ip5_tferror_bby))

    def update_miss_from_cpymad(self, cpymad_betabeatings: pd.DataFrame) -> None:
        """
        Updates a temporary BetaBeatValues after having ran a simulation for a specific seed.
        Appends relevant values to the instance's attributes.

        Args:
            cpymad_betabeatings (pd.DataFrame): the beta-beatings from the simulation, compared to
            the nominal twiss from a reference run.

        Returns:
            Nothing, updates inplace.
        """
        self.misserror_bbx.append(_get_rms(cpymad_betabeatings.BETX))
        self.misserror_bby.append(_get_rms(cpymad_betabeatings.BETY))
        self.max_misserror_bbx.append(cpymad_betabeatings.BETX.max())
        self.max_misserror_bby.append(cpymad_betabeatings.BETY.max())
        # cpymad naming: lowercase and appended with :beam_number
        self.ip1_misserror_bbx.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip1:1", "BETX"]
        ).iloc[0]
        self.ip1_misserror_bby.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip1:1", "BETY"]
        ).iloc[0]
        self.ip5_misserror_bbx.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip5:1", "BETX"]
        ).iloc[0]
        self.ip5_misserror_bby.append(
            cpymad_betabeatings.loc[cpymad_betabeatings.NAME == "ip5:1", "BETY"]
        ).iloc[0]

    def update_miss_from_seeds(self, temp_data) -> None:
        """
        Append computed rms values for a group of seeds, to misalignment result values.

        Args:
            temp_data: a `BetaBeatValues` object with the seeds' results.

        Returns:
            Nothing, updates inplace.
        """
        self.misserror_bbx.append(_get_rms(temp_data.misserror_bbx))
        self.misserror_bby.append(_get_rms(temp_data.misserror_bby))
        self.max_misserror_bbx.append(_get_rms(temp_data.max_misserror_bbx))
        self.max_misserror_bby.append(_get_rms(temp_data.max_misserror_bby))
        self.ip1_misserror_bbx.append(_get_rms(temp_data.ip1_misserror_bbx))
        self.ip1_misserror_bby.append(_get_rms(temp_data.ip1_misserror_bby))
        self.ip5_misserror_bbx.append(_get_rms(temp_data.ip5_misserror_bbx))
        self.ip5_misserror_bby.append(_get_rms(temp_data.ip5_misserror_bby))

    def export(self, csvname: str = "betabeatings.csv") -> pd.DataFrame:
        """
        Exports stored values as a pandas DataFrame, potentially saving them as a csv file.

        Args:
            csvname (str): the name to give the csv file.

        Returns:
            A `pandas.DataFrame` object with the instance's attributes as columns.
        """
        betabeatings_df = pd.DataFrame(self.__dict__)
        betabeatings_df.to_csv(csvname, index=False)
        return betabeatings_df


class StdevValues:
    """
    Simple class to store and transfer standard deviation values.
    """

    __slots__ = {
        "stdev_tf_x": "Horizontal standard deviation values from field errors",
        "stdev_tf_y": "Vertical standard deviation values from field errors",
        "ip1_stdev_tf_x": "Horizontal standard deviation values from field errors at IP1",
        "ip1_stdev_tf_y": "Vertical standard deviation values from field errors at IP1",
        "ip5_stdev_tf_x": "Horizontal standard deviation values from field errors at IP5",
        "ip5_stdev_tf_y": "Vertical standard deviation values from field errors at IP5",
        "max_stdev_tf_x": "Maximal horizontal standard deviation values from field errors",
        "max_stdev_tf_y": "Maximal vertical standard deviation values from field errors",
        "stdev_miss_x": "Horizontal standard deviation values from misalignment errors",
        "stdev_miss_y": "Horizontal standard deviation values from misalignment errors",
        "ip1_stdev_miss_x": "Horizontal standard deviation values from misalignment errors at IP1",
        "ip1_stdev_miss_y": "Vertical standard deviation values from misalignment errors at IP1",
        "ip5_stdev_miss_x": "Horizontal standard deviation values from misalignment errors at IP5",
        "ip5_stdev_miss_y": "Vertical standard deviation values from misalignment errors at IP5",
        "max_stdev_miss_x": "Maximal horizontal standard deviation values from misalignment errors",
        "max_stdev_miss_y": "Maximal vertical standard deviation values from misalignment errors",
    }

    def __init__(self) -> None:
        self.stdev_tf_x: List[float] = []
        self.stdev_tf_y: List[float] = []
        self.ip1_stdev_tf_x: List[float] = []
        self.ip1_stdev_tf_y: List[float] = []
        self.ip5_stdev_tf_x: List[float] = []
        self.ip5_stdev_tf_y: List[float] = []
        self.max_stdev_tf_x: List[float] = []
        self.max_stdev_tf_y: List[float] = []
        self.stdev_miss_x: List[float] = []
        self.stdev_miss_y: List[float] = []
        self.ip1_stdev_miss_x: List[float] = []
        self.ip1_stdev_miss_y: List[float] = []
        self.ip5_stdev_miss_x: List[float] = []
        self.ip5_stdev_miss_y: List[float] = []
        self.max_stdev_miss_x: List[float] = []
        self.max_stdev_miss_y: List[float] = []

    def describe(self) -> None:
        """
        Simple print statement of instance attributes.
        """
        for attribute, value in self.__dict__.items():
            print(f"{attribute:<20} {value}")

    def update_tf(self, temp_data) -> None:
        """
        Append computed stdev values for a group of seeds, to field errors result values.

        Args:
            temp_data: a `BetaBeatValues` object with the seeds' results.

        Returns:
            Nothing, updates inplace.
        """
        self.stdev_tf_x.append(np.std(temp_data.tferror_bbx))
        self.stdev_tf_y.append(np.std(temp_data.tferror_bby))
        self.max_stdev_tf_x.append(np.std(temp_data.max_tferror_bbx))
        self.max_stdev_tf_y.append(np.std(temp_data.max_tferror_bby))
        self.ip1_stdev_tf_x.append(np.std(temp_data.ip1_tferror_bbx))
        self.ip1_stdev_tf_y.append(np.std(temp_data.ip1_tferror_bby))
        self.ip5_stdev_tf_x.append(np.std(temp_data.ip5_tferror_bbx))
        self.ip5_stdev_tf_y.append(np.std(temp_data.ip5_tferror_bby))

    def update_miss(self, temp_data) -> None:
        """
        Append computed rms values for a group of seeds, to misalignment errors result values.

        Args:
            temp_data: a `BetaBeatValues` object with the seeds' results.

        Returns:
            Nothing, updates inplace.
        """
        self.stdev_miss_x.append(np.std(temp_data.misserror_bbx))
        self.stdev_miss_y.append(np.std(temp_data.misserror_bby))
        self.max_stdev_miss_x.append(np.std(temp_data.max_misserror_bbx))
        self.max_stdev_miss_y.append(np.std(temp_data.max_misserror_bby))
        self.ip1_stdev_miss_x.append(np.std(temp_data.ip1_misserror_bbx))
        self.ip1_stdev_miss_y.append(np.std(temp_data.ip1_misserror_bby))
        self.ip5_stdev_miss_x.append(np.std(temp_data.ip5_misserror_bbx))
        self.ip5_stdev_miss_y.append(np.std(temp_data.ip5_misserror_bby))

    def export(self, csvname: str = "stdev.csv") -> pd.DataFrame:
        """
        Simple function to export stored values as a pandas dataframe, potentially saving
        them as a csv file.

        Args:
            csvname (str): the name to give the csv file.

        Returns:
            A `pandas.DataFrame` object with the instance's attributes as columns.
        """
        stdev_df = pd.DataFrame(self.__dict__)
        stdev_df.to_csv(csvname, index=False)
        return stdev_df


def _get_rms(values_list: List[float]) -> float:
    """
    Get the root mean square of a list of values.

    Args:
        values_list (List[float]): a distribution of values.

    Returns:
        The root mean square of said distribution.
    """
    try:
        return np.sqrt(np.sum(i ** 2 for i in values_list) / len(values_list))
    except ZeroDivisionError as issue:
        logger.exception("An empty list was provided, check the simulation logs to understand why.")
        raise ZeroDivisionError("No values were provided") from issue
