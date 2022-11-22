"""
.. _lhc-coupling:

**Coupling Utilities**

The functions below are betatron coupling utilities for the ``LHC``.
"""
import tfs

from cpymad.madx import Madx
from loguru import logger
from optics_functions.coupling import coupling_via_cmatrix

from pyhdtoolkit.cpymadtools import twiss
from pyhdtoolkit.cpymadtools.constants import MONITOR_TWISS_COLUMNS


def correct_lhc_global_coupling(
    madx: Madx, beam: int = 1, telescopic_squeeze: bool = True, calls: int = 100, tolerance: float = 1.0e-21
) -> None:
    """
    .. versionadded:: 0.20.0

    A littly tricky matching routine to perform a decent global coupling correction using
    the ``LHC`` coupling knobs.

    .. important::
        This routine makes use of some matching tricks and uses the ``SUMM`` table's
        ``dqmin`` variable for the matching. It should be considered a helpful little
        trick, but it is not a perfect solution.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam (int): which beam you want to perform the matching for, should be `1` or
            `2`. Defaults to `1`.
        telescopic_squeeze (bool): If set to `True`, uses the coupling knobs
            for Telescopic Squeeze configuration. Defaults to `True`.
        calls (int): max number of varying calls to perform when matching. Defaults to 100.
        tolerance (float): tolerance for successfull matching. Defaults to :math:`10^{-21}`.

    Example:
        .. code-block:: python

            >>> correct_lhc_global_coupling(madx, sequence="lhcb1", telescopic_squeeze=True)
    """
    suffix = "_sq" if telescopic_squeeze else ""
    sequence = f"lhcb{beam:d}"
    logger.debug(f"Attempting to correct global coupling through matching, on sequence '{sequence}'")

    real_knob, imag_knob = f"CMRS.b{beam:d}{suffix}", f"CMIS.b{beam:d}{suffix}"
    logger.debug(f"Matching using the coupling knobs '{real_knob}' and '{imag_knob}'")
    madx.command.match(chrom=True, sequence=sequence)
    madx.command.gweight(dqmin=1, Q1=0)
    madx.command.global_(dqmin=0, Q1=62.28)
    madx.command.vary(name=real_knob, step=1.0e-8)
    madx.command.vary(name=imag_knob, step=1.0e-8)
    madx.command.lmdif(calls=calls, tolerance=tolerance)
    madx.command.endmatch()


def get_lhc_bpms_twiss_and_rdts(madx: Madx) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.19.0

    Runs a ``TWISS`` on the currently active sequence for all ``LHC`` BPMs. The coupling RDTs
    are also computed through a CMatrix approach via  `optics_functions.coupling.coupling_via_cmatrix`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A `~tfs.frame.TfsDataFrame` of the ``TWISS`` table with basic default columns, as well as one
        new column for each of the coupling RDTs. The coupling RDTs are returned as complex numbers.

    Example:
        .. code-block:: python

            >>> twiss_with_rdts = get_lhc_bpms_twiss_and_rdts(madx)
    """
    twiss_tfs = twiss.get_pattern_twiss(  # need chromatic flag as we're dealing with coupling
        madx, patterns=["^BPM.*B[12]$"], columns=MONITOR_TWISS_COLUMNS, chrom=True
    )
    twiss_tfs.columns = twiss_tfs.columns.str.upper()  # optics_functions needs capitalized names
    twiss_tfs.NAME = twiss_tfs.NAME.str.upper()
    twiss_tfs[["F1001", "F1010"]] = coupling_via_cmatrix(twiss_tfs, output=["rdts"])
    return twiss_tfs
