"""
Created on 2020.01.13
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 implementation of the Nonconvex Phase Synchronisation method found in the
following paper (https://arxiv.org/abs/1601.06114, the algorithm reproduced is page 8). It is used
on phase measurements reconstruction at CERN.


Methodology and Use Case
========================
We consider that from measurements, we can only obtain noisy relative phase advances
mu_{i} - mu_{j} and want a converging solution to reconstruct the different individual
mu_{1}, ...., mu_{n} values.

From measurements, we construct a hermitian matrix C in the shape of:
C_{ij} = z_{i} * bar(z_{j}) = exp(i * (mu_{i} - mu_{j}))
A mock one with random values (500 by 500 as we have 500 BPMs per plane in the LHC) would be:
c_matrix = np.exp(1j * np.random.rand(500, 500))

Considering 4 BPMs, the measurement matrix would be:
M_matrix = [[mu_{1 -> 1}, mu_{1 -> 2}, mu_{1 -> 3}, mu_{1 -> 4}],
            [mu_{2 -> 1}, mu_{2 -> 2}, mu_{2 -> 3}, mu_{2 -> 4}],
            [mu_{3 -> 1}, mu_{3 -> 2}, mu_{3 -> 3}, mu_{3 -> 4}],
            [mu_{4 -> 1}, mu_{4 -> 2}, mu_{4 -> 3}, mu_{4 -> 4}]]

Note two particular properties here:
  - Because our measurements are phase differences, the M_matrix will necessarily have zeros on
    its diagonal (mu_{k -> k} = 0).
  - By definition, since mu_{a -> b} = - mu_{b -> a}, M_matrix is symmetric.
  - Also note that for all computations, M_matrix needs to be initialised in radians!


We can very simply get our C_matrix (see page 1 of referenced paper) with `numpy.exp` which,
applied to a `numpy.ndarray` applies the exponential function element-wise. See reference at
https://docs.scipy.org/doc/numpy/reference/generated/numpy.exp.html

Then follows:  C_matrix = np.exp(1j * M_matrix)
Note that M_matrix being symmetric, then c_matrix will be Hermitian.
Note that M_matrix having zeros in its diagonal, c_matrix will have (1 + 0j) on its diagonal.

With added noise to those values (noise should be included in M_matrix in the case of measurements),
we can reconstruct a good estimator of the original values through the EVM method, provided in the class below.
"""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tfs

from fsbox import logging_tools
from pyhdtoolkit.utils.cmdline import CommandLine

LOGGER = logging_tools.get_logger(__name__)


