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
    madx: Madx, patterns: Sequence[str], columns: Sequence[str] = DEFAULT_TWISS_COLUMNS, **kwargs
) -> tfs.TfsDataFrame:
    """
    Extract the `TWISS` table for desired variables, and for certain elements matching a pattern.
    Additionally, the `SUMM` table is also returned in the form of the TfsDataFrame's headers dictionary.

    Warning:
        Although the `pattern` parameter should accept a regex, MAD-X does not implement actual regexes.
        Please refer to the MAD-X manual, section `Regular Expressions` for details on what is implemented
        in MAD-X itself.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        patterns (Sequence[str]): the different element patterns (such as `MQX` or `BPM`) to be applied to
            the command, which will determine the rows in the returned DataFrame.
        columns (Sequence[str]): the variables to be returned, as columns in the DataFrame.

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
    twiss_df.headers = {var: madx.table.summ[var][0] for var in madx.table.summ}
    twiss_df = twiss_df[madx.table.twiss.selected_columns()].iloc[
        np.array(madx.table.twiss.selected_rows()).astype(bool)
    ]

    logger.trace("Clearing 'TWISS' flag")
    madx.select(flag="twiss", clear=True)
    return twiss_df
