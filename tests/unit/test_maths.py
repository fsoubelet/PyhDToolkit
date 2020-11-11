from copy import deepcopy

import numpy as np
import pytest
import scipy.stats as st

import pyhdtoolkit.maths.nonconvex_phase_sync as nps

from pyhdtoolkit.maths import stats_fitting

REF_DISTRIBUTIONS = deepcopy(stats_fitting.DISTRIBUTIONS)


class TestPhaseReconstructor:
    """
    Only testing that the final result is good, considering if anything in between goes wrong the
    end result will be way off. Introduced noise doesn't have more than 1 degree stdev,
    as the highest I've found in LHC was 0.7270 for the low-low bpm combination. Number of BPMs
    varyto emulate different machines, 569 is here specifically because it's how many we have in
    the LHC right now (minus shenanigans of double plane BPMs).
    """

    @pytest.mark.parametrize("input_matrix", [np.random.rand(250, 250), np.random.rand(2, 10)])
    @pytest.mark.parametrize("expected_exception", [ValueError])
    def test_non_hermitian_input(self, input_matrix, expected_exception):
        with pytest.raises(expected_exception):
            _ = nps.PhaseReconstructor(input_matrix)

    @pytest.mark.flaky(max_runs=3, min_passes=1)
    @pytest.mark.parametrize(
        "noise_stdev_degrees", [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 1]
    )
    @pytest.mark.parametrize("n_bpms", [50, 250, 500, 569, 750])
    def test_reconstructor_matrix(self, noise_stdev_degrees, n_bpms):
        signal = _create_random_phase_values(low=0, high=80, n_values=n_bpms, dist="uniform")
        m_meas = _create_meas_matrix_from_values_array(signal)
        m_noise = _create_2d_gaussian_noise(mean=0, stdev=noise_stdev_degrees, shape=m_meas.shape)
        c_hermitian = np.exp(1j * np.deg2rad(m_meas + m_noise))

        pr = nps.PhaseReconstructor(c_hermitian)
        assert isinstance(pr.reconstructor_matrix, np.ndarray)
        assert pr.reconstructor_matrix.shape == c_hermitian.shape

    @pytest.mark.flaky(max_runs=3, min_passes=1)
    @pytest.mark.parametrize(
        "noise_stdev_degrees", [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 1]
    )
    @pytest.mark.parametrize("n_bpms", [50, 250, 500, 569, 750])
    def test_reconstruction(self, noise_stdev_degrees, n_bpms):
        signal = _create_random_phase_values(low=0, high=80, n_values=n_bpms, dist="uniform")
        m_meas = _create_meas_matrix_from_values_array(signal)
        m_noise = _create_2d_gaussian_noise(mean=0, stdev=noise_stdev_degrees, shape=m_meas.shape)
        m_noised_meas = m_meas + m_noise
        c_hermitian = np.exp(1j * np.deg2rad(m_noised_meas))
        pr = nps.PhaseReconstructor(c_hermitian)
        complex_eigenvector_method_result = pr.reconstruct_complex_phases_evm()
        reconstructed = np.abs(
            pr.convert_complex_result_to_phase_values(complex_eigenvector_method_result, deg=True)
        ).reshape(n_bpms,)
        assert np.allclose(reconstructed, signal, atol=0.1, rtol=1e-1)