class PhaseReconstructor:
    """
    Class algorithm to reconstruct your phase values.
    Make sure to provide vectors as `numpy.ndarray` with shape (1, N), N being the dimension.
    """

    def __init__(self, measurements_hermitian_matrix: np.ndarray):
        """
        Initialize your reconstructor object from measurements.
        :param measurements_hermitian_matrix: a `numpy.ndarray` object built from measurements,
        see top of file comment lines on how to build this matrix.
        """
        # Before anything, check that the provided matrix is indeed Hermitian
        if np.allclose(measurements_hermitian_matrix, np.conj(measurements_hermitian_matrix).T):
            self.c_matrix: np.ndarray = measurements_hermitian_matrix
            self.c_matrix_eigenvalues: np.ndarray = np.linalg.eigvalsh(self.c_matrix)
            # Numpy gives the eigenvectors in column form, so transpose is needed there!
            self.c_matrix_eigenvectors: np.ndarray = np.linalg.eigh(self.c_matrix)[-1].T
            self.space_dimension: int = self.c_matrix.shape[0]
        else:
            LOGGER.error("The provided matrix is not Hermitian, aborting.", exc_info=True)
            raise ValueError("Provided matrix should be Hermitian.")

    @property
    def alpha(self) -> np.float64:
        """
        This is a factor used to define the new reconstruction matrix. It is taken either as the
        operator norm of the hermitian noise matrix, or as the max value between 0 and the opposite
        of the min eigenvalue of c_matrix (chosen for implementation, since our noise is included
        in the measurements). See page 8 of the paper for reference.
        :return: a real scalar value, because c_matrix is Hermitian and the eigenvalues of real
        ymmetric or complex Hermitian matrices are always real (see G. Strang, Linear Algebra and
        Its Applications, 2nd Ed., Orlando, FL, Academic Press, Inc., 1980, pg. 222.)
        """
        return np.float64(max(0, np.amin(self.c_matrix_eigenvalues)))

    @property
    def leading_eigenvector(self) -> np.ndarray:
        """
        Return the leading eigenvector of `self.c_matrix`, which is the eigenvector corresponding
        to the max eigenvalue (in absolute value).
        :return: a `numpy.ndarray` object, corresponding to said eigenvector.
        """
        return self.c_matrix_eigenvectors[
            np.where(self.c_matrix_eigenvalues == np.amax(np.absolute(self.c_matrix_eigenvalues)))
        ].reshape((1, self.space_dimension))

    @property
    def reconstructor_matrix(self) -> np.ndarray:
        """
        This is the reconstructor matrix built from `self.c_matrix` and the `alpha` property.
        It is the matrix denoted as \widetilde{C} on page 8 of the reference paper.
        :return: A `numpy.ndarray`, with same dimension as `self.c_matrix`.
        """
        return self.c_matrix + self.alpha * np.identity(self.c_matrix.shape[0])

    def get_eigenvector_estimator(self, eigenvector: np.ndarray) -> np.ndarray:
        """
        Return the eigenvector estimator of a given eigenvector (id est the component-wise
        projection of said eigenvector onto ℂˆ{n}_{1}, see reference paper at page 7 for
        implementation.
        :return: a `numpy.ndarray` object of the same dimension as param `eigenvector`.
        """
        try:
            return eigenvector / np.absolute(eigenvector)
        except RuntimeWarning:  # In case of 0-division, we don't want `inf` values from numpy
            # Generate a random complex vector with same dimension (since `eigenvector` is of
            # dimension N * 1, `numpy.ndarray.size` method will give us N).
            # Remember to initialize a random real and imaginary part.
            e_vect = np.random.randn(eigenvector.size) + 1j * np.random.randn(eigenvector.size)
            while np.absolute(e_vect @ eigenvector) == 0:  # Guarantee that we don't fall back to this edge case.
                e_vect = np.random.randn(eigenvector.size) + 1j * np.random.randn(eigenvector.size)
            return (e_vect @ eigenvector / np.absolute(e_vect @ eigenvector)).reshape((1, self.space_dimension))

    def reconstruct_complex_phases_evm(self) -> np.ndarray:
        """
        Reconstruct simplest estimator fom the eigenvector method. The result is in complex form, and will be radians
        once cast back to real form.
        :return: the complex form of the result as a 'numpy.ndarray' instance.
        """
        return self.get_eigenvector_estimator(self.leading_eigenvector)

    @staticmethod
    def convert_complex_result_to_phase_values(complex_estimator: np.ndarray, deg: bool = False) -> np.ndarray:
        """
        Casts back the complex form of your result to real phase values.
        :param complex_estimator: `numpy.ndarray` instance with the complex form of your result.
        :param deg: if this is set to `True`, the result is cast to degrees (from radians) before
        being returned.
        :return: `numpy.ndarray` with the real phase values of the result.
        """
        return np.apply_along_axis(np.angle, axis=0, arr=complex_estimator, deg=deg)


# ---------- SIMULATIONS / TESTING PURPOSES ---------- #


def create_combinations_matrices_from_twiss(twiss_file: str) -> (np.ndarray, np.ndarray):
    """
    Create combination matrices indicating, for each element, if it is a 'high-high' or 'high-low' (etc) BPM
    combination. Done for each plane, and returns each as a `numpy.ndarray`.
    :param twiss_file: string path to twiss file with BPMs twiss.
    :return: tuple of two `numpy.ndarray` 2D matrices.
    """
    bpms_df = tfs.read(twiss_file)
    bpms_df["CATX"] = bpms_df["BETX"].apply(lambda x: "low" if x <= 40 else ("medium" if 40 < x <= 200 else "high"))
    bpms_df["CATY"] = bpms_df["BETY"].apply(lambda x: "low" if x <= 40 else ("medium" if 40 < x <= 200 else "high"))
    combinations_matrix_x = np.array(
        [[bpm_1_beta_cat + "-" + bpm_2_beta_cat for bpm_1_beta_cat in bpms_df.CATX] for bpm_2_beta_cat in bpms_df.CATX]
    )
    combinations_matrix_y = np.array(
        [[bpm_1_beta_cat + "-" + bpm_2_beta_cat for bpm_1_beta_cat in bpms_df.CATY] for bpm_2_beta_cat in bpms_df.CATY]
    )
    combinations_matrix_x = _remove_duplicate_combinations(combinations_matrix_x)
    combinations_matrix_y = _remove_duplicate_combinations(combinations_matrix_y)
    return combinations_matrix_x, combinations_matrix_y


