"""
.. _maths-stats-fitting:

Stats Fitting
-------------

Module implementing methods to find the best
fit of statistical distributions to data.
"""

from __future__ import annotations

import warnings

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt  # noqa: F401 | if omitted, get AttributeError: module 'matplotlib' has no attribute 'axes'
import numpy as np
import pandas as pd
import scipy.stats as st

from loguru import logger

if TYPE_CHECKING:
    from matplotlib.axes import Axes


# Distributions to check #
DISTRIBUTIONS: dict[st.rv_continuous, str] = {
    st.chi: "Chi",
    st.chi2: "Chi-Square",
    st.expon: "Exponential",
    st.laplace: "Laplace",
    st.lognorm: "LogNorm",
    st.norm: "Normal",
}


def set_distributions_dict(dist_dict: dict[st.rv_continuous, str]) -> None:
    """
    .. versionadded:: 0.5.0

    Sets ``DISTRIBUTIONS`` as the provided `dict`. This allows the user to
    define the distributions to try and fit against the data. One can find
    an example use of this function in the :ref:`distribution fitting
    gallery <demo-distributions-fitting>`.

    Warning
    -------
        This function modifies the global `DISTRIBUTIONS` `dict` that is used
        by other functions in this module. It's not the cleanest way to do
        things that you'll ever see.

    Parameters
    ----------
    dist_dict : dict[st.rv_continuous, str]
        dictionnary with the wanted distributions, in the same format as the
        ``DISTRIBUTIONS`` dict, aka with a `scipy.stats` generator object as
        key, and a string representation of their name as value.

    Example
    -------
        .. code-block:: python

            import scipy.stats as st

            tested_dists = {st.chi: "Chi", st.expon: "Exponential", st.laplace: "Laplace"}
            set_distributions_dict(tested_dists)
    """
    # pylint: disable=global-statement
    logger.debug("Setting tested distributions")
    global DISTRIBUTIONS  # noqa: PLW0603
    DISTRIBUTIONS = dist_dict


def best_fit_distribution(
    data: pd.Series | np.ndarray, bins: int = 200, ax: Axes = None
) -> tuple[st.rv_continuous, tuple[float, ...]]:
    r"""
    .. versionadded:: 0.5.0

    Model data by finding the best fit candidate distribution among those
    in ``DISTRIBUTIONS``. One can find an example use of this function in
    the :ref:`gallery <demo-distributions-fitting>`.

    Parameters
    ----------
    data : Union[pd.Series, np.ndarray]
        A `pandas.Series` or `numpy.ndarray` with your distribution data.
    bins : int
        The number of bins to decompose your data in before fitting.
    ax : matplotlib.axes.Axes, optional
        The `matplotlib.axes.Axes` on which to plot the probability
        density function of the different fitted distributions. This
        should be provided as the axis on which the distribution data
        is plotted, as it will add to that plot. If not provided, no
        plotting will be done.

    Returns
    -------
    tuple[st.rv_continuous, tuple[float, ...]]
        A `tuple` containing the `scipy.stats` generator corresponding
        to the best fit to the data among the provided candidates, and
        the parameters for said generator to best fit the data.

    Example
    -------
        .. code-block:: python

            best_fit_func, best_fit_params = best_fit_distribution(data, 200, axis)
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
                *args, loc, scale = params

                logger.debug(f"Calculating PDF goodness of fit and error for distribution '{distname}'")
                pdf = distribution.pdf(x, *args, loc=loc, scale=scale)
                sse = np.sum(np.power(y - pdf, 2.0))

                try:
                    if ax:  # pragma: no cover
                        logger.debug(f"Plotting fitted PDF for distribution '{distname}'")
                        pd.Series(pdf, x).plot(ax=ax, label=f"{distname} fit", alpha=1)
                except Exception:  # pragma: no cover  # noqa: BLE001
                    logger.exception(f"Plotting distribution '{distname}' failed")

                logger.debug(f"Identifying if distribution '{distname}' is a better fit than previous tries")
                if best_sse > sse > 0:
                    best_distribution = distribution
                    best_params = params
                    best_sse = sse
        except Exception:  # noqa: BLE001  # pragma: no cover
            logger.exception(f"Trying to fit distribution '{distname}' failed and aborted")

    logger.info(f"Found a best fit: '{DISTRIBUTIONS[best_distribution]}' distribution")
    return best_distribution, best_params


def make_pdf(distribution: st.rv_continuous, params: tuple[float, ...], size: int = 25_000) -> pd.Series:
    """
    .. versionadded:: 0.5.0

    Generates a `pandas.Series` for the distributions's Probability Distribution
    Function. This Series will have axis values as index, and PDF values as
    column. One can find an example use of this function in the :ref:`distribution
    fitting gallery <demo-distributions-fitting>`.

    Parameters
    ----------
    distribution : scipy.stats.rv_continuous
        The `scipy.stats` generator for the distribution to generate the PDF from.
    params : tuple[float, ...]
        The parameters for this generator, as given back by the fit to data or
        as guessed from the user.
    size : int
        The number of points to evaluate the PDF on.

    Returns
    -------
    pandas.Series
        A `pandas.Series` with the PDF as values, and the corresponding axis
        values as index.

    Example
    -------
        .. code-block:: python

            best_fit_func, best_fit_params = best_fit_distribution(data, 200, axis)
            pdf = fitting.make_pdf(best_fit_func, best_fit_params)
    """
    # Separate parts of parameters
    *args, loc, scale = params

    logger.debug("Getting sane start and end points of distribution")
    if args:
        start = distribution.ppf(0.01, *args, loc=loc, scale=scale)
        end = distribution.ppf(0.99, *args, loc=loc, scale=scale)
    else:  # pragma: no cover
        start = distribution.ppf(0.01, loc=loc, scale=scale)
        end = distribution.ppf(0.99, loc=loc, scale=scale)

    logger.debug("Building PDF")
    x = np.linspace(start, end, size)
    y = distribution.pdf(x, *args, loc=loc, scale=scale)
    return pd.Series(y, x)
