import pathlib

from copy import deepcopy

import numpy as np
import pytest
import scipy.stats as st

from pyhdtoolkit.maths import stats_fitting
from pyhdtoolkit.maths import utils as mutils

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
REF_DISTRIBUTIONS = deepcopy(stats_fitting.DISTRIBUTIONS)


@pytest.mark.parametrize(
    "input_dict",
    [
        {st.chi: "Chi"},
        {st.chi2: "Chi-Square"},
        {st.expon: "Exponential"},
        {st.laplace: "Laplace"},
        {st.lognorm: "LogNorm"},
        {st.norm: "Normal"},
        REF_DISTRIBUTIONS,  # Putting back the default one to not mess other tests
    ],
)
def test_setting_distributions_dict(input_dict):
    stats_fitting.set_distributions_dict(input_dict)
    assert input_dict == stats_fitting.DISTRIBUTIONS


@pytest.mark.flaky(max_runs=3, min_passes=1)
@pytest.mark.parametrize("tested_distribution", [st.chi, st.laplace])
@pytest.mark.parametrize("degrees_of_freedom", list(range(3, 8)))
def test_best_distribution_fit_with_df(tested_distribution, degrees_of_freedom):
    """
    Testing the right distribution is fit, for scipy.stats rvs distributions with a degrees
    of freedom input.
    """
    # Don't waste time trying to fit distributions that are very different
    stats_fitting.set_distributions_dict({st.chi: "Chi", st.laplace: "Laplace", st.norm: "Normal"})
    points = tested_distribution.rvs(degrees_of_freedom, size=100_000)
    guessed_distribution, _ = stats_fitting.best_fit_distribution(points)
    assert guessed_distribution == tested_distribution
    stats_fitting.set_distributions_dict(REF_DISTRIBUTIONS)


@pytest.mark.flaky(max_runs=3, min_passes=1)
@pytest.mark.parametrize("tested_distribution", [st.lognorm])
@pytest.mark.parametrize("shape", [0.1, 0.3, 0.5, 0.7, 0.954])
def test_best_distribution_fit_with_shape(tested_distribution, shape):
    """
    Testing the right distribution is fit, for scipy.stats rvs distributions with a degrees
    of freedom input.
    """
    # Don't waste time trying to fit distributions that are very different
    stats_fitting.set_distributions_dict({st.lognorm: "LogNorm", st.norm: "Normal"})
    points = tested_distribution.rvs(shape, size=100_000)
    guessed_distribution, _ = stats_fitting.best_fit_distribution(points)
    assert guessed_distribution == tested_distribution
    stats_fitting.set_distributions_dict(REF_DISTRIBUTIONS)


@pytest.mark.flaky(max_runs=3, min_passes=1)
@pytest.mark.parametrize("tested_distribution", [st.expon, st.laplace, st.norm])
def test_best_distribution_fit(tested_distribution):
    """
    Testing the right distribution is fit, for scipy.stats rvs distributions with no special
    parameter input.
    """
    # Don't waste time trying to fit distributions that are very different
    stats_fitting.set_distributions_dict({st.expon: "Exponential", st.laplace: "Laplace", st.norm: "Normal"})
    points = tested_distribution.rvs(size=100_000)
    guessed_distribution, _ = stats_fitting.best_fit_distribution(points)
    assert guessed_distribution == tested_distribution
    stats_fitting.set_distributions_dict(REF_DISTRIBUTIONS)


@pytest.mark.flaky(max_runs=3, min_passes=1)
@pytest.mark.parametrize("degrees_of_freedom", [4, 5, 6, 7])
def test_make_pdf(degrees_of_freedom):
    """
    Can test that the generated pdf is good by checking the mode for a chi2
    -> happens at df - 2. Make it sweat by generating a distribution and having a fit first.
    """
    data: np.ndarray = st.chi2(degrees_of_freedom).rvs(50_000)
    best_fit_func, best_fit_params = stats_fitting.best_fit_distribution(data, 200)
    pdf = stats_fitting.make_pdf(best_fit_func, best_fit_params)
    pdf.idxmax() == pytest.approx(degrees_of_freedom - 2, rel=1e-2)


@pytest.mark.parametrize(("value", "result"), [(1, 0), (10, 1), (0.0311, -2), (5e-7, -7)])
def test_magnitude(value, result):
    assert mutils.get_magnitude(value) == result


def test_mag_and_string(_to_scale, _scaled):
    scaled, mag_str = mutils.get_scaled_values_and_magnitude_string(_to_scale)
    assert np.allclose(scaled, _scaled)
    assert mag_str == "{-1}"


def test_mag_and_string_forced_scale(_to_scale, _force_scaled):
    scaled, mag_str = mutils.get_scaled_values_and_magnitude_string(_to_scale, force_magnitude=2)
    assert np.allclose(scaled, _force_scaled)
    assert mag_str == "{-2}"


# ---------------------- Utilities ---------------------- #


@pytest.fixture
def _to_scale() -> np.ndarray:
    return np.load(INPUTS_DIR / "maths" / "to_scale.npy")


@pytest.fixture
def _scaled() -> np.ndarray:
    return np.load(INPUTS_DIR / "maths" / "scaled.npy")


@pytest.fixture
def _force_scaled() -> np.ndarray:
    return np.load(INPUTS_DIR / "maths" / "force_scaled.npy")