def create_meas_matrix_from_values_array(values_array: np.ndarray) -> np.ndarray:
    """
    For testing purposes. Returns the deltas measurements matrix from an array of values.
    :param values_array: the values of phases at your N BPMs, in a (1, N) shaped `numpy.ndarray`.
    :return: the matrix, as a `numpy.ndarray`.
    """
    return np.array([[i - j for i in values_array] for j in values_array], dtype=float)


def create_random_phase_values(low: float, high: float, n_values: int, dist: str) -> np.ndarray:
    """
    Returns fake generated phase values. They are ascending by default.
    :param low: lowest value, first value will always be 0.
    :param high: highest value.
    :param n_values: number of values to generate.
    :param dist: distribution type required. Will be uniform or linspace.
    :return: a `numpy.ndarray` of shape (n_values,) with the generated values.
    """
    if dist == "linspace":
        values = np.linspace(low, high, n_values)
    elif dist == "uniform":
        values = np.sort(np.random.default_rng().uniform(low, high, n_values))
    else:
        raise ValueError("Provided parameter 'distribution' should be either 'linspace' or 'uniform'.")
    values[0] = 0
    return values


def create_2d_gaussian_noise(mean: float, stdev: float, shape: tuple) -> np.ndarray:
    """
    Generates a 2D Gaussian distribution, makes it antisymmetric and returns it.
    :param mean: mean of the distribution, should be 0 for us (since we add to the ideal M_meas).
    :param stdev: standard deviation of the distribution, should be in degrees if M_meas is given
    in degrees, in radians otherwise.
    :param shape: the shape of the matrix to create, should be M_meas.shape, aka (n_bpms, n_bpms).
    :return: a Gaussian, anti-symmetric, 2D-shaped `numpy.ndarray`.
    """
    gaussian_2d_mat = np.random.default_rng().normal(mean, stdev, size=shape)
    upper_triangle = np.triu(gaussian_2d_mat)
    return upper_triangle - upper_triangle.T


def get_combinations_matrices_from_madx(madx_file: str) -> (np.ndarray, np.ndarray):
    """Call the madx file, analyse twiss and give back combinations."""
    cmd = CommandLine()
    cmd.run(f"madx {madx_file}")
    comb_mat_x, comb_mat_y = create_combinations_matrices_from_twiss("bpms.tfs")
    cmd.run("rm -f bpms.tfs")
    return comb_mat_x, comb_mat_y


def meas_noise_matrix_to_dataframe(matrix: np.ndarray) -> pd.DataFrame:
    """Return a DataFrame version of the provided matrix."""
    headers = [f"BPM{i + 1}" for i in range(matrix.shape[0])]
    df_form = pd.DataFrame(matrix, columns=headers)
    df_form.index = headers
    return df_form


def plot_noised_vs_true_signal(signal: np.ndarray, noised: np.ndarray, figsize: tuple, savefig: bool = None) -> None:
    """
    Plots reconstructed vs original.
    :param signal: true original signal.
    :param noised: original signal with noise applied.
    :param figsize: size of figure.
    :param savefig: boolean, option to save the figure as pdf at 300 dpi.
    :return: none, plots the figure.
    """
    plt.figure(figsize=figsize)
    plt.title("True vs Noised Signal")
    plt.plot(signal, label="True signal", marker=",", ls="--")
    plt.ylabel("Phase Value [deg]")
    plt.plot(noised, c="violet", alpha=1, ls=":", label="Noised Signal")
    plt.xlabel("BPM Number")
    plt.legend(loc="best")
    if savefig:
        plt.savefig("plots/noised_vs_true.pdf", dpi=300)


def plot_reconstructed_vs_true_signal(
    signal: np.ndarray, reconstructed: np.ndarray, figsize: tuple, savefig: bool = None
) -> None:
    """
    Plots reconstructed vs original.
    :param signal: true original signal.
    :param reconstructed: reconstructed signal.
    :param figsize: size of figure.
    :param savefig: boolean, option to save the figure as pdf at 300 dpi.
    :return: none, plots the figure.
    """
    plt.figure(figsize=figsize)
    plt.title("True vs Reconstructed Signal")
    plt.plot(signal, label="True signal", marker=",", ls="--")
    plt.plot(reconstructed, label="Reconstructed signal", marker=",", ls="--")
    plt.ylabel("Phase Value [deg]")
    plt.xlabel("BPM Number")
    plt.legend(loc="best")
    if savefig:
        plt.savefig("plots/evm_reconstruct_vs_true.pdf", dpi=300)


