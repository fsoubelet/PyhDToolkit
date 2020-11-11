"""
Module maths.nonconvex_phase_sync
---------------------------------

Created on 2020.01.13
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 implementation of the Nonconvex Phase Synchronisation method found in the
following paper (DOI: 10.1137/16M105808X, the algorithm reproduced is page 8).


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
we can reconstruct a good estimator of the original values through the EVM method, provided in the
class below.
"""

import numpy as np

from loguru import logger


class PhaseReconstructor:
    """
    Class algorithm to reconstruct your phase values.
    Make sure to provide vectors as `numpy.ndarray` with shape (1, N), N being the dimension.
    """

    __slots__ = {
        "c_matrix": "Hermitian square matrix from your measurements",
        "c_matrix_eigenvalues": "Eigenvalues of c_matrix",
        "c_matrix_eigenvectors": "Eigenvectors of c_matrix",
        "space_dimension": "Dimension of your measurement space",
    }

    def __init__(self, measurements_hermitian_matrix: np.ndarray) -> None:
        """
        Initialize your reconstructor object from measurements.

        Args:
            measurements_hermitian_matrix: a `numpy.ndarray` object built from measurements, see
                module docstring on how to build this matrix.
        """
        logger.debug("Checking that the provided matrix is Hermitian")
        if np.allclose(measurements_hermitian_matrix, np.conj(measurements_hermitian_matrix).T):
            self.c_matrix: np.ndarray = measurements_hermitian_matrix
            self.c_matrix_eigenvalues: np.ndarray = np.linalg.eigvalsh(self.c_matrix)
            # Numpy gives the eigenvectors in column form, so transpose is needed there!
            self.c_matrix_eigenvectors: np.ndarray = np.linalg.eigh(self.c_matrix)[-1].T
            self.space_dimension: int = self.c_matrix.shape[0]
        else:
            logger.exception(
                "Instantiating a PhaseReconstructor with a non hermitian matrix is " "not possible"
            )
            raise ValueError("Provided matrix should be Hermitian")

    @property
    def alpha(self) -> np.float64:
        """
        This is a factor used to define the new reconstruction matrix. It is taken either as the
        operator norm of the hermitian noise matrix, or as the max value between 0 and the opposite
        of the min eigenvalue of c_matrix (chosen for implementation, since our noise is included
        in the measurements). See page 8 of the paper for reference.

        Returns:
           A real scalar value, because c_matrix is Hermitian and the eigenvalues of real symmetric
           or complex Hermitian matrices are always real (see G. Strang, Linear Algebra and Its
           Applications, 2nd Ed., Orlando, FL, Academic Press, Inc., 1980, pg. 222.)
        """
        return np.float64(max(0, np.amin(self.c_matrix_eigenvalues)))

    @property
    def leading_eigenvector(self) -> np.ndarray:
        """
        Returns the leading eigenvector of `self.c_matrix`, which is the eigenvector corresponding
        to the max eigenvalue (in absolute value).

        Returns:
            A `numpy.ndarray` object, corresponding to said eigenvector.
        """
        return self.c_matrix_eigenvectors[
            np.where(self.c_matrix_eigenvalues == np.amax(np.absolute(self.c_matrix_eigenvalues)))
        ].reshape((1, self.space_dimension))

    @property
    def reconstructor_matrix(self) -> np.ndarray:
        """
        This is the reconstructor matrix built from `self.c_matrix` and the `alpha` property.
        It is the matrix denoted as \\widetilde{C} on page 8 of the reference paper.

        Returns:
            A `numpy.ndarray`, with same dimension as `self.c_matrix`.
        """
        return self.c_matrix + self.alpha * np.identity(self.c_matrix.shape[0])

    def get_eigenvector_estimator(self, eigenvector: np.ndarray) -> np.ndarray:
        """
        Return the eigenvector estimator of a given eigenvector (id est the component-wise
        projection of said eigenvector onto ℂˆ{n}_{1}, see reference paper at page 7 for
        implementation.

        Args:
            eigenvector (np.ndarray): a numpy array representing the vector.

        Returns:
             A `numpy.ndarray` object of the same dimension as param `eigenvector`.
        """
        try:
            return eigenvector / np.absolute(eigenvector)
        except RuntimeWarning:  # In case of 0-division, we don't want `inf` values from numpy
            # Generate a random complex vector with same dimension (since `eigenvector` is of
            # dimension N * 1, `numpy.ndarray.size` method will give us N).
            # Remember to initialize a random real and imaginary part.
            logger.exception("Encountered 0-division, trying normalization")
            e_vect = np.random.randn(eigenvector.size) + 1j * np.random.randn(eigenvector.size)
            while (
                np.absolute(e_vect @ eigenvector) == 0
            ):  # Guarantee that we don't fall back to this edge case.
                e_vect = np.random.randn(eigenvector.size) + 1j * np.random.randn(eigenvector.size)
            return (e_vect @ eigenvector / np.absolute(e_vect @ eigenvector)).reshape(
                (1, self.space_dimension)
            )

    def reconstruct_complex_phases_evm(self) -> np.ndarray:
        """
        Reconstruct simplest estimator fom the eigenvector method. The result is in complex form,
        and will be radians once cast back to real form.

        Returns:
            The complex form of the result as a 'numpy.ndarray' instance.
        """
        logger.debug("Getting complex phase results")
        return self.get_eigenvector_estimator(self.leading_eigenvector)

    @staticmethod
    def convert_complex_result_to_phase_values(
        complex_estimator: np.ndarray, deg: bool = False
    ) -> np.ndarray:
        """
        Casts back the complex form of your result to real phase values.

        Args:
            complex_estimator (np.ndarray): your result's complex form as a numpy array.
            deg (bool): if this is set to True, the result is cast to degrees (from radians)
            before being returned. Defaults to False.

        Returns:
            A `numpy.ndarray` with the real phase values of the result.
        """
        logger.debug("Casting complex phases to real values")
        return np.apply_along_axis(np.angle, axis=0, arr=complex_estimator, deg=deg)
