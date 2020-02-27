"""
Created on 2019.06.15
:author: Felix Soubelet

A collection of functions that will be useful to plot the results from GridCompute Algorithm.
"""

import os
import pathlib

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from fsbox import logging_tools

LOGGER = logging_tools.get_logger(__name__)


if os.environ.get("Display", "") == "":
    LOGGER.info(f"Display configuration error found. Using non-interactive Agg backend.")
    matplotlib.use("Agg")


def plot_betas_across_machine(
    s_values: list, betx_values: list, bety_values: list, error_type: str, error_value: str
) -> None:
    """
    Plot beta functions across the machine. Save according to simulation scenario.
    Creates a plot of the horizontal and vertical beta functions across the whole machine. Gives a title generated
    according to the error type and error value. Saves in dedicated subfolder.
    :param s_values: the values of the s axis.
    :param betx_values: horizontal beta values accross the machine.
    :param bety_values: vertical beta values accross the machine.
    :param error_type: which error you have simulated too get those results.
    :param error_value: the value of the error you used in your simulations.
    :return: nothing, plots and saves the figure.
    """
    if error_type == "TFERROR":
        title = f"r'Beta values, hllhc1.3, 15cm optics, relative field error: {error_value}[$10^{-4}$]'"
    elif error_type == "MISERROR":
        title = f"r'Beta values, hllhc1.3 15cm optics, misalignment: {error_value}[mm]'"
    else:
        LOGGER.warning(f"Invalid error parameter {error_type} provided, aborting plot.")
        raise ValueError("Invalid error parameter. Should be either `TFERROR` or `MISERROR`.")

    output_dir = pathlib.Path("beta_plots") / f"{error_type}" / f"{error_value}"
    if not output_dir.is_dir():
        LOGGER.info(f"Creating directory {output_dir}.")
        output_dir.mkdir()

    plt.figure(figsize=(18, 10))
    plt.title(title, fontsize=21)
    plt.xlabel("Position alongside s axis [m]", fontsize=17)
    plt.ylabel(r"$\beta$ value [m]", fontsize=17)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xlim(6500, max(s_values))
    plt.plot(s_values, betx_values, label="BETX")
    plt.plot(s_values, bety_values, label="BETY")
    plt.legend(loc="best", fontsize="xx-large")
    plt.savefig(f"beta_plots/{error_type}/{error_value}/betas_across_machine.png", format="png", dpi=300)
    LOGGER.info(f"Plotted betas for {error_type} {error_value}.")


