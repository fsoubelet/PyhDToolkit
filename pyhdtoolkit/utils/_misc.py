"""
.. _utils-misc:

Miscellanous Personnal Utilities
--------------------------------

Private module that provides miscellaneous
personnal utility functions.

Warning
-------
    The functions in here are intented for personal
    use, and will most likely **not** work on other
    people's machines.
"""

from __future__ import annotations

import shlex

from multiprocessing import cpu_count
from pathlib import Path
from typing import TYPE_CHECKING

import cpymad
import numpy as np
import pandas as pd

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit import __version__
from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.cpymadtools.constants import LHC_IR_BPM_REGEX

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

# ----- Constants ----- #

N_CPUS: int = cpu_count()
RNG: Callable = np.random.default_rng()


def log_runtime_versions() -> None:
    """
    .. versionadded:: 0.17.0

    Issues a ``CRITICAL``-level log stating the runtime versions
    of both `~pyhdtoolkit`, `cpymad` and ``MAD-X``.

    Example
    -------
        .. code-block:: python

            log_runtime_versions()
            # 2022-10-05 15:06:26 | CRITICAL | pyhdtoolkit.utils._misc:39 - Using: pyhdtoolkit 1.0.0rc0 | cpymad 1.10.0  | MAD-X 5.08.01 (2022.02.25)
    """
    with Madx(stdout=False) as madx:
        logger.critical(f"Using: pyhdtoolkit {__version__} | cpymad {cpymad.__version__}  | {madx.version}")


# ----- DataFrames Utilities ----- #


def split_complex_columns(df: pd.DataFrame, drop: bool = False) -> pd.DataFrame:
    """
    .. versionadded:: 1.2.0

    Find complex valued columns in provided dataframe and split them
    into a column for the real and imaginary parts each. New columns
    will be named as the existing ones, with either ``_REAL`` or
    ``_IMAG`` appended to the name depending on which component of
    the complex value they represent.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to split the complex columns in.
    drop : bool
        If ``True``, the original complex columns will be dropped.
        Defaults to ``False``.

    Returns
    -------
    pandas.DataFrame
        A new dataframe with the complex columns split into real and
        imaginary parts, and the original complex columns potentially
        dropped.

    Example
    -------
        .. code-block:: python

            df = split_complex_columns(df, drop=True)
    """
    res = df.copy()
    complex_columns = res.select_dtypes(include="complex").columns
    for column in complex_columns:
        res[f"{column}_REAL"] = np.real(res[column])
        res[f"{column}_IMAG"] = np.imag(res[column])
    if drop is True:
        res = res.drop(columns=complex_columns)
    return res


def add_noise_to_ir_bpms(
    df: pd.DataFrame, max_index: int, stdev: float, columns: Sequence[str] | None = None
) -> pd.DataFrame:
    """
    .. versionadded:: 1.2.0

    Selects the appropriate IR BPMs according to the max index
    provided, and adds gaussian noise to each relevant column
    with the provided standard deviation.

    Important
    ---------
        The BPM names should be in the index of the dataframe.
        Selection is case insensitive.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to add noise to.
    max_index : int
        The maximum index of the IR BPMs to add noise to. This number
        is inclusive (i.e. the BPMs with this index will be selected).
    stdev : float
        The standard deviation of the gaussian noise to add.
    columns : Sequence[str], optional
        The columns to add noise to. If not given, all columns will be
        used. Defaults to ``None``.

    Returns
    -------
    pandas.DataFrame
        A new dataframe with the noise added to the provided columns.

    Example
    -------
        .. code-block:: python

            df = add_noise_to_ir_bpms(df, max_index=5, stdev=1e-6, columns=["DPSI"])
    """
    result = df.copy()
    selected_bpms = LHC_IR_BPM_REGEX.format(max_index=max_index)
    columns = columns or result.columns

    logger.debug(f"Adding noise to IR BPMs up to index {max_index} (included), with standard deviation {stdev}")
    array_length = len(result[result.index.str.match(selected_bpms, case=False)])
    logger.trace(f"Number of affected BPMs: {array_length}")

    for column in columns:
        logger.trace(f"Adding noise to column {column}")
        result.loc[result.index.str.match(selected_bpms, case=False), column] += RNG.normal(0, stdev, array_length)
    return result


def add_noise_to_arc_bpms(
    df: pd.DataFrame, min_index: int, stdev: float, columns: Sequence[str] | None = None
) -> pd.DataFrame:
    """
    .. versionadded:: 1.2.0

    Selects the appropriate non-IR BPMs according to the min index
    provided, and adds gaussian noise to each relevant column with
    the provided standard deviation.

    Warning
    -------
        This selects BPMs by ommission. It will find all IR BPMs up
        to *min_index* and will excluse these from the selection.

    Important
    ---------
        The BPM names should be in the index of the dataframe.
        Selection is case insensitive.

        
    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to add noise to.
    min_index : int
        The minimum index of the BPMs to add noise to. See warning
        caveat right above. This number is inclusive (i.e. the BPMs
        with this index will be selected).
    stdev : float
        The standard deviation of the gaussian noise to add.
    columns : Sequence[str], optional
        The columns to add noise to. If not given, all columns will be
        used. Defaults to ``None``.

    Returns
    -------
    pandas.DataFrame
        A new dataframe with the noise added to the wanted columns.

    Example
    -------
        .. code-block:: python

            df = add_noise_to_arc_bpms(df, min_index=8, stdev=1e-6, columns=["DPSI"])
    """
    result = df.copy()
    ir_bpms = LHC_IR_BPM_REGEX.format(max_index=min(1, min_index - 1))  # so that provided min_index is included
    columns = columns or result.columns

    logger.debug(f"Adding noise to arc BPMs from index {min_index} (included), with standard deviation {stdev}")
    array_length = len(result[~result.index.str.match(ir_bpms, case=False)])  # exclusive selection
    logger.trace(f"Number of affected BPMs: {array_length}")

    for column in columns:
        logger.trace(f"Adding noise to column {column}")
        result.loc[~result.index.str.match(ir_bpms, case=False), column] += RNG.normal(0, stdev, array_length)
    return result


