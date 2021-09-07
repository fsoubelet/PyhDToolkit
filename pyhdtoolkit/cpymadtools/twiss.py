"""
Module cpymadtools.twiss
------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to manipulate MAD-X TWISS functionality through a cpymad.madx.Madx object.
"""
from typing import Sequence

import numpy as np
import tfs

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.constants import DEFAULT_TWISS_COLUMNS

# ----- Utlites ----- #


def get_pattern_twiss(
    madx: Madx, patterns: Sequence[str] = [""], columns: Sequence[str] = None, **kwargs,
) -> tfs.TfsDataFrame:
    """
    Extract the `TWISS` table for desired variables, and for certain elements matching a pattern.
    Additionally, the `SUMM` table is also returned in the form of the TfsDataFrame's headers dictionary.
    The TWISS flag will be fully cleared after running this command.

    Warning:
        Although the `pattern` parameter should accept a regex, MAD-X does not implement actual regexes.
        Please refer to the MAD-X manual, section `Regular Expressions` for details on what is implemented
        in MAD-X itself.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        patterns (Sequence[str]): the different element patterns (such as `MQX` or `BPM`) to be applied to
            the command, which will determine the rows in the returned DataFrame. Defaults to [""] which
            will select all elements.
        columns (Sequence[str]): the variables to be returned, as columns in the DataFrame. Defaults to
            `None`, which will return all available columns.

    Keyword Args:
        Any keyword argument that can be given to the MAD-X TWISS command, such as `chrom`, `ripken`,
        `centre` or starting coordinates with `betax`, 'betay` etc.

    Returns:
        A TfsDataFrame with the selected columns for all elements matching the provided patterns,
        and the internal `summ` table as header dict.
    """
    logger.trace("Clearing 'TWISS' flag")
    madx.select(flag="twiss", clear=True)

    for pattern in patterns:
        logger.trace(f"Adding pattern {pattern} to 'TWISS' flag")
        madx.select(flag="twiss", pattern=pattern, column=columns)
    madx.twiss(**kwargs)

    logger.trace("Extracting relevant parts of the TWISS table")
    twiss_df = tfs.TfsDataFrame(madx.table.twiss.dframe().copy())
    twiss_df.headers = {var.upper(): madx.table.summ[var][0] for var in madx.table.summ}
    twiss_df = twiss_df[madx.table.twiss.selected_columns()].iloc[madx.table.twiss.selected_rows()]

    logger.trace("Clearing 'TWISS' flag")
    madx.select(flag="twiss", clear=True)
    return twiss_df


def get_twiss_tfs(madx: Madx) -> tfs.TfsDataFrame:
    """
    Returns a tfs.TfsDataFrame from the Madx instance's twiss dframe, typically in the way we're used to
    getting it from MAD-X outputting the TWISS (uppercase names, colnames, summ table in headers).

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.

    Returns:
        A tfs.TfsDataFrame.
    """
    logger.info("Exporting internal TWISS and SUMM tables to TfsDataFrame")
    twiss_tfs = tfs.TfsDataFrame(madx.table.twiss.dframe())
    twiss_tfs.name = [element[:-2] for element in twiss_tfs.name]
    twiss_tfs.columns = twiss_tfs.columns.str.upper()
    twiss_tfs = twiss_tfs.set_index("NAME")
    twiss_tfs.index = twiss_tfs.index.str.upper()
    twiss_tfs.headers = {var.upper(): madx.table.summ[var][0] for var in madx.table.summ}
    return twiss_tfs


def get_ips_twiss(madx: Madx, columns: Sequence[str] = DEFAULT_TWISS_COLUMNS, **kwargs) -> tfs.TfsDataFrame:
    """
    Quickly get the `TWISS` table for certain variables at IP locations only. The `SUMM` table will be
    included as the TfsDataFrame's header dictionary.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        columns (Sequence[str]): the variables to be returned, as columns in the DataFrame.

    Keyword Args:
        Any keyword argument that can be given to the MAD-X TWISS command, such as `chrom`, `ripken`,
        `centre` or starting coordinates with `betax`, 'betay` etc.

    Returns:
        A TfsDataFrame of the twiss output.
    """
    logger.info("Getting Twiss at IPs")
    return get_pattern_twiss(madx=madx, patterns=["IP"], columns=columns, **kwargs)


def get_ir_twiss(
    madx: Madx, ir: int, columns: Sequence[str] = DEFAULT_TWISS_COLUMNS, **kwargs
) -> tfs.TfsDataFrame:
    """
    Quickly get the `TWISS` table for certain variables for one IR, meaning at the IP and Q1 to Q3 both
    left and right of the IP. The `SUMM` table will be included as the TfsDataFrame's header dictionary.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        ir (int): which interaction region to get the TWISS for.
        columns (Sequence[str]): the variables to be returned, as columns in the DataFrame.

    Keyword Args:
        Any keyword argument that can be given to the MAD-X TWISS command, such as `chrom`, `ripken`,
        `centre` or starting coordinates with `betax`, 'betay` etc.

    Returns:
        A TfsDataFrame of the twiss output.
    """
    logger.info(f"Getting Twiss for IR{ir:d}")
    return get_pattern_twiss(
        madx=madx,
        patterns=[
            f"IP{ir:d}",
            f"MQXA.[12345][RL]{ir:d}",  # Q1 and Q3 LHC
            f"MQXB.[AB][12345][RL]{ir:d}",  # Q2A and Q2B LHC
            f"MQXF[AB].[AB][12345][RL]{ir:d}",  # Q1 to Q3 A and B HL-LHC
        ],
        columns=columns,
        **kwargs,
    )
