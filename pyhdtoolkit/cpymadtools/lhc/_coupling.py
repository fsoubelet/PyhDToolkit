"""
.. _lhc-coupling:

**Coupling Utilities**

The functions below are betatron coupling utilities for the ``LHC``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from optics_functions.coupling import coupling_via_cmatrix

from pyhdtoolkit.cpymadtools.constants import MONITOR_TWISS_COLUMNS
from pyhdtoolkit.cpymadtools.twiss import get_pattern_twiss

if TYPE_CHECKING:
    from cpymad.madx import Madx
    from tfs import TfsDataFrame


def get_lhc_bpms_twiss_and_rdts(madx: Madx, /) -> TfsDataFrame:
    """
    .. versionadded:: 0.19.0

    Runs a ``TWISS`` on the currently active sequence for all ``LHC`` BPMs.
    The coupling RDTs are also computed through a CMatrix approach via a call
    to `optics_functions.coupling.coupling_via_cmatrix`.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.

    Returns
    -------
    TfsDataFrame
        A `~tfs.frame.TfsDataFrame` of the ``TWISS`` table with basic
        default columns, as well as one new complex-valued column for
        each of the coupling RDTs.

    Example
    -------
        .. code-block:: python

            twiss_with_rdts = get_lhc_bpms_twiss_and_rdts(madx)
    """
    twiss_tfs = get_pattern_twiss(madx, patterns=["^BPM.*B[12]$"], columns=MONITOR_TWISS_COLUMNS)
    twiss_tfs.columns = twiss_tfs.columns.str.upper()  # optics_functions needs capitalized names
    twiss_tfs.NAME = twiss_tfs.NAME.str.upper()
    twiss_tfs[["F1001", "F1010"]] = coupling_via_cmatrix(twiss_tfs, output=["rdts"])
    return twiss_tfs