def plot_bbing_max_errorbar(
    errors: list, beta_beatings_df: pd.DataFrame, stdev_df: pd.DataFrame, plane: str, figname: str
) -> None:
    """
    Plot beta-beating values, with error bars, as a function of the error values. Save according to plotted plane.
    Creates a plot of the horizontal or vertical beta-beatings across the range of simulated error values. Gives a
    title generated according to the error type and error value. Saves in dedicated subfolder.
    :param errors: list with different error values simulated.
    :param beta_beatings_df: a `pandas.DataFrame` object with the resulting beta-beating values.
    :param stdev_df: a `pandas.DataFrame` object with the standard deviations for those values.
    :param plane: the name of the plane to plot.
    :param figname: how to name the file when exporting the plot.
    :return: nothing, plots and saves the figure.
    """

    if plane == "Horizontal":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.TFERROR_X,
            yerr=stdev_df.STD_TF_X,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.MISSERROR_X,
            yerr=stdev_df.STD_MISS_X,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(errors, beta_beatings_df.MAX_TFERROR_X, "^", color="C0", label="Max Value from Field Errors")
        axes.plot(errors, beta_beatings_df.MAX_MISSERROR_X, "^", color="C1", label="Max Value from Misalignment Errors")
        axes.set_xlabel(r"Relative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-Beating Against Triplet Errors, {plane} Plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="png", dpi=300)

    elif plane == "Vertical":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.TFERROR_Y,
            yerr=stdev_df.STD_TF_Y,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.MISSERROR_Y,
            yerr=stdev_df.STD_MISS_Y,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(errors, beta_beatings_df.MAX_TFERROR_Y, "^", color="C0", label="Max Value from Field Errors")
        axes.plot(errors, beta_beatings_df.MAX_MISSERROR_Y, "^", color="C1", label="Max Value from Misalignment Errors")
        axes.set_xlabel(r"Relative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-beating against triplet errors, {plane} plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="png", dpi=300)

    else:
        LOGGER.warning(f"Invalid plane parameter {plane} provided, aborting plot.")
        raise ValueError("Invalid plane parameter. Should be either `Horizontal` or `Vertical`.")
    LOGGER.info(f"Plotted beta-beatings with error bars for {plane.lower()} plane.")


def plot_bbing_with_ips_errorbar(
    errors: list, beta_beatings_df: pd.DataFrame, stdev_df: pd.DataFrame, plane: str, figname: str
) -> None:
    """
    Plot beta-beating values, with error bars, as a function of the error values. Save according to plotted plane.
    Creates a plot of the horizontal or vertical beta-beatings across the range of simulated error values,
    with the addition of the beta-beating value at IPs. Gives a title generated according to the error type and error
    value. Saves in dedicated subfolder.
    :param errors: list with different error values simulated.
    :param beta_beatings_df: a `pandas.DataFrame` object with the resulting beta-beating values.
    :param stdev_df: a `pandas.DataFrame` object with the standard deviations for those values.
    :param plane: the name of the plane to plot.
    :param figname: how to name the file when exporting the plot.
    :return: nothing, plots and saves the figure.
    """

    if plane == "Horizontal":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.TFERROR_X,
            yerr=stdev_df.STD_TF_X,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.MISSERROR_X,
            yerr=stdev_df.STD_MISS_X,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(
            errors, beta_beatings_df.IP1_TFERROR_X, "^", color="C0", label="IP1 Beta-Beating Value from Field Errors"
        )
        axes.plot(
            errors,
            beta_beatings_df.IP1_MISSERROR_X,
            "^",
            color="C1",
            label="IP1 Beta-Beating Value from Misalignment Errors",
        )
        axes.plot(
            errors, beta_beatings_df.IP5_TFERROR_X, "x", color="C0", label="IP5 Beta-Beating Value from Field Errors"
        )
        axes.plot(
            errors,
            beta_beatings_df.IP5_MISSERROR_X,
            "x",
            color="C1",
            label="IP5 Beta-Beating Value from Misalignment Errors",
        )
        axes.set_xlabel(r"Relative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-Beating Against Triplet Errors, {plane} Plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="png", dpi=300)

    if plane == "Vertical":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.TFERROR_Y,
            yerr=stdev_df.STD_TF_Y,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.MISSERROR_Y,
            yerr=stdev_df.STD_MISS_Y,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(
            errors, beta_beatings_df.IP1_TFERROR_Y, "^", color="C0", label="IP1 Beta-Beating Value from Field Errors"
        )
        axes.plot(
            errors,
            beta_beatings_df.IP1_MISSERROR_Y,
            "^",
            color="C1",
            label="IP1 Beta-Beating Value from Misalignment Errors",
        )
        axes.plot(
            errors, beta_beatings_df.IP5_TFERROR_Y, "x", color="C0", label="IP5 Beta-Beating Value from Field Errors"
        )
        axes.plot(
            errors,
            beta_beatings_df.IP5_MISSERROR_Y,
            "x",
            color="C1",
            label="IP5 Beta-Beating Value from Misalignment Errors",
        )
        axes.set_xlabel(r"TRelative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-Beating Against Triplet Errors, {plane} Plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="png", dpi=300)

    else:
        LOGGER.warning(f"Invalid plane parameter {plane} provided, aborting plot.")
        raise ValueError("Invalid plane parameter. Should be either `Horizontal` or `Vertical`.")
    LOGGER.info(f"Plotted beta-beatings (including IPs) with error bars for {plane.lower()} plane.")


def plot_intermediate_beta_histograms(
    betasx: list, betasy: list, error_val: float, title: str, outputname: str
) -> None:
    """
    Plot histogram distribution for betas at seeds.
    :param betasx: list of all horizontal beta values for all seeds for a specific error value.
    :param betasy: list of all vertical beta values for all seeds for a specific error value.
    :param error_val: the error value.
    :param title: the title to give the figure.
    :param outputname: the name to give the file saving the figure.
    :return: nothing, plots and saves the figure.
    """
    plt.hist(betasx, bins=50, label=f"{error_val}, horizontal", alpha=0.6, density=True)
    plt.hist(betasy, bins=50, label=f"{error_val}, vertical", alpha=0.6, density=True)
    plt.legend(loc="best")
    plt.title(title)
    plt.savefig(outputname, format="png", dpi=300)
    LOGGER.info(f"Plotted intermediate beta histogram, saved as {outputname}.")


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
