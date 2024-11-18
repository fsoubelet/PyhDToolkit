"""
.. _cpymadtools-twiss:

TWISS Routines
--------------

Module with functions to manipulate ``MAD-X`` ``TWISS`` functionality
through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tfs

from loguru import logger

from pyhdtoolkit.cpymadtools.constants import DEFAULT_TWISS_COLUMNS

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cpymad.madx import Madx


# ----- Utlites ----- #


def get_pattern_twiss(
    madx: Madx,
    /,
    columns: Sequence[str] | None = None,
    patterns: Sequence[str] = (),
    **kwargs,
) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.8.0

    Extracts the ``TWISS`` table for desired variables from the provided
    `~cpymad.madx.Madx` object, for elements matching the provided *patterns*.
    The table is returned as a `~tfs.frame.TfsDataFrame`, the headers of which
    are the contents of the internal ``SUMM`` table.

    Note
    ----
        The ``TWISS`` flag will be fully cleared after running this function.

    Warning
    -------
        Although the *patterns* parameter should accept a regex, ``MAD-X`` does
        not implement actual regexes. Please refer to the `MAD-X manual
        <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_, section
        `Regular Expressions` for details on what is implemented in ``MAD-X`` itself.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    columns : Sequence[str], optional
        The variables to be returned, as columns in the `~tfs.frame.TfsDataFrame`.
        Defaults to `None`, which will return all available columns.
    patterns : Sequence[str]
        The different element patterns (such as ``MQX`` or ``BPM``) to be applied
        to the ``TWISS`` command, which will determine the rows in the returned
        `~tfs.frame.TfsDataFrame`. Defaults to an empty sequence, which will select
        all elements.
    **kwargs
        Any keyword argument that can be given to the ``MAD-X`` ``TWISS`` command,
        such as `chrom`, `ripken`, `centre`; or starting values for `betx`, `bety`
        etc.

    Returns
    -------
    tfs.TfsDataFrame
        A `~tfs.frame.TfsDataFrame` with the selected columns for all elements matching
        the provided patterns, and the internal ``SUMM`` table as headers.

    Examples
    --------
        To get LHC IP points:

        .. code-block:: python

            ips_df = get_pattern_twiss(madx=madx, patterns=["IP"])

        To get (HL)LHC IR1 triplets:

        .. code-block:: python

            triplets_df = get_pattern_twiss(
                madx=madx,
                patterns=[
                    r"MQXA.[12345][RL]1",  # Q1 and Q3 LHC
                    r"MQXB.[AB][12345][RL]1",  # Q2A and Q2B LHC
                    r"MQXF[AB].[AB][12345][RL]1",  # Q1 to Q3 A and B HL-LHC
                ],
            )
    """
    columns = columns or DEFAULT_TWISS_COLUMNS
    logger.trace("Clearing 'TWISS' flag")
    madx.select(flag="twiss", clear=True)

    for pattern in patterns:
        logger.trace(f"Adding pattern {pattern} to 'TWISS' flag")
        madx.select(flag="twiss", pattern=pattern, column=columns)

    # DO NOT change to madx.command.twiss(**kwargs): it doesn't properly set the selected_columns and selected_rows
    madx.twiss(**kwargs)

    logger.trace("Extracting relevant parts of the TWISS table")
    twiss_df = tfs.TfsDataFrame(madx.table.twiss.dframe())
    twiss_df.headers = {var.upper(): madx.table.summ[var][0] for var in madx.table.summ}
    twiss_df = twiss_df[madx.table.twiss.selected_columns()].iloc[madx.table.twiss.selected_rows()]

    logger.trace("Clearing 'TWISS' flag")
    madx.select(flag="twiss", clear=True)
    return twiss_df


def get_twiss_tfs(madx: Madx, /, **kwargs) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.8.3

    Returns a `~tfs.frame.TfsDataFrame` from the `~cpymad.madx.Madx` instance's
    ``TWISS`` table, typically in the way we're used to getting it from ``MAD-X``
    outputting the `TWISS` (uppercase names, colnames, ``SUMM`` table in headers).
    This will call the `TWISS` command first before returning the dframe to you.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    **kwargs
        Any keyword argument that can be given to the ``MAD-X`` ``TWISS`` command,
        such as `chrom`, `ripken`, `centre`; or starting values for `betx`, `bety`
        etc.

    Returns
    -------
    tfs.TfsDataFrame
        A `~tfs.frame.TfsDataFrame` of the ``TWISS`` table, with the internal
        ``SUMM`` table as headers.

    Example
    -------
        .. code-block:: python

            twiss_df = get_twiss_tfs(madx, chrom=True, ripken=True)
    """
    logger.trace("Clearing 'TWISS' flag")
    madx.select(flag="twiss", clear=True)
    madx.command.twiss(**kwargs)

    logger.debug("Exporting internal TWISS and SUMM tables to TfsDataFrame")
    twiss_tfs = tfs.TfsDataFrame(madx.table.twiss.dframe())
    twiss_tfs.name = twiss_tfs.name.apply(lambda x: x[:-2])  # remove :1 from names
    twiss_tfs.columns = twiss_tfs.columns.str.upper()
    twiss_tfs = twiss_tfs.set_index("NAME")
    twiss_tfs.index = twiss_tfs.index.str.upper()
    twiss_tfs.headers = {var.upper(): madx.table.summ[var][0] for var in madx.table.summ}
    return twiss_tfs
