"""
Script scripts.triplets_errors.algo
----------------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

Command-line utility script, which will launch a series of MAD-X simulations, perform analysis of
the outputs and hand out a plot.

Arguments should be given as options at launch in the command-line. See README for instructions.
"""

import argparse
import sys

from copy import deepcopy
from typing import List

import cpymad
import numpy as np
import pandas as pd

from loguru import logger
from rich.progress import track

from pyhdtoolkit.cpymadtools.generators import LatticeGenerator
from pyhdtoolkit.scripts.triplet_errors.data_classes import BetaBeatValues, StdevValues
from pyhdtoolkit.scripts.triplet_errors.plotting_functions import (
    plot_bbing_max_errorbar,
    plot_bbing_with_ips_errorbar,
)
from pyhdtoolkit.utils.contexts import timeit
from pyhdtoolkit.utils.defaults import LOGURU_FORMAT


class GridCompute:
    """
    Algorithm as a class to run the simulations and analyze the outputs.

    Will prompt error values for confirmation, run MAD-X simulations through a `cpymad.madx.Madx`
    object, get beta-beating values from the outputs and return the appropriate structures.
    """

    __slots__ = {
        "reference_mad": "cpymad Madx object to run the nominal configuration",
        "errors_mad": "cpymad Madx object to run errored simulations",
        "rms_betabeatings": "BetaBeatValues class to hold rms beta-beatings from simulations",
        "standard_deviations": "StdevValues class to hold standard deviations from simulations",
        "lost_seeds_tf": "List of field error values leading to loss of closed orbit",
        "lost_seeds_miss": "List of misalignment values leading to loss of closed orbit",
        "nominal_twiss": "Twiss dataframe from the nominal simulation",
    }

    def __init__(self) -> None:
        """
        Initializing will take some time since the reference script is being ran, to store the
        reference dframe. Unless you go into PTC it should be a matter of seconds.
        """
        self.reference_mad = cpymad.madx.Madx(stdout=False)
        self.errors_mad = cpymad.madx.Madx(stdout=False)
        self.rms_betabeatings = BetaBeatValues()
        self.standard_deviations = StdevValues()
        self.lost_seeds_tf: List[int] = []
        self.lost_seeds_miss: List[int] = []
        self.nominal_twiss = self._get_nominal_twiss()

    def _get_nominal_twiss(self) -> pd.DataFrame:
        """
        Run a MAD-X simulation without errors, and extract the nominal Twiss from the results.
        This will be stored in the `nominal_twiss` instance attribute.

        Returns:
            Nothing, directly updates the instance's `nominal_twiss` attribute inplace.
        """
        logger.info("Running simulation for reference nominal run")
        ref_script = LatticeGenerator.generate_tripleterrors_study_reference()
        self.reference_mad.input(ref_script)
        logger.debug("Extracting reference Twiss dframe from cpymad")
        return deepcopy(self.reference_mad.table.twiss.dframe())

    def run_tf_errors(self, error_values: List[float], n_seeds: int) -> None:
        """
        Run simulations for field errors, compute the values from the outputs, and store the final
        results in the class's data structures.

        Args:
            error_values (List[float]): the different error values to run simulations for
            n_seeds (int): number of simulations to run for each error values.

        Returns:
            Nothing, directly updates the instance's `rms_betabeatings` and `standard_deviations`
            attributes.
        """
        with timeit(lambda spanned: logger.info(f"Simulated field errors in: {spanned:.4f} seconds")):
            for error in error_values:
                logger.debug(f"Running simulation for Relative Field Error: {error}E-4")
                temp_data = BetaBeatValues()

                for _ in track(range(n_seeds), description="Simulating Field Errors Seeds", transient=True):
                    # Getting beta-beatings & appending to temporary BetaBeatValues
                    tferrors_twiss: pd.DataFrame = self._track_tf_error(error)
                    betabeatings: pd.DataFrame = _get_betabeatings(self.nominal_twiss, tferrors_twiss)
                    temp_data.update_tf_from_cpymad(betabeatings)

                # Append computed seeds' RMS for this error value in `rms_betabeatings` attribute.
                self.rms_betabeatings.update_tf_from_seeds(temp_data)

                # Getting stdev of all values for the N computed seeds
                self.standard_deviations.update_tf(temp_data)

                # Getting the lost seeds if any
                self.lost_seeds_tf.append(n_seeds - len(temp_data.tferror_bbx))

    def _track_tf_error(self, error: float) -> pd.DataFrame:
        """
        Run tferror tracking for a given seed, which is randomly assigned at function call.

        Args:
            error (float): the error value to input in the madx script.

        Returns:
            The twiss dframe from cpymad.
        """
        seed = str(np.random.randint(1e6, 5e6))
        tferror_script = LatticeGenerator.generate_tripleterrors_study_tferror_job(seed, str(error))
        self.errors_mad.input(tferror_script)
        return self.errors_mad.table.twiss.dframe()

    def run_miss_errors(self, error_values: List[float], n_seeds: int) -> None:
        """
        Run the simulations for misalignment errors, compute the values from the outputs, and store
        the final results in the class's data structures.

        Args:
            error_values (List[float]): the different error values to run simulations for.
            n_seeds (int): number of simulations to run for each error values.

        Returns:
            Nothing, directly updates the instance's `rms_betabeatings` and `standard_deviations`
            attributes.
        """
        with timeit(lambda spanned: logger.info(f"Simulated misalignment errors in: {spanned:.4f} seconds")):
            for error in error_values:
                logger.debug(f"Running for Longitudinal Misalignment Error: {float(error)}mm")
                temp_data = (
                    BetaBeatValues()
                )  # this will hold the beta-beats for all seeds with this error value.

                for _ in track(range(n_seeds), description="Simulating Misalignment Seeds", transient=True):
                    # Getting beta-beatings & appending to temporary BetaBeatValues
                    mserrors_twiss: pd.DataFrame = self._track_miss_error(error)
                    betabeatings: pd.DataFrame = _get_betabeatings(self.nominal_twiss, mserrors_twiss)
                    temp_data.update_miss_from_cpymad(betabeatings)

                # Append computed seeds' RMS for this error value in `rms_betabeatings` attribute.
                self.rms_betabeatings.update_miss_from_seeds(temp_data)

                # Getting stdev of all values for the N computed seeds
                self.standard_deviations.update_miss(temp_data)

                # Getting the lost seeds if any
                self.lost_seeds_miss.append(n_seeds - len(temp_data.misserror_bbx))

    def _track_miss_error(self, error: float) -> pd.DataFrame:
        """
        Run misserror tracking for a given seed, which is randomly assigned at function call.

        Args:
            error (float): the error value to input in the madx script.

        Returns:
            The twiss dframe from cpymad.
        """
        seed = str(np.random.randint(1e6, 5e6))
        mserror_script = LatticeGenerator.generate_tripleterrors_study_mserror_job(seed, str(error))
        self.errors_mad.input(mserror_script)
        return self.errors_mad.table.twiss.dframe()