class TestStatsFitting:
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
    def test_setting_distributions_dict(self, input_dict):
        stats_fitting.set_distributions_dict(input_dict)
        assert stats_fitting.DISTRIBUTIONS == input_dict

    @pytest.mark.flaky(max_runs=3, min_passes=1)
    @pytest.mark.parametrize("tested_distribution", [st.chi, st.laplace])
    @pytest.mark.parametrize("degrees_of_freedom", list(range(3, 8)))
    def test_best_distribution_fit_with_df(self, tested_distribution, degrees_of_freedom):
        """
        Testing the right distribution is fit, for scipy.stats rvs distributions with a degrees
        of freedom input.
        """
        # Don't waste time trying to fit distributions that are very different
        stats_fitting.set_distributions_dict(
            {st.chi: "Chi", st.laplace: "Laplace", st.norm: "Normal"}
        )
        points = tested_distribution.rvs(degrees_of_freedom, size=100_000)
        guessed_distribution, _ = stats_fitting.best_fit_distribution(points)
        assert guessed_distribution == tested_distribution
        stats_fitting.set_distributions_dict(REF_DISTRIBUTIONS)

    @pytest.mark.flaky(max_runs=3, min_passes=1)
    @pytest.mark.parametrize("tested_distribution", [st.lognorm])
    @pytest.mark.parametrize("shape", [0.1, 0.3, 0.5, 0.7, 0.954])
    def test_best_distribution_fit_with_shape(self, tested_distribution, shape):
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
    @pytest.mark.parametrize("several_runs_avoid_flukes", list(range(10)))
    def test_best_distribution_fit(self, tested_distribution, several_runs_avoid_flukes):
        """
        Testing the right distribution is fit, for scipy.stats rvs distributions with no special
        parameter input.
        """
        # Don't waste time trying to fit distributions that are very different
        stats_fitting.set_distributions_dict(
            {st.expon: "Exponential", st.laplace: "Laplace", st.norm: "Normal"}
        )
        points = tested_distribution.rvs(size=100_000)
        guessed_distribution, _ = stats_fitting.best_fit_distribution(points)
        assert guessed_distribution == tested_distribution
        stats_fitting.set_distributions_dict(REF_DISTRIBUTIONS)

    @pytest.mark.flaky(max_runs=3, min_passes=1)
    @pytest.mark.parametrize("degrees_of_freedom", [4, 5, 6, 7])
    def test_make_pdf(self, degrees_of_freedom):
        """
        Can test that the generated pdf is good by checking the mode for a chi2
        -> happens at df - 2. Make it sweat by generating a distribution and having a fit first.
        """
        data: np.ndarray = st.chi2(degrees_of_freedom).rvs(50_000)
        best_fit_func, best_fit_params = stats_fitting.best_fit_distribution(data, 200)
        pdf = stats_fitting.make_pdf(best_fit_func, best_fit_params)
        pdf.idxmax() == pytest.approx(degrees_of_freedom - 2, rel=1e-2)


# ---------------------- Utilities ---------------------- #


def _create_random_phase_values(low: float, high: float, n_values: int, dist: str) -> np.ndarray:
    """
    Returns fake generated phase values. They are ascending by default.

    Args:
        low: lowest value, first value will always be 0.
        high: highest value.
        n_values: number of values to generate.
        dist: distribution type required. Will be uniform or linspace.

    Returns:
        A `numpy.ndarray` of shape (n_values,) with the generated values.
    """
    if dist == "linspace":
        values = np.linspace(low, high, n_values)
    elif dist == "uniform":
        values = np.sort(np.random.default_rng().uniform(low, high, n_values))
    else:
        raise ValueError(
            "Provided parameter 'distribution' should be either 'linspace' or 'uniform'."
        )
    values[0] = 0
    return values


def _create_meas_matrix_from_values_array(values_array: np.ndarray) -> np.ndarray:
    """
    For testing purposes. Returns the deltas measurements matrix from an array of values.

    Args:
        values_array: the values of phases at your N BPMs, in a (1, N) shaped `numpy.ndarray`.

    Returns:
        The matrix, as a `numpy.ndarray`.
    """
    return np.array([[i - j for i in values_array] for j in values_array], dtype=float)


def _create_2d_gaussian_noise(mean: float, stdev: float, shape: tuple) -> np.ndarray:
    """
    Generates a 2D Gaussian distribution, makes it antisymmetric and returns it.

    Args:
        mean:  mean of the distribution, should be 0 for us (since we add to the ideal M_meas).
        stdev:  standard deviation of the distribution, should be in degrees if M_meas is given
        in degrees, in radians otherwise.
        shape: the shape of the matrix to create, should be M_meas.shape, aka (n_bpms, n_bpms).

    Returns:
        A  Gaussian, anti-symmetric, 2D-shaped `numpy.ndarray`.
    """
    gaussian_2d_mat = np.random.default_rng().normal(mean, stdev, size=shape)
    upper_triangle = np.triu(gaussian_2d_mat)
    return upper_triangle - upper_triangle.T
