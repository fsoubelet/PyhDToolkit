"""
.. _lhc-mist:

**Miscellaneous Utilities**

The functions below are miscellaneous utilities for the ``LHC``.
"""
from typing import List, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools import twiss
from pyhdtoolkit.cpymadtools.constants import (
    LHC_ANGLE_FLAGS,
    LHC_CROSSING_ANGLE_FLAGS,
    LHC_EXPERIMENT_STATE_FLAGS,
    LHC_IP2_SPECIAL_FLAG,
    LHC_IP_OFFSET_FLAGS,
    LHC_PARALLEL_SEPARATION_FLAGS,
)
from pyhdtoolkit.optics.ripken import _add_beam_size_to_df


def make_sixtrack_output(madx: Madx, energy: int) -> None:
    """
    .. versionadded:: 0.15.0

    Prepare output for a ``SixTrack`` run. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        energy (float): beam energy, in [GeV].

    Example:
        .. code-block:: python

            >>> make_sixtrack_output(madx, energy=6800)
    """
    logger.debug("Preparing outputs for SixTrack")

    logger.debug("Powering RF cavities")
    madx.globals["VRF400"] = 8 if energy < 5000 else 16  # is 6 at injection for protons iirc?
    madx.globals["LAGRF400.B1"] = 0.5  # cavity phase difference in units of 2pi
    madx.globals["LAGRF400.B2"] = 0.0

    logger.debug("Executing TWISS and SIXTRACK commands")
    madx.twiss()  # used by sixtrack
    madx.sixtrack(cavall=True, radius=0.017)  # this value is only ok for HL(LHC) magnet radius


def reset_lhc_bump_flags(madx: Madx) -> None:
    """
    .. versionadded:: 0.15.0

    Resets all LHC IP bump flags to 0.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Example:
        .. code-block:: python

            >>> reset_lhc_bump_flags(madx)
    """
    logger.debug("Resetting all LHC IP bump flags")
    ALL_BUMPS = (
        LHC_ANGLE_FLAGS
        + LHC_CROSSING_ANGLE_FLAGS
        + LHC_EXPERIMENT_STATE_FLAGS
        + LHC_IP2_SPECIAL_FLAG
        + LHC_IP_OFFSET_FLAGS
        + LHC_PARALLEL_SEPARATION_FLAGS
    )
    with madx.batch():
        madx.globals.update({bump: 0 for bump in ALL_BUMPS})


def get_lhc_tune_and_chroma_knobs(
    accelerator: str, beam: int = 1, telescopic_squeeze: bool = True, run3: bool = False
) -> Tuple[str, str, str, str]:
    """
    .. versionadded:: 0.16.0

    Gets names of knobs needed to match tunes and chromaticities as a tuple of strings,
    for the LHC or HLLHC machines. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        accelerator (str): Accelerator either 'LHC' (dQ[xy], dQp[xy] knobs) or 'HLLHC'
            (kqt[fd], ks[fd] knobs).
        beam (int): Beam to use, for the knob names. Defaults to 1.
        telescopic_squeeze (bool): if set to `True`, returns the knobs for Telescopic
            Squeeze configuration. Defaults to `True` to reflect run III scenarios.
        run3 (bool): if set to `True`, returns the Run 3 `*_op` knobs. Defaults to `False`.

    Returns:
        A `tuple` of strings with knobs for ``(qx, qy, dqx, dqy)``.

    Examples:
        .. code-block:: python

            >>> get_lhc_tune_and_chroma_knobs("LHC", beam=1, telescopic_squeeze=False)
            ('dQx.b1', 'dQy.b1', 'dQpx.b1', 'dQpy.b1')

        .. code-block:: python

            >>> get_lhc_tune_and_chroma_knobs("LHC", beam=2, run3=True)
            ('dQx.b2_op', 'dQx.b2_op', 'dQpx.b2_op', 'dQpx.b2_op')

        .. code-block:: python

            >>> get_lhc_tune_and_chroma_knobs("HLLHC", beam=2)
            ('kqtf.b2_sq', 'kqtd.b2_sq', 'ksf.b2_sq', 'ksd.b2_sq')
    """
    beam = 2 if beam == 4 else beam
    if run3:
        suffix = "_op"
    elif telescopic_squeeze:
        suffix = "_sq"
    else:
        suffix = ""

    if accelerator.upper() not in ("LHC", "HLLHC"):
        logger.error("Invalid accelerator name, only 'LHC' and 'HLLHC' implemented")
        raise NotImplementedError(f"Accelerator '{accelerator}' not implemented.")

    return {
        "LHC": (
            f"dQx.b{beam}{suffix}",
            f"dQy.b{beam}{suffix}",
            f"dQpx.b{beam}{suffix}",
            f"dQpy.b{beam}{suffix}",
        ),
        "HLLHC": (
            f"kqtf.b{beam}{suffix}",
            f"kqtd.b{beam}{suffix}",
            f"ksf.b{beam}{suffix}",
            f"ksd.b{beam}{suffix}",
        ),
    }[accelerator.upper()]


def get_lhc_bpms_list(madx: Madx) -> List[str]:
    """
    .. versionadded:: 0.16.0

    Returns the list of monitoring BPMs for the current LHC sequence in use.
    The BPMs are queried through a regex in the result of a ``TWISS`` command.

    .. note::
        As this function calls the ``TWISS`` command and requires that ``TWISS`` can
        succeed on your sequence.

    Args:
        madx (cpymad.madx.Madx): an instantiated cpymad.madx.Madx object.

    Returns:
        The `list` of BPM names.

    Example:
        .. code-block:: python

            >>> observation_bpms = get_lhc_bpms_list(madx)
    """
    twiss_df = twiss.get_twiss_tfs(madx).reset_index()
    bpms_df = twiss_df[twiss_df.NAME.str.contains("^bpm.*B[12]$", case=False, regex=True)]
    return bpms_df.NAME.tolist()


def get_sizes_at_ip(madx: Madx, ip: int, geom_emit_x: float = None, geom_emit_y: float = None) -> Tuple[float, float]:
    """
    .. versionadded:: 1.0.0

    Get the Lebedev beam sizes (horizontal and vertical) at the provided LHC *ip*.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ip (int): the IP to get the sizes at.
        geom_emit_x (float): the horizontal geometrical emittance to use for the
            calculation. If not provided, will look for the values of the
            ``geometric_emit_x`` variable in ``MAD-X``.
        geom_emit_y (float): the vertical geometrical emittance to use for the
            calculation. If not provided, will look for the values of the
            ``geometric_emit_y`` variable in ``MAD-X``.

    Returns:
        A tuple of the horizontal and vertical beam sizes at the provided *IP*.

    Example:
        .. code-block:: python

            >>> ip5_x, ip5_y = get_size_at_ip(madx, ip=5)
    """
    logger.debug(f"Getting horizotnal and vertical sizes at IP{ip:d} through Ripken parameters")
    geom_emit_x = geom_emit_x or madx.globals["geometric_emit_x"]
    geom_emit_y = geom_emit_y or madx.globals["geometric_emit_y"]

    twiss_tfs = twiss.get_twiss_tfs(madx, ripken=True)
    twiss_tfs = _add_beam_size_to_df(twiss_tfs, geom_emit_x, geom_emit_y)
    return twiss_tfs.loc[f"IP{ip:d}"].SIZE_X, twiss_tfs.loc[f"IP{ip:d}"].SIZE_Y