def _get_betabeatings(nominal_twiss: pd.DataFrame, errors_twiss: pd.DataFrame) -> pd.DataFrame:
    """
    Simple function to get beta-beatings from a `cpymad.madx.Madx`'s Twiss output.

    Args:
        nominal_twiss (pd.DataFrame): a twiss.dframe() results from a reference scenario.
        errors_twiss (pd.DataFrame): a twiss.dframe() results from the perturbed scenario.

    Returns:
        A `pd.DataFrame` with the beta-beat values, in percentage.
    """
    betabeat = pd.DataFrame()
    betabeat["NAME"] = nominal_twiss.name
    betabeat["s"] = nominal_twiss.s
    betabeat["BETX"] = 100 * (errors_twiss.betx - nominal_twiss.betx) / nominal_twiss.betx
    betabeat["BETY"] = 100 * (errors_twiss.bety - nominal_twiss.bety) / nominal_twiss.bety
    return betabeat


def _parse_arguments() -> argparse.Namespace:
    """
    Simple argument parser to make life easier in the command-line.
    Returns a NameSpace with arguments as attributes.
    """
    parser = argparse.ArgumentParser(description="Running the beta-beating script.")
    parser.add_argument(
        "-e",
        "--errors",
        dest="errors",
        nargs="+",
        default=[1, 3, 5],
        type=int,
        help="Error values to simulate",
    )
    parser.add_argument(
        "-s", "--seeds", dest="seeds", default=50, type=int, help="Number of seeds to simulate per error.",
    )
    parser.add_argument(
        "-p", "--plotbetas", dest="plotbetas", default=False, help="Option for plotting betas at each error.",
    )
    parser.add_argument(
        "-l",
        "--logs",
        dest="log_level",
        default="info",
        type=str,
        help="The base console logging level. Can be 'debug', 'info', 'warning' and 'error'."
        "Defaults to 'info'.",
    )
    return parser.parse_args()


def _set_logger_level(log_level: str = "info") -> None:
    """
    Sets the logger level to the one provided at the commandline.

    Default loguru handler will have DEBUG level and ID 0.
    We need to first remove this default handler and add ours with the wanted level.

    Args:
        log_level (str): string, the default logging level to print out.
    """
    logger.remove(0)
    logger.add(sys.stderr, format=LOGURU_FORMAT, level=log_level.upper())


@logger.catch
def main() -> None:
    """
    Run the whole process.

    Will prompt for error grid values for confirmation. Instantiates a GridCompute object and runs
    for each type of errors. The results are stored in the class itself, to be accessed for
    plotting.
    """
    command_line_args = _parse_arguments()
    _set_logger_level(command_line_args.log_level)
    simulations = GridCompute()

    logger.info(f"Here are the error values that will be ran: {command_line_args.errors}")

    # Running simulations
    simulations.run_tf_errors(command_line_args.errors, command_line_args.seeds)
    simulations.run_miss_errors(command_line_args.errors, command_line_args.seeds)

    # Getting the results in dataframes and exporting to csv
    logger.info("Exporting results to csv")
    bbing_df: pd.DataFrame = simulations.rms_betabeatings.to_pandas()
    std_df: pd.DataFrame = simulations.standard_deviations.to_pandas()
    bbing_df.to_csv("beta_beatings.csv", index=False)
    std_df.to_csv("standard_deviations.csv", index=False)

    # Plotting the results
    plot_bbing_max_errorbar(
        command_line_args.errors,
        beta_beatings_df=bbing_df,
        stdev_df=std_df,
        plane="Horizontal",
        figname="miss_vs_tf_max_hor.png",
    )
    plot_bbing_max_errorbar(
        command_line_args.errors,
        beta_beatings_df=bbing_df,
        stdev_df=std_df,
        plane="Vertical",
        figname="miss_vs_tf_max_ver.png",
    )
    plot_bbing_with_ips_errorbar(
        command_line_args.errors,
        beta_beatings_df=bbing_df,
        stdev_df=std_df,
        plane="Horizontal",
        figname="miss_vs_tf_ips_hor.png",
    )
    plot_bbing_with_ips_errorbar(
        command_line_args.errors,
        beta_beatings_df=bbing_df,
        stdev_df=std_df,
        plane="Vertical",
        figname="miss_vs_tf_ips_ver.png",
    )


if __name__ == "__main__":
    main()
