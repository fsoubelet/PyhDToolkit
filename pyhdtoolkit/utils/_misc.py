"""
.. _utils-misc:

Miscellanous Personnal Utilities
--------------------------------

Private module that provides miscellaneous personnal utility functions.

.. warning::
    The functions in here are intented for personal use, and will most likely 
    **not** work on other people's machines.
"""
import shlex

from multiprocessing import cpu_count
from pathlib import Path

import cpymad

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit import __version__
from pyhdtoolkit.cpymadtools import errors

# ----- Constants ----- #

N_CPUS = cpu_count()


def log_runtime_versions() -> None:
    """
    .. versionadded:: 0.17.0

    Issues a ``CRITICAL``-level log stating the runtime versions of both `~pyhdtoolkit`, `cpymad` and ``MAD-X``.
    """
    with Madx(stdout=False) as mad:
        logger.critical(f"Using: pyhdtoolkit {__version__} | cpymad {cpymad.__version__}  | {mad.version}")


# ----- MAD-X Setup Utilities ----- #


def apply_colin_corrs_balance(madx: Madx) -> None:
    """
    .. versionadded:: 0.20.0

    Applies the local coupling correction settings from the 2022 commissioning as
    they were in the machine, and tilts of Q3s that would compensate for those settings.
    This way the bump of each corrector is very local to MQSX3 - Q3 and other effects can
    be added and studied in the machine, pretending a perfect local coupling correction.


    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object with your
            ``LHC`` setup.
    """
    # ----- Let's balance IR1 ----- #
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[1], beam=1, quadrupoles=[3], sides="L", DPSI=-1.61e-3)
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[1], beam=1, quadrupoles=[3], sides="R", DPSI=1.41e-3)
    madx.globals["kqsx3.l1"] = 8e-4
    madx.globals["kqsx3.r1"] = 7e-4
    # ----- Let's balance IR2 ----- #
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[2], beam=1, quadrupoles=[3], sides="L", DPSI=-2.84e-3)
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[2], beam=1, quadrupoles=[3], sides="R", DPSI=2.84e-3)
    madx.globals["kqsx3.l2"] = -14e-4
    madx.globals["kqsx3.r2"] = -14e-4
    # ----- Let's balance IR5 ----- #
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[5], beam=1, quadrupoles=[3], sides="L", DPSI=-1.21e-3)
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[5], beam=1, quadrupoles=[3], sides="R", DPSI=1.21e-3)
    madx.globals["kqsx3.l5"] = 6e-4
    madx.globals["kqsx3.r5"] = 6e-4
    # ----- Let's balance IR8 ----- #
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[8], beam=1, quadrupoles=[3], sides="L", DPSI=-1e-3)
    errors.misalign_lhc_ir_quadrupoles(madx, ips=[8], beam=1, quadrupoles=[3], sides="R", DPSI=1e-3)
    madx.globals["kqsx3.l8"] = -5e-4
    madx.globals["kqsx3.r8"] = -5e-4
    madx.command.twiss(chrom=True)


# ----- Fetching Utilities ----- #


def get_betastar_from_opticsfile(opticsfile: Path) -> float:
    """
    .. versionadded:: 0.16.0

    Parses the :math:`\\beta^{*}` value from the *opticsfile* content,
    which is in the first lines. This contains a check that ensures the betastar
    is the same for IP1 and IP5. The values returned are in meters.

    Args:
        opticsfile (Path): `pathlib.Path` object to the optics file.

    Returns:
        The :math:`\\beta^{*}` value parsed from the file.

    Raises:
        AssertionError: if the :math:`\\beta^{*}` value for IP1 and IP5 is not
            the same (in both planes too).
    """
    file_lines = opticsfile.read_text().split("\n")
    ip1_x_line, ip1_y_line, ip5_x_line, ip5_y_line = [line for line in file_lines if line.startswith("bet")]
    betastar_x_ip1 = float(shlex.split(ip1_x_line)[2])
    betastar_y_ip1 = float(shlex.split(ip1_y_line)[2])
    betastar_x_ip5 = float(shlex.split(ip5_x_line)[2])
    betastar_y_ip5 = float(shlex.split(ip5_y_line)[2])
    assert betastar_x_ip1 == betastar_y_ip1 == betastar_x_ip5 == betastar_y_ip5
    return betastar_x_ip1  # doesn't matter which plane, they're all the same