def plot_absolute_difference_to_true_signal(
    signal: np.ndarray, reconstructed: np.ndarray, noise_stdev: float, figsize: tuple, savefig: bool = None
) -> None:
    """
    Plots the value difference of reconstructed signal to original.
    :param signal: true original signal.
    :param reconstructed: reconstructed signal.
    :param noise_stdev: stdev of the added noise distribution.
    :param figsize: size of figure.
    :param savefig: boolean, option to save the figure as pdf at 300 dpi.
    :return: none, plots the figure.
    """
    plt.figure(figsize=figsize)
    plt.title("Absolute Difference to Original Signal")
    plt.plot(
        np.abs(signal - reconstructed),
        color="cornflowerblue",
        label="Abs. diff. of rec. to original signal",
        marker=",",
        ls=":",
    )
    plt.hlines(
        noise_stdev * 0.1,
        xmin=0,
        xmax=len(reconstructed),
        color="seagreen",
        label="10% of noise distribution stdev",
        ls="--",
    )
    plt.hlines(
        np.mean(np.abs(signal - reconstructed)),
        xmin=0,
        xmax=len(reconstructed),
        color="darkred",
        label=f"Mean of abs. diff. ({100 * np.mean(np.abs(signal - reconstructed)) / noise_stdev:.2f}% of noise stdev)",
        ls="--",
    )
    plt.ylabel("Absolute Difference [deg]")
    plt.xlabel("BPM Number")
    plt.legend(loc="best")
    if savefig:
        plt.savefig("plots/reconstruct_to_signal_diff.pdf", dpi=300)


def _remove_duplicate_combinations(combinations_matrix: np.ndarray) -> np.ndarray:
    """
    Will simply transform 'low-high' in 'high-low' etc so that one case is only one specific string.
    :param combinations_matrix: your combinations matrix.
    :return: same, but refactored.
    """
    combinations_matrix[combinations_matrix == "low-high"] = "high-low"
    combinations_matrix[combinations_matrix == "medium-high"] = "high-medium"
    combinations_matrix[combinations_matrix == "low-medium"] = "medium-low"
    return combinations_matrix


def sigmas_square(num: int, meas_used: int) -> np.ndarray:
    """
    Generate a chi-square distribution of 'num' elements, each computed from a normal distribution of 'meas_used'
    elements.
    :param num: Number of elements for the generated distribution.
    :param meas_used: Number of values for each
    :return: the result as a `numpy.ndarray`.
    """
    res = []
    for _ in range(num):
        norm_dist = np.random.default_rng().normal(loc=0, scale=1, size=meas_used)
        res.append(np.sum(np.square([i - np.mean(norm_dist) for i in norm_dist])))
    return np.array(res)


def get_andreas_data() -> pd.DataFrame:
    """
    Load the errors distribution data from Andreas as a pandas Dataframe.
    :return: the file data as a `pandas.DataFrame` object.
    """
    with pathlib.Path("phase_data.txt").open() as phases:
        data = phases.read().strip().strip("\n").replace("\n", "").split(" ")

    data = [value for value in data if value != ""]
    for i in range(4, len(data)):
        data[i] = np.float(data[i])

    headers = np.array(data[:4])
    andreas_data = np.array(data[4:]).reshape((285156, 4))
    errors_df = pd.DataFrame(data=andreas_data, columns=headers)

    # Units are in radians and in units of 2pi
    errors_df["phase"] = errors_df.phase.apply(lambda x: x * 2 * np.pi)
    errors_df["phase_err"] = errors_df.phase_err.apply(lambda x: x * 2 * np.pi)

    # Creating Combinations
    errors_df["CAT1"] = errors_df.beta1.apply(lambda x: "low" if x <= 40 else ("medium" if 40 < x <= 200 else "high"))
    errors_df["CAT2"] = errors_df.beta2.apply(lambda x: "low" if x <= 40 else ("medium" if 40 < x <= 200 else "high"))
    errors_df["Combination"] = errors_df.CAT1 + "-" + errors_df.CAT2
    return errors_df.copy()


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
