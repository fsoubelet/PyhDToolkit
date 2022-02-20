"""
.. _cpymadtools-utils:

Miscellaneous Utilities
-----------------------

Module with utility functions to do mundane operations with `~cpymad.madx.Madx` objects.
"""
import tfs

from cpymad.madx import Madx
from loguru import logger


def get_table_tfs(madx: Madx, table_name: str, headers_table: str = "SUMM") -> tfs.TfsDataFrame:
    """
    Turns an internal table from the ``MAD-X`` process into a `~tfs.frame.TfsDataFrame`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        table_name (str): the name of the internal table to retrieve.
        headers_table (str): the name of the internal table to use for headers.
            Defaults to ``SUMM``.

    Returns:
        A `~tfs.frame.TfsDataFrame` object with the *table_name* data, and the desired
        *headers_table* (usually ``SUMM``) as headers.

    Examples:
        .. code-block:: python

            >>> twiss_tfs = get_table_tfs(madx, table_name="TWISS")
    """
    logger.debug(f"Extracting table {table_name} into a TfsDataFrame")
    dframe = tfs.TfsDataFrame(madx.table[table_name].dframe())
    dframe.columns = dframe.columns.str.upper()

    if "NAME" in dframe.columns:
        logger.trace("Uppercasing 'NAME' column contents")
        dframe.NAME = dframe.NAME.str.upper()

    logger.trace(f"Turning {headers_table} table into headers")
    dframe.headers = {var.upper(): madx.table[headers_table][var][0] for var in madx.table[headers_table]}
    return dframe
