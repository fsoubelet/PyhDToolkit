"""
.. _lhc-twiss:

**Twiss Utilities**

The functions below are twiss utilities for the ``LHC`` insertion regions.
"""
from typing import Sequence

import tfs

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools import twiss
from pyhdtoolkit.cpymadtools.constants import DEFAULT_TWISS_COLUMNS


def get_ips_twiss(madx: Madx, columns: Sequence[str] = DEFAULT_TWISS_COLUMNS, **kwargs) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.9.0

    Quickly get the ``TWISS`` table for certain variables at IP locations only. The ``SUMM`` table will be
    included as the `~tfs.frame.TfsDataFrame`'s header dictionary.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        columns (Sequence[str]): the variables to be returned, as columns in the DataFrame.
        **kwargs: Any keyword argument that can be given to the ``MAD-X`` ``TWISS`` command, such as ``chrom``,
            ``ripken``, ``centre``; or starting coordinates with ``betx``, ``bety`` etc.

    Returns:
        A `~tfs.frame.TfsDataFrame` of the ``TWISS`` table's sub-selection.

    Example:
        .. code-block:: python

            >>> ips_df = get_ips_twiss(madx, chrom=True, ripken=True)
    """
    logger.debug("Getting Twiss at IPs")
    return twiss.get_pattern_twiss(madx=madx, columns=columns, patterns=["IP"], **kwargs)


def get_ir_twiss(madx: Madx, ir: int, columns: Sequence[str] = DEFAULT_TWISS_COLUMNS, **kwargs) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.9.0

    Quickly get the ``TWISS`` table for certain variables for one Interaction Region, meaning at the IP and
    Q1 to Q3 both left and right of the IP. The ``SUMM`` table will be included as the `~tfs.frame.TfsDataFrame`'s
    header dictionary.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ir (int): which interaction region to get the TWISS for.
        columns (Sequence[str]): the variables to be returned, as columns in the DataFrame.
        **kwargs: Any keyword argument that can be given to the ``MAD-X`` ``TWISS`` command, such as ``chrom``,
            ``ripken``, ``centre``; or starting coordinates with ``betx``, ``bety`` etc.

    Returns:
        A `~tfs.frame.TfsDataFrame` of the ``TWISS`` table's sub-selection.

    Example:
        .. code-block:: python

            >>> ir_df = get_ir_twiss(madx, chrom=True, ripken=True)
    """
    logger.debug(f"Getting Twiss for IR{ir:d}")
    return twiss.get_pattern_twiss(
        madx=madx,
        columns=columns,
        patterns=[
            f"IP{ir:d}",
            f"MQXA.[12345][RL]{ir:d}",  # Q1 and Q3 LHC
            f"MQXB.[AB][12345][RL]{ir:d}",  # Q2A and Q2B LHC
            f"MQXF[AB].[AB][12345][RL]{ir:d}",  # Q1 to Q3 A and B HL-LHC
        ],
        **kwargs,
    )