# ----- MAD-X Setup Utilities ----- #


def apply_colin_corrs_balance(madx: Madx, /) -> None:
    """
    .. versionadded:: 0.20.0

    Applies the SbS local coupling correction settings from
    the 2022 commissioning as they were in the machine, and
    tilts of Q3s that would compensate for those settings.
    This way the bump of each corrector is very local to
    MQSX3 - MQSXQ3 and other effects can be added and studied,
    *pretending* a perfect local coupling correction.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object with your
        ``LHC`` setup. Positional only.

    Example
    -------
        .. code-block:: python

            apply_colin_corrs_balance(madx)
    """
    # ----- Let's balance IR1 ----- #
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[1], beam=1, quadrupoles=[3], sides="L", DPSI=-1.61e-3)
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[1], beam=1, quadrupoles=[3], sides="R", DPSI=1.41e-3)
    madx.globals["kqsx3.l1"] = 8e-4
    madx.globals["kqsx3.r1"] = 7e-4
    # ----- Let's balance IR2 ----- #
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[2], beam=1, quadrupoles=[3], sides="L", DPSI=-2.84e-3)
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[2], beam=1, quadrupoles=[3], sides="R", DPSI=2.84e-3)
    madx.globals["kqsx3.l2"] = -14e-4
    madx.globals["kqsx3.r2"] = -14e-4
    # ----- Let's balance IR5 ----- #
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[5], beam=1, quadrupoles=[3], sides="L", DPSI=-1.21e-3)
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[5], beam=1, quadrupoles=[3], sides="R", DPSI=1.21e-3)
    madx.globals["kqsx3.l5"] = 6e-4
    madx.globals["kqsx3.r5"] = 6e-4
    # ----- Let's balance IR8 ----- #
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[8], beam=1, quadrupoles=[3], sides="L", DPSI=-1e-3)
    lhc.misalign_lhc_ir_quadrupoles(madx, ips=[8], beam=1, quadrupoles=[3], sides="R", DPSI=1e-3)
    madx.globals["kqsx3.l8"] = -5e-4
    madx.globals["kqsx3.r8"] = -5e-4
    madx.command.twiss()


# ----- Fetching Utilities ----- #


def get_betastar_from_opticsfile(opticsfile: Path | str, check_symmetry: bool = True) -> float:
    """
    .. versionadded:: 0.16.0

    Parses the :math:`\\beta^{*}` value from the *opticsfile*
    content, which is in the first lines. This contains an
    optional check to ensure the betastar is the same for IP1
    and IP5. The values returned are in meters.

    Note
    ----
        For files in ``acc-models-lhc`` make sure to point
        to the strength file (see example below) where the
        :math:`\\beta^{*}` is set, as the opticsfile itself
        only contains call.

    Parameters
    ----------
    opticsfile : pathlib.Path | str
        Path object to the optics file.
    check_symmetry : bool
        If ``True``, the function will check that the betastar
        values for IP1 and IP5 are the same. Defaults to `True`.

    Returns
    -------
    float
        The :math:`\\beta^{*}` value parsed from the file.

    Raises
    ------
    AssertionError
        If the :math:`\\beta^{*}` value for IP1 and IP5 is
        not the same (in both planes too). This is only
        the case if *check_symmetry* is set to ``True``.

    Example
    -------
        .. code-block:: python

            get_betastar_from_opticsfile(
                "acc-models-lhc/strengths/ATS_Nominal/2022/squeeze/ats_30cm.madx"
            )
            # returns 0.3
    """
    file_lines = Path(opticsfile).read_text().split("\n")
    ip1_x_line, ip1_y_line, ip5_x_line, ip5_y_line = (line for line in file_lines if line.startswith("bet"))
    betastar_x_ip1 = float(shlex.split(ip1_x_line)[2])
    betastar_y_ip1 = float(shlex.split(ip1_y_line)[2])
    betastar_x_ip5 = float(shlex.split(ip5_x_line)[2])
    betastar_y_ip5 = float(shlex.split(ip5_y_line)[2])
    if check_symmetry and not (betastar_x_ip1 == betastar_y_ip1 == betastar_x_ip5 == betastar_y_ip5):
        msg = "The betastar values for IP1 and IP5 are not the same in both planes."
        raise AssertionError(msg)
    return betastar_x_ip1  # doesn't matter which plane, they're all the same
