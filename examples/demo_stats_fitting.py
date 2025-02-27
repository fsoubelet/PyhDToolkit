"""
.. _demo-distributions-fitting:

=====================
Distributions Fitting
=====================

This example shows how to use the `~.maths.stats_fitting.best_fit_distribution` function
to determine which statistical distribution best first a given data set, and plot the
results together.

In this example, we'll go further and see how by using the probability density function of
a fit to a chi-square_ distrubtion, one can get knowledge of the underlying normal distributions
it originated from.

.. _chi-square: https://en.wikipedia.org/wiki/Chi-squared_distribution
"""

# sphinx_gallery_thumbnail_number = 2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import scipy.stats as st

from pyhdtoolkit.maths import stats_fitting as fitting
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.plotting.utils import set_arrow_label
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# We will for this example create a chi-square_ distribution with known parameters. As the
# chisquare distribution is based on deviations of independent, normal distribution variables,
# we will create a normal distribution with K degrees of freedom, and compute the associated
#
# .. math::
#
#    \sigma_{j}^{2} = \frac{1}{K} \cdot \sum_{i=1}^{K} \big(X_{i} - \bar{X} \big)^{2}
#
# By repeating so a few thousand times, we get a chi-square distribution.


def chi_square_dist(num: int, meas_used: int) -> np.ndarray:
    """
    Generates a chi-square distribution of *num* elements, each computed
    from a normal distribution of *meas_used* elements.

    Args:
        num (int): number of elements for the generated distribution.
        meas_used (int): number of values for each.

    Returns:
        The resulting distribution as a `numpy.ndarray`.
    """
    result = []
    for _ in range(num):
        norm_dist = np.random.default_rng().normal(loc=0, scale=1, size=meas_used)
        result.append(np.sum(np.square([i - np.mean(norm_dist) for i in norm_dist])))
    return np.array(result)


def chi_dist(num: int, meas_used: int) -> np.ndarray:
    """
    Generates a chi distribution of *num* elements, each computed from a
    normal distribution of *meas_used* elements.

    Args:
        num (int): number of elements for the generated distribution.
        meas_used (int): number of values for each.

    Returns:
        The resulting distribution as a `numpy.ndarray`.
    """
    result = []
    for _ in range(num):
        norm_dist = np.random.default_rng().normal(loc=0, scale=1, size=meas_used)
        result.append(np.sqrt(np.sum(np.square([i - np.mean(norm_dist) for i in norm_dist]))))
    return np.array(result)


###############################################################################
# Now, from this chi-squared distribution of values, how do we find back the standard deviation
# :math:`\sigma_{0}` of the normal (gaussian) distributions it is computed from?
# Let's first start by fitting a statistical chisquared model to the data!
#
# From there, we can plot the Probability Density Function of our best candidate and see how well
# it fits our data. It should fit very well, and then a good guess of this :math`\sigma_{0}`` is
# based on the index at which to find the peak of the best candidate's PDF.
#
# Since this peak happens at :math:`K - 2`, then we have:
#
# .. math::
#
#    \sigma_{0} = \sqrt{\frac{index\_at\_peak}{(K - 2)}}
#
# .. note::
#     In the case where we use :math:`N` measurements, we have :math:`K = N - 1`` degrees of freedom.
#     This means that :math:`N` measurements lead to a Chisquare(N-1) distribution.
#     As a consequence, it is important to replace :math:`K`` by :math:`N - 1`` in all the equations above,
#     and the normal distribution's stdev estimator becomes:
#
#     .. math::
#
#        \sigma_{0} = \sqrt{\frac{\mathrm{index\_at\_peak}}{(N - 3)}}
#
# Enough talk, see below an example with :math:`N = 5` measurements.

measurements_used = 5
degrees_of_freedom = measurements_used - 1

# Chi-square distribution
sigs = chi_square_dist(50_000, meas_used=measurements_used)
data = pd.Series(sigs)

# Chi distribution
chis = chi_dist(num=50_000, meas_used=measurements_used)
chi_data = pd.Series(chis)

###############################################################################
# For the sake of not over-crowding our plot, let's reduce the amount of statistical
# distributions we will try to fit to the data:

DISTRIBUTIONS = {
    st.chi: "Chi",
    st.chi2: "ChiSquared",
    st.norm: "Normal",
}
fitting.set_distributions_dict(DISTRIBUTIONS)

###############################################################################
# Now we plot our data, and try to fit these three distributions to it, by calling
# the `~.maths.stats_fitting.best_fit_distribution` function:

