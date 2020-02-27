"""
Created on 2020.02.06
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 module implementing methods to find the best fit of statistical distributions to data.
"""
import warnings

import numpy as np
import pandas as pd
import scipy.stats as st

from fsbox import logging_tools

LOGGER = logging_tools.get_logger(__name__)
# Distributions to check #
DISTRIBUTIONS = {
    st.chi: "Chi",
    st.chi2: "ChiSquared",
    st.expon: "Exponential",
    st.laplace: "Laplace",
    st.lognorm: "LogNorm",
    st.norm: "Normal",
}


def set_distributions_dict(dist_dict: dict = None) -> None:
    """
    Sets DISTRIBUTIONS as the provided dict. This is useful to define only the ones you want to try out.
    :param dist_dict: dictionnary with the wanted distributions, in the format of DISTRIBUTIONS. This should be the
    scipy.stats generator objects as keys, and a string representation of their name as value.
    :return: nothing, modifies the global DISTRIBUTIONS dict called by other functions.
    """
    # pylint: disable=global-statement
    global DISTRIBUTIONS
    DISTRIBUTIONS = dist_dict


def best_fit_distribution(data: pd.Series, bins: int = 200, ax=None) -> tuple:
    """
    Model data by finding best fit candidate distribution among those in DISTRIBUTIONS.
    :param data: a pandas.Series with your distribution data as values.
    :param bins: the number of bins to decompose your data in before performing fittings.
    :param ax: the matplotlib.axes._subplots.AxesSubplot object on which to plot the pdf of tried functions.
    This should be provided as the ax on which you plotted your distribution.
    :return: a tuple containing the scipy.stats generator corresponding to the best fit candidate, and the
    parameters to give said generator to get this fit.
    """
    # pylint: disable=too-many-locals
    # Get histogram of original data
    y, x = np.histogram(data, bins=bins, density=True)
    x = (x + np.roll(x, -1))[:-1] / 2.0

    # Best holders
    best_distribution = st.norm
    best_params = (0.0, 1.0)
    best_sse = np.inf

    # Estimate distribution parameters from data
    for distribution, distname in DISTRIBUTIONS.items():
        try:
            with warnings.catch_warnings():  # Ignore warnings from data that can't be fit
                warnings.filterwarnings("ignore")

                # Fit distribution to data and separate parts of returned parameters
                params = distribution.fit(data)
                arg = params[:-2]
                loc = params[-2]
                scale = params[-1]

                # Calculate fitted PDF and error with fit in distribution
                pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)
                sse = np.sum(np.power(y - pdf, 2.0))

                try:
                    if ax:
                        pd.Series(pdf, x).plot(ax=ax, label=f"{distname} fit", alpha=1, lw=2)
                except Exception:
                    LOGGER.warning(f"Plotting distribution '{distname}' failed.")

                # identify if this distribution is better
                if best_sse > sse > 0:
                    best_distribution = distribution
                    best_params = params
                    best_sse = sse
        except Exception:
            LOGGER.warning(f"Trying to fit distribution '{distname}' failed and aborted.")

    return best_distribution, best_params


def make_pdf(distribution, params, size: int = None) -> pd.Series:
    """
    Generate a pandas Series for the distributions's Probability Distribution Function.
    This Series will have axis values as index, and PDF values as values.
    :param distribution: a scipy.stats generator object, similar to those found in DISTRIBUTIONS for instance.
    :param params: the parameters given back by the fit.
    :param size: the number of points to evaluate.
    :return: a pandas.Series object with the PDF as values, corresponding axis values as index.
    """
    size = 10_000 if size is None else size
    # Separate parts of parameters
    args = params[:-2]
    loc = params[-2]
    scale = params[-1]

    # Get sane start and end points of distribution
    start = (
        distribution.ppf(0.01, *args, loc=loc, scale=scale) if args else distribution.ppf(0.01, loc=loc, scale=scale)
    )
    end = distribution.ppf(0.99, *args, loc=loc, scale=scale) if args else distribution.ppf(0.99, loc=loc, scale=scale)

    # Build PDF and turn into pandas Series
    x = np.linspace(start, end, size)
    y = distribution.pdf(x, loc=loc, scale=scale, *args)
    return pd.Series(y, x)


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
