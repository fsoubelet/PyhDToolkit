"""
Script scripts.triplet_errors.plotting_functions
------------------------------------------------

Created on 2019.06.15
:author: Felix Soubelet

A collection of functions that will be useful to plot the results from GridCompute Algorithm.
"""

import os
import pathlib

from typing import List

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from loguru import logger

if os.environ.get("Display", "") == "":
    logger.warning("Display configuration error found. Using non-interactive Agg backend")
    matplotlib.use("Agg")


def plot_betas_across_machine(
    s_values: List[float],
    betx_values: List[float],
    bety_values: List[float],
    error_type: str,
    error_value: str,
) -> None:
    """
    Plot beta functions across the machine. Save according to simulation scenario.
    Creates a plot of the horizontal and vertical beta functions across the whole machine. Gives a
    title generated according to the error type and error value. Saves in dedicated subfolder.

    Args:
        s_values (List[float]): the values of the s axis.
        betx_values (List[float]): horizontal betatron function values accross the machine.
        bety_values (List[float]): vertical betatron function values accross the machine.
        error_type (str): which error you have simulated too get those results.
        error_value (str): the value of the error you used in your simulations.
    """
    if error_type == "TFERROR":
        title = f"r'Beta values, hllhc1.3, 15cm optics, relative field error: {error_value}[$10^{-4}$]'"
    elif error_type == "MISERROR":
        title = f"r'Beta values, hllhc1.3 15cm optics, misalignment: {error_value}[mm]'"
    else:
        logger.warning(f"Invalid error parameter {error_type} provided, aborting plot")
        raise ValueError("Error parameter should be either `TFERROR` or `MISERROR`.")

    output_dir = pathlib.Path("beta_plots") / f"{error_type}" / f"{error_value}"
    if not output_dir.is_dir():
        logger.info(f"Creating directory {output_dir}")
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
    plt.savefig(f"beta_plots/{error_type}/{error_value}/betas_across_machine.png", format="pdf", dpi=300)
    logger.info(f"Plotted betas for {error_type} {error_value}")


