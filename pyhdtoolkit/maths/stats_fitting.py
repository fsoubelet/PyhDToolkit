"""
Module maths.stats_fitting
--------------------------

Created on 2020.02.06
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 module implementing methods to find the best fit of statistical distributions
to data.
"""
import warnings

import numpy as np
import pandas as pd
import scipy.stats as st

from loguru import logger

# Distributions to check #
DISTRIBUTIONS = {
    st.chi: "Chi",
    st.chi2: "Chi-Square",
    st.expon: "Exponential",
    st.laplace: "Laplace",
    st.lognorm: "LogNorm",
    st.norm: "Normal",
}


def set_distributions_dict(dist_dict: dict = None) -> None:
    """
    Sets DISTRIBUTIONS as the provided dict. This is useful to define only the ones you want to
    try out.

    Args:
        dist_dict: dictionnary with the wanted distributions, in the format of DISTRIBUTIONS. This
                   should be the
        scipy.stats generator objects as keys, and a string representation of their name as value.

    Returns:
        Nothing, modifies the global DISTRIBUTIONS dict called by other functions.
    """
    # pylint: disable=global-statement
    logger.debug("Setting tested distributions")
    global DISTRIBUTIONS
    DISTRIBUTIONS = dist_dict


def best_fit_distribution(data: pd.Series, bins: int = 200, ax=None) -> tuple:
    """
    Model data by finding best fit candidate distribution among those in DISTRIBUTIONS.

    Args:
        data: a pandas.Series or numpy.ndarray with your distribution data as values.
        bins: the number of bins to decompose your data in before performing fittings.
        ax: the matplotlib.axes._subplots.AxesSubplot object on which to plot the pdf of tried
            functions. This should be provided as the ax on which you plotted your distribution.

    Returns:
        A tuple containing the scipy.stats generator corresponding to the best fit candidate, and the
        parameters to give said generator to get this fit.
    """
    # pylint: disable=too-many-locals
    logger.debug(f"Getting histogram of original data, in {bins} bins")
    y, x = np.histogram(data, bins=bins, density=True)
    x = (x + np.roll(x, -1))[:-1] / 2.0

    logger.debug("Creating initial guess")
    best_distribution = st.norm
    best_params = (0.0, 1.0)
    best_sse = np.inf

    # Estimate distribution parameters from data
    for distribution, distname in DISTRIBUTIONS.items():
        try:
            with warnings.catch_warnings():  # Ignore warnings from data that can't be fit
                warnings.filterwarnings("ignore")

                logger.debug(f"Trying to fit distribution '{distname}'")
                params = distribution.fit(data)
                arg = params[:-2]
                loc = params[-2]
                scale = params[-1]

                logger.debug(
                    f"Calculating PDF goodness of fit and error for distribution '{distname}'"
                )
                pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)
                sse = np.sum(np.power(y - pdf, 2.0))

                try:
                    if ax:
                        logger.debug(f"Plotting fitted PDF for distribution '{distname}'")
                        pd.Series(pdf, x).plot(ax=ax, label=f"{distname} fit", alpha=1, lw=2)
                except Exception:
                    logger.exception(f"Plotting distribution '{distname}' failed, moving on.")

                logger.debug(
                    f"Identifying if distribution '{distname}' is a better fit than previous tries"
                )
                if best_sse > sse > 0:
                    best_distribution = distribution
                    best_params = params
                    best_sse = sse
        except Exception:
            logger.exception(f"Trying to fit distribution '{distname}' failed and aborted")
    logger.info(f"Found a best fit: '{DISTRIBUTIONS[best_distribution]}' distribution. Now ending")
    return best_distribution, best_params


def make_pdf(distribution, params, size: int = 25_000) -> pd.Series:
    """
    Generate a pandas Series for the distributions's Probability Distribution Function. This Series
    will have axis values as index, and PDF values as values.

    Args:
        distribution: a scipy.stats generator object, similar to those found in DISTRIBUTIONS.
        params: the parameters given back by the fit.
        size: the number of points to evaluate.

    Returns:
        A pandas.Series object with the PDF as values, corresponding axis values as index.
    """
    # Separate parts of parameters
    args = params[:-2]
    loc = params[-2]
    scale = params[-1]

    logger.debug("Getting sane start and end points of distribution")
    start = (
        distribution.ppf(0.01, *args, loc=loc, scale=scale)
        if args
        else distribution.ppf(0.01, loc=loc, scale=scale)
    )
    end = (
        distribution.ppf(0.99, *args, loc=loc, scale=scale)
        if args
        else distribution.ppf(0.99, loc=loc, scale=scale)
    )

    logger.debug("Building PDF.")
    x = np.linspace(start, end, size)
    y = distribution.pdf(x, loc=loc, scale=scale, *args)

    logger.debug("Casting to pandas.Series object")
    return pd.Series(y, x)
