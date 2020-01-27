# Nonconvex phase synchronisation

Details of use case will be found in the high-level docstring of the `nonconvex_phase_sync.py` file.
This is an implementation of the solution described in Nicolas Boumal's 2016 paper ([reference](https://arxiv.org/abs/1601.06114)).

Let's consider a simple line with 5 BPMs, at the different (randomly generated for this example) phase values:
```
BPM 1: phase is 14.5 degrees
BPM 2: phase is 25.0 degrees
BPM 3: phase is 31.2 degrees
BPM 4: phase is 47.6 degrees
BPM 5: phase is 55.3 degrees
```

At measurement, we don't know those exact values, we can only access (noisy) phase differences.
In our case, due to different beta functions at different BPMs, some signals are very good quality (e.g between two BPMs at high beta) and some are very poor quality (e.g. between two BPMs at low beta, or two BPMs with bad phase advance combination).

As a consequence some elements (or even entire rows or columns) in our measurement matrix will be of poor quality. The paper cited above provides a method to reconstruct, as noise-free as possible, the absolute phase values at measurement points.

Let's walk through the resolution, firstly the setup:

```python
import numpy as np
from pyhdtoolkit.omc_math.nonconvex_phase_sync import PhaseReconstructor

# We create our measurements matrix, here with values in degrees, which we will convert
# to radians right up next (see module docstring on how to create this matrix)
M_matrix = np.array(
    [
        [0, 10.5, 16.7, 33.1, 40.8],
        [-10.5, 0, 6.2, 22.6, 30.3],
        [-16.7, -6.2, 0, 16.4, 24.1],
        [-33.1, -22.6, -16.4, 0, 7.7],
        [-40.8, -30.3, -24.1, -7.7, 0],
    ]
)

# Let's now create our corresponding Hermitian matrix (without forgetting to cast M_matrix to 
# radians), and initiate a `PhaseReconstructor` object from this matrix
C_matrix = np.exp(1j * np.deg2rad(M_matrix))
PR = PhaseReconstructor(C_matrix)
```

## Eigenvector Method

The eigenvector method provides a best compromise estimator, attainable with little computation, of the simplest deltas array with reduced noise.

Here, this would be: [delta_phase1->1, delta_phase1->2, delta_phase1->3, delta_phase1->4].


This estimator is the eigenvector estimator of the leading eigenvector, a.k.a the element-wise projection onto C^{n} of the leading eigenvector: the eigenvector corresponding to the highest (in absolute value) eigenvalue.

With the `PhaseReconstructor` instance initialized above, it is achieved as seen bellow:
```python
# Going through trough the eigenvector method, casting back results to degrees goes as:

complex_ev_method_result = PR.get_eigenvector_estimator(PR.leading_eigenvector)
PR.convert_complex_result_to_phase_values(complex_ev_method_result, deg=True)
# [out]:  array([[  0. , -10.5, -16.7, -33.1, -40.8]])

# Here, this is a perfect result, since we have no noise introduced to our measurement
```

## Generalized Power Method

The cited paper introduces the generalized power method, an iterative computing method to reconstruct the absolute phase values at measurement points, as noise-free as possible.

The implementation details can be found in the paper, and in the `nonconvex_phase_sync` module's docstrings.
The iteration stops when a convergence criteria is reached, the margin for which has to be provided.
The paper suggests a numerical value of `1e-7`, which we will use in this example

With the `PhaseReconstructor` instance initialized above, this goes as:
```python
margin = np.float64(1e-7)
complex_phases = PR.reconstruct_complex_phases_gpm(convergence_margin=margin)
real_phases = PR.convert_complex_result_to_phase_values(complex_phases, deg=True)
# [out]: 
```