def plot_bbing_max_errorbar(
    errors: List[float], beta_beatings_df: pd.DataFrame, stdev_df: pd.DataFrame, plane: str, figname: str,
) -> None:
    """
    Plot beta-beating values, with error bars, as a function of the error values. Save according
    to plotted plane. Creates a plot of the horizontal or vertical beta-beatings across the range
    of simulated error values. Gives a title generated according to the error type and error
    value. Saves in dedicated subfolder.

    Args:
        errors (List[float]): the different error values simulated.
        beta_beatings_df (pd.DataFrame): the resulting beta-beating values.
        stdev_df (pd.DataFrame): the standard deviations for those values.
        plane (str): the name of the plane to plot.
        figname (str): how to name the file when exporting the plot.
    """

    if plane.lower() == "horizontal":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.tferror_bbx,
            yerr=stdev_df.stdev_tf_x,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.misserror_bbx,
            yerr=stdev_df.stdev_miss_x,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(
            errors, beta_beatings_df.max_tferror_bbx, "^", color="C0", label="Max Value from Field Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.max_misserror_bbx,
            "^",
            color="C1",
            label="Max Value from Misalignment Errors",
        )
        axes.set_xlabel(r"Relative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-Beating Against Triplet Errors, {plane} Plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="pdf", dpi=300)

    elif plane.lower() == "vertical":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.tferror_bby,
            yerr=stdev_df.stdev_tf_y,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.misserror_bby,
            yerr=stdev_df.stdev_miss_y,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(
            errors, beta_beatings_df.max_tferror_bby, "^", color="C0", label="Max Value from Field Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.max_misserror_bby,
            "^",
            color="C1",
            label="Max Value from Misalignment Errors",
        )
        axes.set_xlabel(r"Relative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-beating against triplet errors, {plane} plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="pdf", dpi=300)

    else:
        logger.warning(f"Invalid plane parameter {plane} provided, aborting plot")
        raise ValueError("Plane parameter should be either `Horizontal` or `Vertical`")
    logger.info(f"Plotted beta-beatings with error bars for {plane.lower()} plane")


def plot_bbing_with_ips_errorbar(
    errors: List[float], beta_beatings_df: pd.DataFrame, stdev_df: pd.DataFrame, plane: str, figname: str,
) -> None:
    """
    Plot beta-beating values, with error bars, as a function of the error values. Save according
    to plotted plane. Creates a plot of the horizontal or vertical beta-beatings across the range
    of simulated error values, with the addition of the beta-beating value at IPs. Gives a title
    generated according to the error type and error value. Saves in dedicated subfolder.

    Args:
        errors (List[float]): list with different error values simulated.
        beta_beatings_df (pd.DataFrame): the resulting beta-beating values.
        stdev_df (pd.DataFrame): the standard deviations for those values.
        plane (str): the name of the plane to plot.
        figname (str): how to name the file when exporting the plot.
    """

    if plane.lower() == "horizontal":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.tferror_bbx,
            yerr=stdev_df.stdev_tf_x,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.misserror_bbx,
            yerr=stdev_df.stdev_miss_x,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip1_tferror_bbx,
            "^",
            color="C0",
            label="IP1 Beta-Beating Value from Field Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip1_misserror_bbx,
            "^",
            color="C1",
            label="IP1 Beta-Beating Value from Misalignment Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip5_tferror_bbx,
            "x",
            color="C0",
            label="IP5 Beta-Beating Value from Field Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip5_misserror_bbx,
            "x",
            color="C1",
            label="IP5 Beta-Beating Value from Misalignment Errors",
        )
        axes.set_xlabel(r"Relative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-Beating Against Triplet Errors, {plane} Plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="pdf", dpi=300)

    elif plane.lower() == "vertical":
        _, axes = plt.subplots(1, 1, figsize=(8, 6))
        axes.errorbar(
            errors,
            beta_beatings_df.tferror_bby,
            yerr=stdev_df.stdev_tf_y,
            color="C0",
            label="Global Beta-Beating from Field Errors",
        )
        axes.errorbar(
            errors,
            beta_beatings_df.misserror_bby,
            yerr=stdev_df.stdev_miss_y,
            color="C1",
            label="Global Beta-Beating from Misalignment Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip1_tferror_bby,
            "^",
            color="C0",
            label="IP1 Beta-Beating Value from Field Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip1_misserror_bby,
            "^",
            color="C1",
            label="IP1 Beta-Beating Value from Misalignment Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip5_tferror_bby,
            "x",
            color="C0",
            label="IP5 Beta-Beating Value from Field Errors",
        )
        axes.plot(
            errors,
            beta_beatings_df.ip5_misserror_bby,
            "x",
            color="C1",
            label="IP5 Beta-Beating Value from Misalignment Errors",
        )
        axes.set_xlabel(r"TRelative Field Error [$10^{-4}$] or Longitudinal Misalignment [mm]", fontsize=15)
        axes.set_ylabel(r"$\Delta \beta / \beta$ [%]", fontsize=15)
        plt.tight_layout()
        plt.title(f"Beta-Beating Against Triplet Errors, {plane} Plane", fontsize=15)
        plt.legend(loc="best")
        plt.savefig(figname, format="pdf", dpi=300)

    else:
        logger.warning(f"Invalid plane parameter {plane} provided, aborting plot")
        raise ValueError("Plane parameter should be either `Horizontal` or `Vertical`")
    logger.info(f"Plotted beta-beatings (including IPs) with error bars for {plane.lower()} plane")


def plot_intermediate_beta_histograms(
    betasx: List[float], betasy: List[float], error_val: float, title: str, outputname: str
) -> None:
    """
    Plot histogram distribution for betas at seeds.

    Args:
        betasx (List[float]): horizontal beta values for all seeds for a specific error value.
        betasy (List[float]): vertical beta values for all seeds for a specific error value.
        error_val (float): the error value.
        title (str): the title to give the figure.
        outputname (str): the name to give the file saving the figure.
    """
    plt.hist(betasx, bins=50, label=f"{error_val}, horizontal", alpha=0.6, density=True)
    plt.hist(betasy, bins=50, label=f"{error_val}, vertical", alpha=0.6, density=True)
    plt.legend(loc="best")
    plt.title(title)
    plt.savefig(outputname, format="pdf", dpi=300)
    logger.info(f"Plotted intermediate beta histogram, saved as {outputname}")
