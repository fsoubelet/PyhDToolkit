"""
Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

Command-line utility script, which will launch a series of MAD-X simulations, perform analysis of the outputs and
hand out a plot.

Arguments should be given as options at launch in the command-line. See README for instructions.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import tqdm

import cpymad
from pyhdtoolkit.cpymadtools import lattice_generators
from pyhdtoolkit.studies.triplet_errors.data_classes import BetaBeatValues, StdevValues
from pyhdtoolkit.studies.triplet_errors.plotting_functions import plot_bbing_max_errorbar, plot_bbing_with_ips_errorbar


class GridCompute:
    """
    Algorithm as a class to run the simulations and analyze the outputs.

    Will prompt error values for confirmation, run MAD-X simulations through a `cpymad.madx.Madx` object,
    get beta-beating values from the outputs and return the appropriate structures.
    """

    def __init__(self):
        """
        Initializing will take some time since the reference script is being ran, to store the reference dframe.
        Unless you go into PTC it should be a matter of seconds.
        """
        self.reference_mad = cpymad.madx.Madx(stdout=False)
        self.errors_mad = cpymad.madx.Madx(stdout=False)
        self.rms_betabeatings = BetaBeatValues()
        self.standard_deviations = StdevValues()
        self.lost_seeds_tf = []
        self.lost_seeds_miss = []
        self.nominal_twiss = self._get_nominal_twiss()

    def _get_nominal_twiss(self) -> pd.DataFrame:
        """
        Run a MAD-X simulation without errors, and extract the nominal Twiss from the results.
        This will be stored in the `nominal_twiss` instance attribute.
        :return: nothing, directly updates the instance's `nominal_twiss` attribute inplace.
        """
        print(f"\n[GridCompute] Simulating reference nominal run")
        ref_script = lattice_generators.LatticeGenerator.generate_tripleterrors_study_reference()
        self.reference_mad.input(ref_script)
        reference_dframe = deepcopy(self.reference_mad.table.twiss.dframe())
        return reference_dframe

    def run_tf_errors(self, error_values: list, n_seeds: int) -> None:
        """
        Run simulations for field errors, compute the values from the outputs, and store the final results in the
        class's data structures.
        :param error_values: a list of the different error values to run simulations for
        :param n_seeds: number of simulations to run for each error values.
        :return: nothing, directly updates the instance's `rms_betabeatings` and `standard_deviations` attributes.
        """
        if self.nominal_twiss is None:
            raise AttributeError(
                "You should initialize the nominal twiss first. To do so run `self._get_nominal_twiss`"
            )
        start_time = datetime.now()

        # Running the errors simulations
        for error in error_values:
            print(f"\n[GridCompute] Relative Field Error : {error}E-4")
            temp_data = BetaBeatValues()  # this will hold the beta-beats for all seeds with this error value.

            for _ in tqdm.tqdm(range(n_seeds), desc="Simulating", unit="Seeds"):
                seed = str(np.random.randint(1e6, 5e6))
                tferror_script = lattice_generators.LatticeGenerator.generate_tripleterrors_study_tferror_job(
                    seed, str(error)
                )
                self.errors_mad.input(tferror_script)
                tferrors_twiss = self.errors_mad.table.twiss.dframe()

                # Getting the beta-beatings and appending to temporary BetaBeatValues defined earlier
                betabeatings = _get_betabeatings(self.nominal_twiss, tferrors_twiss)  # this is a pd.DataFrame
                temp_data.update_tf_from_cpymad(betabeatings)

            # Append RMS of all computed seeds for this error value in `rms_betabeatings` instance attribute.
            self.rms_betabeatings.update_tf_from_seeds(temp_data)

            # Getting stdev of all values for the N computed seeds
            self.standard_deviations.update_tf(temp_data)

            # Getting the lost seeds if any
            self.lost_seeds_tf.append(n_seeds - len(temp_data.tferror_bbx))

        end_time = datetime.now()
        print(f"[GridCompute] Simulated field errors in {end_time - start_time}\n")

    def run_miss_errors(self, error_values: list, n_seeds: int) -> None:
        """
        Run the simulations for misalignment errors, compute the values from the outputs, and store the final results
        in the class's data structures.
        :param error_values: a list of the different error values to run simulations for
        :param n_seeds: number of simulations to run for each error values.
        :return: nothing, directly updates the instance's `rms_betabeatings` and `standard_deviations` attributes.
        """
        if self.nominal_twiss is None:
            raise AttributeError(
                "You should initialize the nominal twiss first. To do so run `self._get_nominal_twiss`"
            )
        start_time = datetime.now()

        # Running the errors simulations
        for error in error_values:
            print(f"\n[GridCompute] Longitudinal Missalignment Error : {float(error)}mm")
            temp_data = BetaBeatValues()  # this will hold the beta-beats for all seeds with this error value.

            for _ in tqdm.tqdm(range(n_seeds), desc="Simulating", unit="Seeds"):
                seed = str(np.random.randint(1e6, 5e6))
                mserror_script = lattice_generators.LatticeGenerator.generate_tripleterrors_study_mserror_job(
                    seed, str(error)
                )
                self.errors_mad.input(mserror_script)
                mserrors_twiss = self.errors_mad.table.twiss.dframe()

                # Getting the beta-beatings and appending to temporary BetaBeatValues defined earlier
                betabeatings = _get_betabeatings(self.nominal_twiss, mserrors_twiss)  # this is a pd.DataFrame
                temp_data.update_miss_from_cpymad(betabeatings)

            # Append RMS of all computed seeds for this error value in `rms_betabeatings` instance attribute.
            self.rms_betabeatings.update_miss_from_seeds(temp_data)

            # Getting stdev of all values for the N computed seeds
            self.standard_deviations.update_miss(temp_data)

            # Getting the lost seeds if any
            self.lost_seeds_miss.append(n_seeds - len(temp_data.misserror_bbx))

        end_time = datetime.now()
        print(f"[GridCompute] Simulated missalignment errors in {end_time - start_time}\n")


def _get_betabeatings(nominal_twiss: pd.DataFrame, errors_twiss: pd.DataFrame) -> pd.DataFrame:
    """
    Simple function to get beta-beatings from a `cpymad.madx.Madx`'s Twiss output.
    :param nominal_twiss: twiss.dframe() results from a reference scenario.
    :param errors_twiss: twiss.dframe() results from the perturbed scenario.
    :return: a `pd.DataFrame` with the beta-beat values, in percentage.
    """
    betabeat = pd.DataFrame()
    betabeat["NAME"] = nominal_twiss.name
    betabeat["s"] = nominal_twiss.s
    betabeat["BETX"] = 100 * (errors_twiss.betx - nominal_twiss.betx) / nominal_twiss.betx
    betabeat["BETY"] = 100 * (errors_twiss.bety - nominal_twiss.bety) / nominal_twiss.bety
    return betabeat


def _parse_args():
    """
    Simple argument parser to make life easier in the command-line.
    """
    parser = argparse.ArgumentParser(description="Running the beta-beating script.")
    parser.add_argument(
        "-e", "--errors", dest="errors", nargs="+", default=[1, 3, 5], type=int, help="Error values to simulate"
    )
    parser.add_argument(
        "-s", "--seeds", dest="seeds", default=50, type=int, help="Number of seeds to simulate per error."
    )
    parser.add_argument(
        "-p", "--plotbetas", dest="plotbetas", default=False, help="Option for plotting betas at each error."
    )
    options = parser.parse_args()
    return options.errors, options.seeds, options.plotbetas


def main():
    """
    Run the whole process.

    Will prompt for error grid values for confirmation. Instantiates a GridCompute object and runs for each type of
    errors. The results are stored in the class itself, to be accessed for plotting.
    """
    print("\n[GridCompute] Welcome to GridCompute.")

    # Getting commandline arguments and instantiating
    errors, seeds, plotbetas = _parse_args()
    simulations = GridCompute()

    print(f"\n[GridCompute] Here are the error values that will be ran: {errors}")
    print(f"[GridCompute] This will launch {2 * seeds * len(errors)} MAD-X simulations.")
    print(f"[GridCompute] Estimated time to completion: {str(timedelta(seconds=2*15*seeds*len(errors)))}.")
    checkup = input("\n[GridCompute] Press any key to launch, otherwise 'ctrl-c'to abort: ")

    # Running simulations
    simulations.run_tf_errors(errors, seeds)
    simulations.run_miss_errors(errors, seeds)

    # Getting the results in dataframes and exporting to csv
    bbing_df = simulations.rms_betabeatings.export(csvname="beta_beatings.csv")
    std_df = simulations.standard_deviations.export(csvname="standard_deviations.csv")

    # Plotting the results
    plot_bbing_max_errorbar(
        errors, beta_beatings_df=bbing_df, stdev_df=std_df, plane="Horizontal", figname="miss_vs_tf_max_hor.png"
    )
    plot_bbing_max_errorbar(
        errors, beta_beatings_df=bbing_df, stdev_df=std_df, plane="Vertical", figname="miss_vs_tf_max_ver.png"
    )
    plot_bbing_with_ips_errorbar(
        errors, beta_beatings_df=bbing_df, stdev_df=std_df, plane="Horizontal", figname="miss_vs_tf_ips_hor.png"
    )
    plot_bbing_with_ips_errorbar(
        errors, beta_beatings_df=bbing_df, stdev_df=std_df, plane="Vertical", figname="miss_vs_tf_ips_ver.png"
    )


if __name__ == "__main__":
    main()
