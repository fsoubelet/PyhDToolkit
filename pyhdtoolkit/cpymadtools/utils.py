"""
.. _cpymadtools-utils:

Miscellaneous Utilities
-----------------------

Module with utility functions to do mundane operations
with `~cpymad.madx.Madx` objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import tfs

from loguru import logger

if TYPE_CHECKING:
    from cpymad.madx import Madx


def export_madx_table(
    madx: Madx,
    /,
    table_name: str,
    file_name: Path | str,
    pattern: str | None = None,
    headers_table: str = "SUMM",
    **kwargs,
) -> None:
    """
    .. versionadded:: 0.17.0

    Exports an internal table from the ``MAD-X`` process into a
    `~tfs.frame.TfsDataFrame` on disk.

    Important
    ---------
        Tables can only be correctly read back in ``MAD-X`` (through
        ``READTABLE``) if the written file has a ``NAME`` and a ``TYPE``
        entries in its headers.

        If these entries are not present (see below for their usage), then
        they will be given default values so the **TFS** file can be read
        back by ``MAD-X``.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    table_name : str
        The name of the internal table to retrieve.
    file_name : Path | str
        The name of the file to export to.
    pattern : str | None, optional
        If given, will be used as a regular expression to filter the
        extracted table, by passing it as the *regex* parameter of
        `pandas.DataFrame.filter`.
    headers_table : str
        The name of the internal table to use for headers. Defaults to
        using the ``SUMM`` table.
    **kwargs
        Any keyword arguments will be passed to `~tfs.writer.write_tfs`.

    Example
    -------
        .. code-block:: python

            madx.command.twiss()
            export_madx_table(madx, table_name="TWISS", file_name="twiss.tfs")
    """
    file_path = Path(file_name)
    logger.debug(f"Exporting table {table_name} into '{file_path.absolute()}'")
    dframe = get_table_tfs(madx, table_name, headers_table)
    if pattern:
        logger.debug(f"Setting NAME column as index and filtering extracted table with regex pattern '{pattern}'")
        dframe = dframe.set_index("NAME").filter(regex=pattern, axis="index").reset_index()
    if "NAME" not in dframe.headers:
        logger.debug("No 'NAME' header found, adding a default value 'EXPORT'")
        dframe.headers["NAME"] = "EXPORT"
    if "TYPE" not in dframe.headers:
        logger.debug("No 'TYPE' header found, adding a default value 'EXPORT'")
        dframe.headers["TYPE"] = "EXPORT"
    logger.debug("Writing to disk")
    tfs.write(file_path, dframe, **kwargs)


def get_table_tfs(madx: Madx, /, table_name: str, headers_table: str = "SUMM") -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.11.0

    Turns an internal table from the ``MAD-X`` process into a
    `~tfs.frame.TfsDataFrame`.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    table_name : str
        The name of the internal table to retrieve.
    headers_table : str
        The name of the internal table to use for headers. Defaults to
        using the ``SUMM`` table.

    Returns
    -------
    tfs.frame.TfsDataFrame
        A `~tfs.frame.TfsDataFrame` object with the *table_name* data,
        and the desired *headers_table* (usually ``SUMM``) as headers.

    Example
    -------
        .. code-block:: python

            twiss_tfs = get_table_tfs(madx, table_name="TWISS")
    """
    logger.debug(f"Extracting table {table_name} into a TfsDataFrame")
    # Converting to dict and then DataFrame because the madx.table.name.dframe()
    # method sometimes complains about element names and crashes (mostly seen)
    # when exporting error tables.
    dframe = pd.DataFrame.from_dict(dict(madx.table[table_name]))
    dframe = tfs.TfsDataFrame(dframe)
    dframe.columns = dframe.columns.str.upper()

    if "NAME" in dframe.columns:
        logger.trace("Uppercasing 'NAME' column contents")
        dframe.NAME = dframe.NAME.str.upper()

    logger.trace(f"Turning {headers_table} table into headers")
    dframe.headers = {var.upper(): madx.table[headers_table][var][0] for var in madx.table[headers_table]}
    return dframe


# ----- Helpers ----- #


def _get_k_strings(start: int = 0, stop: int = 8, orientation: str = "both") -> list[str]:
    """
    Returns the list of K-strings for various magnets and orders (``K1L``, ``K2SL`` etc strings).
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Args:
        start (int): the starting order, defaults to 0.
        stop (int): the order to go up to, defaults to 8.
        orientation (str): magnet orientation, can be `straight`, `skew` or `both`.
            Defaults to `both`.

    Returns:
        The `list` of names as strings.
    """
    if orientation not in ("straight", "skew", "both"):
        logger.error(f"Orientation '{orientation}' is not accepted, should be one of 'straight', 'skew', 'both'.")
        msg = "Invalid 'orientation' parameter"
        raise ValueError(msg)

    if orientation == "straight":
        orientation = ("",)
    elif orientation == "skew":
        orientation = ("S",)
    else:  # both
        orientation = ("", "S")

    return [f"K{i:d}{s:s}L" for i in range(start, stop) for s in orientation]