ax = data.plot(
    kind="hist",
    bins=100,
    density=True,
    alpha=0.6,
    label="Generated Distribution",
    figsize=(20, 12),
)
data_y_lim = ax.get_ylim()

# Find best fit candidate
best_fit_func, best_fit_params = fitting.best_fit_distribution(data, 200, ax)
ax.set_ylim(data_y_lim)

ax.set_title("All Fitted Distributions")
ax.set_ylabel("Normed Hist Counts")
plt.legend()
plt.show()

###############################################################################
# That's nice. We can already see that only the chi-squared distrubtion seems to
# be a good fit. Let's do a new plot with only the best fit's probability density
# function (which we get with the `~.maths.stats_fitting.make_pdf` function) added
# onto the data, and determine its mode:

# Let's get the PDF of the best fit
pdf: pd.Series = fitting.make_pdf(best_fit_func, best_fit_params)

plt.figure(figsize=(20, 12))

ax = pdf.plot(lw=2, label=f"{fitting.DISTRIBUTIONS[best_fit_func]} fit PDF", legend=True)
data.plot(
    kind="hist",
    bins=100,
    density=True,
    alpha=0.5,
    label=f"Generated ({measurements_used - 1} degrees of freedom)",
    legend=True,
    ax=ax,
)
param_names = (
    (best_fit_func.shapes + ", loc, scale").split(", ")
    if best_fit_func.shapes
    else ["loc", "scale"]
)
param_str = ", ".join(
    [f"{k}={v:0.2f}" for k, v in zip(param_names, best_fit_params, strict=False)]
)
dist_str = f"{fitting.DISTRIBUTIONS[best_fit_func]}({param_str})"

# Let's add to the plot some info on the fit's peak
set_arrow_label(
    axis=ax,
    label=f"Measured Mode: {pdf.idxmax():.3f}",
    arrow_position=(pdf.idxmax(), pdf.max()),
    label_position=(1.1 * np.mean(ax.get_xlim()), 0.75 * max(pdf.to_numpy())),
    color="indianred",
    arrow_arc_rad=0.3,
    fontsize=25,
)
plt.vlines(pdf.idxmax(), ymin=0, ymax=max(pdf.to_numpy()), linestyles="--", color="indianred")
ax.set_title("Best fit to distribution:\n" + dist_str)
ax.set_ylabel("Normed Hist Counts")
ax.set_xlabel("x")
ax.legend()

###############################################################################
# We expect a mode of 2, we can check that this is indeed the case. Here we leave
# a nice tolerance to ensure the documentation build does not fail.

assert np.isclose(pdf.idxmax(), 2, rtol=2e-2)


###############################################################################
# With this knowledge, we can now determine the standard deviation of the normal
# distribution we've used to create this chi-square distribution. Remember that
# in the `chi_square_dist` function we have called `np.random.default_rng().normal`
# with ``loc=0`` and ``scale=1``, so we expect here to find a standard deviation of
# one.

factor = (
    np.sqrt(2)
    * scipy.special.gamma((degrees_of_freedom + 1) / 2)
    / scipy.special.gamma(degrees_of_freedom / 2)
)

determined_stdev = chi_data.mean() / factor
assert np.isclose(determined_stdev, 1, rtol=1e-2)  # nice tolerance here too

###############################################################################
# Which we do :)
#
# Bonus: here's a plot of trying to fit all basic distributions to the chi
# distribution generated above.

# Let's reset the distributions dict
DISTRIBUTIONS = {
    st.chi: "Chi",
    st.chi2: "Chi-Square",
    st.expon: "Exponential",
    st.laplace: "Laplace",
    st.lognorm: "LogNorm",
    st.norm: "Normal",
}
fitting.set_distributions_dict(DISTRIBUTIONS)

ac = chi_data.plot(
    kind="hist",
    bins=100,
    density=True,
    alpha=0.6,
    label="Generated Chi Distribution",
    figsize=(20, 12),
)
data_ylim = ac.get_ylim()

# Find best fit candidate
best_fit_func, best_fit_params = fitting.best_fit_distribution(chi_data, 200, ac)
ac.set_ylim(data_ylim)
ac.set_title("All Fitted Distributions")
ac.set_ylabel("Normed Hist Counts")
plt.legend()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.maths.stats_fitting`: `~.maths.stats_fitting.best_fit_distribution`, `~.maths.stats_fitting.make_pdf`
#    - `~.plotting.utils`: `~.plotting.utils.set_arrow_label`
