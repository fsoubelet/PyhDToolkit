"""
Module cpymadtools.utils
------------------------

Created on 2021.07.22
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with utility functions to do mundane operatiions with `cpymad.madx.Madx` objects.
"""
import tfs

from cpymad.madx import Madx
from loguru import logger


def get_table_tfs(madx: Madx, table_name: str) -> tfs.TfsDataFrame:
    """
    Turns an internal table from the `MAD-X` process into a `TfsDataFrame` object.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
        table_name (str): the name of the internal table.

    Returns:
        A `TfsDataFrame` object with the table data, and the `SUMM` table as headers.
    """
    logger.debug(f"Extracting table {table_name} into a TfsDataFrame")
    dframe = tfs.TfsDataFrame(madx.table[table_name].dframe())
    dframe.columns = dframe.columns.str.upper()

    if "NAME" in dframe.columns:
        logger.trace("Uppercasing 'NAME' column contents")
        dframe.NAME = dframe.NAME.str.upper()

    logger.trace("Turning SUMM table into headers")
    dframe.headers = {var.upper(): madx.table.summ[var][0] for var in madx.table.summ}
    return dframe
