from pathlib import Path

import numpy as np

from pyhdtoolkit.optics import twiss

INPUT_PATHS = {
    "alpha_beta": Path(__file__).parent.parent / "inputs" / "alpha_beta.npy",
    "u_vector": Path(__file__).parent.parent / "inputs" / "u_vector.npy",
    "u_bar": Path(__file__).parent.parent / "inputs" / "u_bar.npy",
}


def test_courant_snyder_transform():
    # Test uses the dispatcher's 'py_func' object for coverage integrity, packaged implementation
    # is still JIT compiled.
    alpha_beta = np.load(INPUT_PATHS["alpha_beta"])
    u_vector = np.load(INPUT_PATHS["u_vector"])
    u_bar_result = np.load(INPUT_PATHS["u_bar"])
    u_transform = twiss.courant_snyder_transform.py_func(u_vector, alpha_beta[0], alpha_beta[1])
    np.testing.assert_array_almost_equal(u_transform, u_bar_result)
