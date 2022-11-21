"""
.. _cpymadtools-lhc:

LHC-Specific Utilities
----------------------

Module with functions to perform ``MAD-X`` actions through a `~cpymad.madx.Madx` object,
that are specific to LHC and HLLHC machines.
"""
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import tfs

from cpymad.madx import Madx
from loguru import logger
from optics_functions.coupling import coupling_via_cmatrix

from pyhdtoolkit.cpymadtools import twiss
from pyhdtoolkit.cpymadtools.constants import (
    DEFAULT_TWISS_COLUMNS,
    LHC_ANGLE_FLAGS,
    LHC_CROSSING_ANGLE_FLAGS,
    LHC_CROSSING_SCHEMES,
    LHC_EXPERIMENT_STATE_FLAGS,
    LHC_IP2_SPECIAL_FLAG,
    LHC_IP_OFFSET_FLAGS,
    LHC_KCD_KNOBS,
    LHC_KCO_KNOBS,
    LHC_KCOSX_KNOBS,
    LHC_KCOX_KNOBS,
    LHC_KCS_KNOBS,
    LHC_KCSSX_KNOBS,
    LHC_KCSX_KNOBS,
    LHC_KCTX_KNOBS,
    LHC_KO_KNOBS,
    LHC_KQS_KNOBS,
    LHC_KQSX_KNOBS,
    LHC_KQTF_KNOBS,
    LHC_KSF_KNOBS,
    LHC_KSS_KNOBS,
    LHC_PARALLEL_SEPARATION_FLAGS,
    MONITOR_TWISS_COLUMNS,
)
from pyhdtoolkit.cpymadtools.utils import _get_k_strings
from pyhdtoolkit.optics.ripken import _add_beam_size_to_df

# ----- Constants ----- #

# These need to be formatted
# After number 10 are either MQ or MQT quadrupole elements, which officially belong to the arcs
LHC_IR_QUADS_PATTERNS: Dict[int, List[str]] = {
    1: ["^MQXA.1{side}{ip:d}", "^MQXFA.[AB]1{side}{ip:d}"],  # Q1 LHC, Q1A & Q1B HL-LHC
    2: ["^MQXB.[AB]2{side}{ip:d}", "^MQXB.[AB]2{side}{ip:d}"],  # Q2A & Q2B LHC, Q2A & Q2B HL-LHC
    3: ["^MQXA.3{side}{ip:d}", "^MQXFA.[AB]3{side}{ip:d}"],  # Q3 LHC, Q3A & Q3B HL-LHC
    4: ["^MQY.4{side}{ip:d}.B{beam:d}"],  # Q4 LHC & HL-LHC
    5: ["^MQML.5{side}{ip:d}.B{beam:d}"],  # Q5 LHC & HL-LHC
    6: ["^MQML.6{side}{ip:d}.B{beam:d}"],  # Q6 LHC & HL-LHC
    7: ["^MQM.[AB]7{side}{ip:d}.B{beam:d}"],  # Q7A & Q7B LHC & HL-LHC
    8: ["^MQML.8{side}{ip:d}.B{beam:d}"],  # Q8 LHC & HL-LHC
    9: ["^MQM.9{side}{ip:d}.B{beam:d}", "^MQMC.9{side}{ip:d}.B{beam:d}"],  # Q9 3.4m then 2.4m LHC & HL-LHC
    10: ["^MQML.10{side}{ip:d}.B{beam:d}"],  # Q10 4.8m LHC & HL-LHC
}


# ----- Setup Utilities ----- #


def prepare_lhc_run2(
    opticsfile: str, beam: int = 1, use_b4: bool = False, energy: float = 6500, slicefactor: int = None, **kwargs
) -> Madx:
    """
    .. versionadded:: 1.0.0

    Returns a prepared default ``LHC`` setup for the given *opticsfile*, for a Run 2 setup. Both beams
    are made with a default Run 2 configuration, and the ``lhcb`` sequence for the given beam is re-cycled
    from ``MSIA.EXIT.B{beam}`` as in the ``OMC`` model_creator, and then ``USE``-d. Specific variable settings
    can be given as keyword arguments.

    .. important::
        As this is a Run 2 setup, it is assumed that files are organised in the typical setup as found on ``AFS``.
        The sequence file will be looked for as a relative location from the optics file: it is assumed that next
        to the sequence file is a **PROTON** or **ION** folder with the opticsfiles.

    .. note::
        Matching is **not** performed by this function and should be taken care of by the user, but the working point
        should be set by the definitions in the *opticsfile*. Beware that passing specific variables as keyword arguments
        might change that working point.

    Args:
        opticsfile (str): name of the optics file to be used. Can be the string path to the file or only the opticsfile
            name itself, which would be looked for at the **acc-models-lhc/operation/optics/** path.
        beam (int): which beam to set up for. Defaults to beam 1.
        use_b4 (bool): if `True`, the lhcb4 sequence file will be used. This is the beam 2 sequence but for tracking
            purposes. Defaults to `False`.
        energy (float): beam energy to set up for, in GeV. Defaults to 6500.
        slicefactor (int): if provided, the sequence will be sliced and made thin. Defaults to `None`,
            which leads to an unsliced sequence.
        **kwargs: if `echo` or `warn` are found in the keyword arguments they will be transmitted as options
            to ``MAD-X`` (by default they are given as `False`). Any other keyword argument is transmitted to
            the `~cpymad.madx.Madx` creation call.

    Returns:
        An instanciated `~cpymad.madx.Madx` object with the required configuration.

    Example:
        .. code-block:: python

            >>> madx = prepare_lhc_run2(
            ...     "/afs/cern.ch/eng/lhc/optics/runII/2018/PROTON/opticsfile.22", beam=2, stdout=True
            ... )
    """
    if use_b4 and beam != 2:
        logger.error("Cannot use beam 4 sequence file for beam 1")
        raise ValueError("Cannot use beam 4 sequence file for beam 1")

    def _run2_sequence_from_opticsfile(opticsfile: Path, use_b4: bool = False) -> Path:
        filename = "lhc_as-built.seq" if not use_b4 else "lhcb4_as-built.seq"
        seqfile_path = opticsfile.parent.parent / filename
        if not seqfile_path.is_file():
            logger.error(f"Could not find sequence file '{filename}' at expected location '{seqfile_path}'")
        return seqfile_path

    logger.debug("Creating Run 2 setup MAD-X instance")
    echo, warn = kwargs.pop("echo", False), kwargs.pop("warn", False)

    madx = Madx(**kwargs)
    madx.option(echo=echo, warn=warn)
    logger.debug("Calling sequence")
    madx.call(_fullpath(_run2_sequence_from_opticsfile(Path(opticsfile))))
    make_lhc_beams(madx, energy=energy, b4=use_b4)

    if slicefactor:
        logger.debug("A slicefactor was provided, slicing the sequence")
        make_lhc_thin(madx, sequence=f"lhcb{beam:d}", slicefactor=slicefactor)
        make_lhc_beams(madx, energy=energy, b4=use_b4)

    re_cycle_sequence(madx, sequence=f"lhcb{beam:d}", start=f"MSIA.EXIT.B{beam:d}")

    logger.debug("Calling optics file from the 'operation/optics' folder")
    madx.call(opticsfile)

    make_lhc_beams(madx, energy=energy, b4=use_b4)
    madx.command.use(sequence=f"lhcb{beam:d}")
    return madx


def prepare_lhc_run3(
    opticsfile: str, beam: int = 1, use_b4: bool = False, energy: float = 6800, slicefactor: int = None, **kwargs
) -> Madx:
    """
    .. versionadded:: 1.0.0

    Returns a prepared default ``LHC`` setup for the given *opticsfile*, for a Run 3 setup. Both beams
    are made with a default Run 3 configuration, and the provided sequence is re-cycled from ``MSIA.EXIT.[B12]``
    as in the ``OMC`` model_creator, then ``USE``-d. Specific variable settings can be given as keyword arguments.

    .. important::
        As this is a Run 3 setup, it is assumed that the ``acc-models-lhc`` repo is available in the root space,``.
        which is needed by the different files in ``acc-models-lhc``.

    .. note::
        Matching is **not** performed by this function and should be taken care of by the user, but the working
        point should be set by the variable definitions in the *opticsfile*.

    Args:
        opticsfile (str): name of the optics file to be used. Can be the string path to the file or only the opticsfile
            name itself, which would be looked for at the **acc-models-lhc/operation/optics/** path.
        beam (int): which beam to set up for. Defaults to beam 1.
        use_b4 (bool): if `True`, the lhcb4 sequence file will be used. This is the beam 2 sequence but for tracking
            purposes. Defaults to `False`.
        energy (float): beam energy to set up for, in GeV. Defaults to 6800.
        slicefactor (int): if provided, the sequence will be sliced and made thin. Defaults to `None`,
            which leads to an unsliced sequence.
        **kwargs: if `echo` or `warn` are found in the keyword arguments they will be transmitted as options to ``MAD-X``.
            Any other keyword argument is transmitted to the `~cpymad.madx.Madx` creation call.

    Returns:
        An instanciated `~cpymad.madx.Madx` object with the required configuration.

    Example:
        .. code-block:: python

            >>> madx = prepare_lhc_run3(
            ...     "R2022a_A30cmC30cmA10mL200cm.madx", slicefactor=4, stdout=True
            ... )
    """
    if use_b4 and beam != 2:
        logger.error("Cannot use beam 4 sequence file for beam 1")
        raise ValueError("Cannot use beam 4 sequence file for beam 1")

    logger.debug("Creating Run 3 setup MAD-X instance")
    echo, warn = kwargs.pop("echo", False), kwargs.pop("warn", False)

    madx = Madx(**kwargs)
    madx.option(echo=echo, warn=warn)

    sequence = "lhc.seq" if not use_b4 else "lhcb4.seq"
    logger.debug(f"Calling sequence file '{sequence}'")
    madx.call(f"acc-models-lhc/{sequence}")
    make_lhc_beams(madx, energy=energy, b4=use_b4)

    if slicefactor:
        logger.debug("A slicefactor was provided, slicing the sequence")
        make_lhc_thin(madx, sequence=f"lhcb{beam:d}", slicefactor=slicefactor)
        make_lhc_beams(madx, energy=energy, b4=use_b4)

    re_cycle_sequence(madx, sequence=f"lhcb{beam:d}", start=f"MSIA.EXIT.B{beam:d}")

    logger.debug("Calling optics file from the 'operation/optics' folder")
    if Path(opticsfile).is_file():
        madx.call(opticsfile)
    else:
        madx.call(f"acc-models-lhc/operation/optics/{Path(opticsfile).with_suffix('.madx')}")

    make_lhc_beams(madx, energy=energy, b4=use_b4)
    madx.command.use(sequence=f"lhcb{beam:d}")
    return madx


class LHCSetup:
    """
    .. versionadded:: 1.0.0

    This is a context manager to prepare an LHC Run 2 or Run 3 setup: calling sequences and opticsfile,
    re-cycling as is done in the ``OMC`` model creator, making beams, potentially slicing, etc. For details
    on the achieved setups, look at the `~prepare_lhc_run2` or `~prepare_lhc_run3` functions.

    .. important::
        For the Run 3 setup, it is assumed that the **acc-models-lhc** repo is available in the root space.

    .. note::
        Matching is **not** performed by this setup and should be taken care of by the user, but the working
        point should be set by the definitions in the *opticsfile*.

    .. note::
        If you intend to do tracking for beam 2, remember that the ``lhcb4`` sequence needs to be called.
        This is handled by giving the ``use_b4`` argument as `True` to the constructor.

    Args:
        run (int): which run to set up for, should be 2 or 3. Defaults to run 3.
        opticsfile (str): name of the opticsfile to be used. For a Run 2 setup, should be the string path to the file.
            For a Run 3 setup, can be the string path to the file or only the opticsfile name itself, which would be
            looked for at the **acc-models-lhc/operation/optics/** path. Defaults to `None`, which will raise an error.
        beam (int): which beam to set up for. Defaults to beam 1.
        use_b4 (bool): if `True`, the lhcb4 sequence file will be used. This is the beam 2 sequence but for tracking
            purposes. Defaults to `False`.
        energy (float): beam energy to set up for, in GeV. Defaults to 6800, to match the default of run 3.
        slicefactor (int): if provided, the sequence will be sliced and "made thin". Defaults to `None`,
            which leads to an unsliced sequence.
        **kwargs: if `echo` or `warn` are found in the keyword arguments they will be transmitted as options to ``MAD-X``.
            Any other keyword argument is transmitted to the `~cpymad.madx.Madx` creation call.

    Returns:
        An instanciated context manager `~cpymad.madx.Madx` object with the required configuration.

    Raises:
        NotImplementedError: if the *run* argument is not 2 or 3.
        AssertionError: if the *opticsfile* argument is not provided.

    Examples:

        Get a Run 2 setup for beam 2:

        .. code-block:: python

            >>> with LHCSetup(run=2, opticsfile="2018/PROTON/opticsfile.22", beam=2) as madx:
            ...    # do some stuff

        Get a Run 3 setup for beam 1, with a sliced sequence and muted output:

        .. code-block:: python

            >>> with LHCSetup(run=3, opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", slicefactor=4, stdout=False) as madx:
            ...    # do some stuff
    """

    def __init__(
        self,
        run: int = 3,
        opticsfile: str = None,
        beam: int = 1,
        use_b4: bool = False,
        energy: float = 6800,
        slicefactor: int = None,
        **kwargs,
    ):
        assert opticsfile is not None, "An opticsfile must be provided"
        if use_b4 and beam != 2:
            logger.error("Cannot use beam 4 sequence file for beam 1")
            raise ValueError("Cannot use beam 4 sequence file for beam 1")

        if int(run) not in (2, 3):
            raise NotImplementedError("This setup is only possible for Run 2 and Run 3 configurations.")
        elif run == 2:
            self.madx = prepare_lhc_run2(
                opticsfile=opticsfile, beam=beam, use_b4=use_b4, energy=energy, slicefactor=slicefactor, **kwargs
            )
        else:
            self.madx = prepare_lhc_run3(
                opticsfile=opticsfile, beam=beam, use_b4=use_b4, energy=energy, slicefactor=slicefactor, **kwargs
            )

    def __enter__(self):
        return self.madx

    def __exit__(self, *exc_info):
        self.madx.quit()


# ----- Configuration Utlites ----- #


def make_lhc_beams(
    madx: Madx,
    energy: float = 7000,
    emittance_x: float = 3.75e-6,
    emittance_y: float = 3.75e-6,
    b4: bool = False,
    **kwargs,
) -> None:
    """
    .. versionadded:: 0.15.0

    Defines beams with default configuratons for ``LHCB1`` and ``LHCB2`` sequences.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        energy (float): beam energy, in [GeV]. Defaults to 6500.
        emittance_x (float): horizontal emittance in [m]. Will be used to calculate
            geometric emittance which is then fed to the ``BEAM`` command.
        emittance_y (float): vertical emittance in [m]. Will be used to calculate
            geometric emittance which is then fed to the ``BEAM`` command.
        b4 (bool): if `True`, will consider one is using ``lhb4`` to do tracking on beam 2,
            and will properly set the ``bv`` flag to 1. Defaults to `False`.
        **kwargs: Any keyword argument that can be given to the ``MAD-X`` ``BEAM`` command.

    Examples:

        .. code-block:: python

            >>> make_lhc_beams(madx, energy=6800, emittance_x=2.5e-6, emittance_y=3e-6)

        Setting up in a way compatible for tracking of beam 2 (needs to call ``lhcb4`` and set
        ``bv`` to 1):

        .. code-block:: python

            >>> make_lhc_beams(madx, energy=6800, emittance_x=2.5e-6, emittance_y=3e-6, b4=True)
    """
    logger.debug("Making default beams for 'lhcb1' and 'lhbc2' sequences")
    madx.globals["NRJ"] = energy
    madx.globals["brho"] = energy * 1e9 / madx.globals.clight
    geometric_emit_x = madx.globals["geometric_emit_x"] = emittance_x / (energy / 0.938)
    geometric_emit_y = madx.globals["geometric_emit_y"] = emittance_y / (energy / 0.938)

    for beam in (1, 2):
        bv = 1 if beam == 1 or b4 is True else -1
        logger.debug(f"Defining beam for sequence 'lhcb{beam:d}'")
        madx.command.beam(
            sequence=f"lhcb{beam:d}",
            particle="proton",
            bv=bv,
            energy=energy,
            npart=1.15e11,
            ex=geometric_emit_x,
            ey=geometric_emit_y,
            sige=4.5e-4,
            **kwargs,
        )


def make_lhc_thin(madx: Madx, sequence: str, slicefactor: int = 1, **kwargs) -> None:
    """
    .. versionadded:: 0.15.0

    Executes the ``MAKETHIN`` command for the LHC sequence as previously done in ``MAD-X`` macros.
    This will use the ``teapot`` style and will enforce ``makedipedge``.

    One can find an exemple use of this function in the :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>`
    and :ref:`Free Tracking <demo-free-tracking>` example galleries.

    Args:
        madx (cpymad.madx.Madx): an instantiated `~cpymad.madx.Madx` object.
        sequence (str): the sequence to use for the ``MAKETHIN`` command.
        slicefactor (int): the slice factor to apply in ``MAKETHIN``, which is a factor
            applied to default values for different elements, as did the old macro. Defaults
            to 1.
        **kwargs: any keyword argument will be transmitted to the ``MAD-X`` ``MAKETHN``
            command, namely ``style`` (will default to ``teapot``) and the ``makedipedge``
            flag (will default to `True`).

    Example:
        .. code-block:: python

            >>> make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
    """
    logger.debug(f"Slicing sequence '{sequence}'")
    madx.select(flag="makethin", clear=True)
    four_slices_patterns = [r"mbx\.", r"mbrb\.", r"mbrc\.", r"mbrs\."]
    four_slicefactor_patterns = [
        r"mqwa\.",
        r"mqwb\.",
        r"mqy\.",
        r"mqm\.",
        r"mqmc\.",
        r"mqml\.",
        r"mqtlh\.",
        r"mqtli\.",
        r"mqt\.",
    ]

    logger.debug("Defining slices for general MB and MQ elements")
    madx.select(flag="makethin", class_="MB", slice_=2)
    madx.select(flag="makethin", class_="MQ", slice_=2 * slicefactor)

    logger.debug("Defining slices for triplets")
    madx.select(flag="makethin", class_="mqxa", slice_=16 * slicefactor)
    madx.select(flag="makethin", class_="mqxb", slice_=16 * slicefactor)

    logger.debug("Defining slices for various specifc mb elements")
    for pattern in four_slices_patterns:
        madx.select(flag="makethin", pattern=pattern, slice_=4)

    logger.debug("Defining slices for varous specifc mq elements")
    for pattern in four_slicefactor_patterns:
        madx.select(flag="makethin", pattern=pattern, slice_=4 * slicefactor)

    madx.use(sequence=sequence)
    style = kwargs.get("style", "teapot")
    makedipedge = kwargs.get("makedipedge", False)  # defaults to False to compensate default TEAPOT style
    madx.command.makethin(sequence=sequence, style=style, makedipedge=makedipedge)


def re_cycle_sequence(madx: Madx, sequence: str = "lhcb1", start: str = "IP3") -> None:
    """
    .. versionadded:: 0.15.0

    Re-cycles the provided *sequence* from a different starting point, given as *start*.

    One can find an exemple use of this function in the :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>`
    and :ref:`Free Tracking <demo-free-tracking>` example galleries.

    Args:
        madx (cpymad.madx.Madx): an instantiated `~cpymad.madx.Madx` object.
        sequence (str): the sequence to re-cycle.
        start (str): element to start the new cycle from.

    Example:
        .. code-block:: python

            >>> lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
    """
    logger.debug(f"Re-cycling sequence '{sequence}' from {start}")
    madx.command.seqedit(sequence=sequence)
    madx.command.flatten()
    madx.command.cycle(start=start)
    madx.command.endedit()


def lhc_orbit_variables() -> Tuple[List[str], Dict[str, str]]:
    """
    .. versionadded:: 0.8.0

    Get the variable names used for orbit setup in the (HL)LHC. Initial implementation
    credits go to :user:`Joschua Dilly <joschd>`.

    Returns:
        A `tuple` with a `list` of all orbit variables, and a `dict` of additional variables,
        that in the default configurations have the same value as another variable.

    Example:
        .. code-block:: python

            >>> variables, specials = lhc_orbit_variables()
    """
    logger.trace("Returning (HL)LHC orbit variables")
    on_variables = (
        "crab1",
        "crab5",  # exists only in HL-LHC
        "x1",
        "sep1",
        "o1",
        "oh1",
        "ov1",
        "x2",
        "sep2",
        "o2",
        "oe2",
        "a2",
        "oh2",
        "ov2",
        "x5",
        "sep5",
        "o5",
        "oh5",
        "ov5",
        "x8",
        "sep8",
        "o8",
        "a8",
        "sep8h",
        "x8v",
        "oh8",
        "ov8",
        "alice",
        "sol_alice",
        "lhcb",
        "sol_atlas",
        "sol_cms",
    )
    variables = [f"on_{var}" for var in on_variables] + [f"phi_IR{ir:d}" for ir in (1, 2, 5, 8)]
    special = {
        "on_ssep1": "on_sep1",
        "on_xx1": "on_x1",
        "on_ssep5": "on_sep5",
        "on_xx5": "on_x5",
    }
    return variables, special


def setup_lhc_orbit(madx: Madx, scheme: str = "flat", **kwargs) -> Dict[str, float]:
    """
    .. versionadded:: 0.8.0

    Automated orbit setup for (HL)LHC runs, for some default schemes. It is assumed that at
    least sequence and optics files have been called. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        scheme (str): the default scheme to apply, as defined in the ``LHC_CROSSING_SCHEMES``
            constant. Accepted values are keys of `LHC_CROSSING_SCHEMES`. Defaults to *flat*
            (every orbit variable to 0).
        **kwargs: Any standard crossing scheme variables (``on_x1``, ``phi_IR1``, etc). Values
            given here override the values in the default scheme configurations.

    Returns:
        A `dict` of all orbit variables set, and their values as set in the ``MAD-X`` globals.

    Example:
        .. code-block:: python

            >>> orbit_setup = setup_lhc_orbit(madx, scheme="lhc_top")
    """
    if scheme not in LHC_CROSSING_SCHEMES.keys():
        logger.error(f"Invalid scheme parameter, should be one of {LHC_CROSSING_SCHEMES.keys()}")
        raise ValueError("Invalid scheme parameter given")

    logger.debug("Getting orbit variables")
    variables, special = lhc_orbit_variables()

    scheme_dict = LHC_CROSSING_SCHEMES[scheme]
    final_scheme = {}

    for orbit_variable in variables:
        variable_value = kwargs.get(orbit_variable, scheme_dict.get(orbit_variable, 0))
        logger.trace(f"Setting orbit variable '{orbit_variable}' to {variable_value}")
        # Sets value in MAD-X globals & returned dict, taken from scheme dict or kwargs if provided
        madx.globals[orbit_variable] = final_scheme[orbit_variable] = variable_value

    for special_variable, copy_from in special.items():
        special_variable_value = kwargs.get(special_variable, madx.globals[copy_from])
        logger.trace(f"Setting special orbit variable '{special_variable}' to {special_variable_value}")
        # Sets value in MAD-X globals & returned dict, taken from a given global or kwargs if provided
        madx.globals[special_variable] = final_scheme[special_variable] = special_variable_value

    return final_scheme


# ----- Magnets Powering ----- #


def apply_lhc_colinearity_knob(madx: Madx, colinearity_knob_value: float = 0, ir: int = None) -> None:
    """
    .. versionadded:: 0.15.0

    Applies the a trim of the LHC colinearity knob.

    .. note::
        If you don't know what this is, you really should not be using this function.

    .. tip::
        The convention, which is also the one I implemented in ``LSA`` for the ``LHC``, is that a
        positive value of the colinearity knob results in a powering increase of the ``MQSX`` *right*
        of the IP, and a powering decrease of the ``MQSX`` *left* of the IP.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        colinearity_knob_value (float): Units of the colinearity knob to apply. Defaults to 0 so users
            don't mess up local IR coupling by mistake. This should be a positive integer, normally between 1
            and 10.
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.

    Example:
        .. code-block:: python

            >>> apply_lhc_colinearity_knob(madx, colinearity_knob_value=5, ir=1)
    """
    logger.debug(f"Applying Colinearity knob with a unit setting of {colinearity_knob_value}")
    logger.warning("You should re-match tunes & chromaticities after this colinearity knob is applied")
    knob_variables = (f"KQSX3.R{ir:d}", f"KQSX3.L{ir:d}")  # MQSX IP coupling correctors powering
    right_knob, left_knob = knob_variables

    madx.globals[right_knob] = colinearity_knob_value * 1e-4
    logger.debug(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    madx.globals[left_knob] = -1 * colinearity_knob_value * 1e-4
    logger.debug(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_colinearity_knob_delta(madx: Madx, colinearity_knob_delta: float = 0, ir: int = None) -> None:
    """
    .. versionadded:: 0.21.0

    This is essentially the same as `.apply_lhc_colinearity_knob`, but instead of a applying fixed powering
    value, it applies a delta to the (potentially) existing value.

    .. note::
        If you don't know what this is, you really should not be using this function.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        colinearity_knob_delta (float): Units of the colinearity knob to vary the existing powerings with.
            Defaults to 0.
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.

    Example:
        .. code-block:: python

            >>> apply_lhc_colinearity_knob_delta(madx, colinearity_knob_delta=3.5, ir=1)
    """
    logger.debug(f"Applying Colinearity knob delta of {colinearity_knob_delta}")
    logger.warning("You should re-match tunes & chromaticities after this delta is applied")
    knob_variables = (f"KQSX3.R{ir:d}", f"KQSX3.L{ir:d}")  # MQSX IP coupling correctors powering
    right_knob, left_knob = knob_variables

    logger.debug("Query current knob values")
    current_right = madx.eval(right_knob)  # ugly, but avoids KeyError if not defined yet
    current_left = madx.eval(left_knob)  # augly, but avoids KeyError if not defined yet
    logger.debug(f"Current right knob value is {current_right}")
    logger.debug(f"Current left knob value is {current_left}")

    madx.globals[right_knob] = current_right + colinearity_knob_delta * 1e-4
    logger.debug(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    madx.globals[left_knob] = current_left - colinearity_knob_delta * 1e-4
    logger.debug(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_rigidity_waist_shift_knob(
    madx: Madx, rigidty_waist_shift_value: float = 0, ir: int = None, side: str = "left"
) -> None:
    """
    .. versionadded:: 0.15.0

    Applies a trim of the LHC rigidity waist shift knob, moving the waist left or right of IP.
    The waist shift is achieved by moving all four betatron waists simltaneously: unbalancing
    the triplet powering knobs of the left and right-hand sides of the IP.

    .. note::
        If you don't know what this is, you really should not be using this function.

    .. warning::
        Applying the shift will modify your tunes and is likely to flip them, making a subsequent matching
        impossible if your lattice has coupling. To avoid this, one should match to tunes split further apart
        before applying the waist shift knob, and then match to the desired working point. For instance for
        the LHC, matching to (62.27, 60.36) before applying and afterwards rematching to (62.31, 60.32) usually
        works well.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        rigidty_waist_shift_value (float): Units of the rigidity waist shift knob (positive values only).
        ir (int): The Interaction Region to apply the knob to, should be one of [1, 2, 5, 8].
            Classically 1 or 5.
        side (str): Which side of the IP to move the waist to, determines a sign in the calculation.
            Defaults to `left`, which means :math:`s_{\\mathrm{waist}} \\lt s_{\\mathrm{ip}}` (and
            setting it to `right` would move the waist such that
            :math:`s_{\\mathrm{waist}} \\gt s_{\\mathrm{ip}}`).

    Example:
        .. code-block:: python

            >>> matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.27, 60.36)
            >>> apply_lhc_rigidity_waist_shift_knob(madx, rigidty_waist_shift_value=1.5, ir=5)
            >>> matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32)
    """
    logger.debug(f"Applying Rigidity Waist Shift knob with a unit setting of {rigidty_waist_shift_value}")
    logger.warning("You should re-match tunes & chromaticities after this rigid waist shift knob is applied")
    right_knob, left_knob = f"kqx.r{ir:d}", f"kqx.l{ir:d}"  # IP triplet default knob (no trims)

    current_right_knob = madx.globals[right_knob]
    current_left_knob = madx.globals[left_knob]

    if side.lower() == "left":
        madx.globals[right_knob] = (1 - rigidty_waist_shift_value * 0.005) * current_right_knob
        madx.globals[left_knob] = (1 + rigidty_waist_shift_value * 0.005) * current_left_knob
    elif side.lower() == "right":
        madx.globals[right_knob] = (1 + rigidty_waist_shift_value * 0.005) * current_right_knob
        madx.globals[left_knob] = (1 - rigidty_waist_shift_value * 0.005) * current_left_knob
    else:
        logger.error(f"Given side '{side}' invalid, only 'left' and 'right' are accepted values.")
        raise ValueError("Invalid value for parameter 'side'.")

    logger.debug(f"Set '{right_knob}' to {madx.globals[right_knob]}")
    logger.debug(f"Set '{left_knob}' to {madx.globals[left_knob]}")


def apply_lhc_coupling_knob(
    madx: Madx, coupling_knob: float = 0, beam: int = 1, telescopic_squeeze: bool = True
) -> None:
    """
    .. versionadded:: 0.15.0

    Applies a trim of the LHC coupling knob to reach the desired :math:`|C^{-}|` value.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        coupling_knob (float): Desired value for the Cminus, typically a few units of ``1E-3``.
            Defaults to 0 so users don't mess up coupling by mistake.
        beam (int): beam to apply the knob to. Defaults to beam 1.
        telescopic_squeeze (bool): if set to `True`, uses the knobs for Telescopic Squeeze configuration.
            Defaults to `True` since `v0.9.0`.

    Example:
        .. code-block:: python

            >>> apply_lhc_coupling_knob(madx, coupling_knob=5e-4, beam=1)
    """
    # NOTE: for maintainers, no `_op` suffix on ATS coupling knobs, only `_sq` even in Run 3
    logger.debug("Applying coupling knob")
    logger.warning("You should re-match tunes & chromaticities after this coupling knob is applied")
    suffix = "_sq" if telescopic_squeeze else ""
    # NOTE: Only using this knob will give a dqmin very close to coupling_knob
    # If one wants to also assign f"CMIS.b{beam:d}{suffix}" the dqmin will be > coupling_knob
    knob_name = f"CMRS.b{beam:d}{suffix}"

    logger.debug(f"Knob '{knob_name}' is {madx.globals[knob_name]} before implementation")
    madx.globals[knob_name] = coupling_knob
    logger.debug(f"Set '{knob_name}' to {madx.globals[knob_name]}")


def carry_colinearity_knob_over(madx: Madx, ir: int, to_left: bool = True) -> None:
    """
    .. versionadded:: 0.20.0

    Removes the powering setting on one side of the colinearty knob and applies it to the
    other side.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ir (int): The Interaction Region around which to apply the change, should be
            one of [1, 2, 5, 8].
        to_left (bool): If `True`, the magnet right of IP is de-powered of and its powering
            is transferred to the magnet left of IP. If `False`, then the opposite happens.
            Defaults to `True`.

    Example:
        .. code-block:: python

            >>> carry_colinearity_knob_over(madx, ir=5, to_left=True)
    """
    side = "left" if to_left else "right"
    logger.debug(f"Carrying colinearity knob powering around IP{ir:d} over to the {side} side")

    left_variable, right_variable = f"kqsx3.l{ir:d}", f"kqsx3.r{ir:d}"
    left_powering, right_powering = madx.globals[left_variable], madx.globals[right_variable]
    logger.debug(f"Current powering values are: '{left_variable}'={left_powering} | '{right_variable}'={left_powering}")

    new_left = left_powering + right_powering if to_left else 0
    new_right = 0 if to_left else left_powering + right_powering
    logger.debug(f"New powering values are: '{left_variable}'={new_left} | '{right_variable}'={new_right}")
    madx.globals[left_variable] = new_left
    madx.globals[right_variable] = new_right
    logger.debug("New powerings applied")


def power_landau_octupoles(madx: Madx, beam: int, mo_current: float, defective_arc: bool = False) -> None:
    """
    .. versionadded:: 0.15.0

    Powers the Landau octupoles in the (HL)LHC.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam (int): beam to use.
        mo_current (float): `MO` powering, in [A].
        defective_arc: If set to `True`, the ``KOD`` in Arc 56 are powered for less ``Imax``.

    Example:
        .. code-block:: python

            >>> power_landau_octupoles(madx, beam=1, mo_current=350, defect_arc=True)
    """
    try:
        brho = madx.globals.nrj * 1e9 / madx.globals.clight  # clight is MAD-X constant
    except AttributeError as madx_error:
        logger.exception("The global MAD-X variable 'NRJ' should have been set in the optics files but is not defined.")
        raise EnvironmentError("No 'NRJ' variable found in scripts") from madx_error

    logger.debug(f"Powering Landau Octupoles, beam {beam} @ {madx.globals.nrj} GeV with {mo_current} A.")
    strength = mo_current / madx.globals.Imax_MO * madx.globals.Kmax_MO / brho
    beam = 2 if beam == 4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            octupole = f"KO{fd}.{arc}"
            logger.debug(f"Powering element '{octupole}' at {strength} Amps")
            madx.globals[octupole] = strength

    if defective_arc and (beam == 1):
        madx.globals["KOD.A56B1"] = strength * 4.65 / 6  # defective MO group


def deactivate_lhc_arc_sextupoles(madx: Madx, beam: int) -> None:
    """
    .. versionadded:: 0.15.0

    Deactivates all arc sextupoles in the (HL)LHC.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam (int): beam to use.

    Example:
        .. code-block:: python

            >>> deactivate_lhc_arc_sextupoles(madx, beam=1)
    """
    # KSF1 and KSD2 - Strong sextupoles of sectors 81/12/45/56
    # KSF2 and KSD1 - Weak sextupoles of sectors 81/12/45/56
    # Rest: Weak sextupoles in sectors 78/23/34/67
    logger.debug(f"Deactivating all arc sextupoles for beam {beam}.")
    beam = 2 if beam == 4 else beam

    for arc in _all_lhc_arcs(beam):
        for fd in "FD":
            for i in (1, 2):
                sextupole = f"KS{fd}{i:d}.{arc}"
                logger.debug(f"De-powering element '{sextupole}'")
                madx.globals[sextupole] = 0.0


def vary_independent_ir_quadrupoles(
    madx: Madx, quad_numbers: Sequence[int], ip: int, sides: Sequence[str] = ("r", "l"), beam: int = 1
) -> None:
    """
    .. versionadded:: 0.15.0

    Sends the ``VARY`` commands for the desired quadrupoles in the IR surrounding the provided *ip*.
    The independent quadrupoles for which this is implemented are Q4 to Q13 included. This is useful
    to setup some specific matching involving these elements.

    .. important::
        It is necessary to have defined a ``brho`` variable when creating your beams. If one has used
        `make_lhc_beams` to create the beams, this has already been done automatically.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        quad_numbers (Sequence[int]): quadrupoles to be varied, by number (aka position from IP).
        ip (int): the IP around which to apply the instructions.
        sides (Sequence[str]): the sides of IP to act on. Should be `R` for right and `L` for left,
            accepts these letters case-insensitively. Defaults to both sides of the IP.
        beam (int): the beam for which to apply the instructions. Defaults to 1.

    Example:
        .. code-block:: python

            >>> vary_independent_ir_quadrupoles(
            ...     madx, quad_numbers=[10, 11, 12, 13], ip=1, sides=("r", "l")
            ... )
    """
    if (
        ip not in (1, 2, 5, 8)
        or any(side.upper() not in ("R", "L") for side in sides)
        or any(quad not in (4, 5, 6, 7, 8, 9, 10, 11, 12, 13) for quad in quad_numbers)
    ):
        logger.error("Either the IP number of the side provided are invalid, not applying any error.")
        raise ValueError("Invalid 'quad_numbers', 'ip', 'sides' argument")

    logger.debug(f"Preparing a knob involving quadrupoles {quad_numbers}")
    # Each quad has a specific power circuit used for their k1 boundaries
    power_circuits: Dict[int, str] = {
        4: "mqy",
        5: "mqml",
        6: "mqml",
        7: "mqm",
        8: "mqml",
        9: "mqm",
        10: "mqml",
        11: "mqtli",
        12: "mqt",
        13: "mqt",
    }
    for quad in quad_numbers:
        circuit = power_circuits[quad]
        for side in sides:
            logger.debug(f"Sending vary command for Q{quad}{side.upper()}{ip}")
            madx.command.vary(
                name=f"kq{'t' if quad >= 11 else ''}{'l' if quad == 11 else ''}{quad}.{side}{ip}b{beam}",
                step=1e-7,
                lower=f"-{circuit}.{'b' if quad == 7 else ''}{quad}{side}{ip}.b{beam}->kmax/brho",
                upper=f"+{circuit}.{'b' if quad == 7 else ''}{quad}{side}{ip}.b{beam}->kmax/brho",
            )


def switch_magnetic_errors(madx: Madx, **kwargs) -> None:
    """
    .. versionadded:: 0.7.0

    Applies magnetic field orders. This will only work for LHC and HLLHC machines.
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        **kwargs: The setting works through keyword arguments, and several specific
            kwargs are expected. `default` sets global default to this value (defaults to `False`).
            `AB#` sets the default for all of that order, the order being the `#` number. `A#` or
            `B#` sets the default for systematic and random of this id. `A#s`, `B#r`, etc. sets the
            specific value for this given order. In all kwargs, the order # should be in the range
            [1...15], where 1 == dipolar field.

    Examples:

        Set random values for (alsmost) all of these orders:

        .. code-block:: python

            >>> random_kwargs = {}
            >>> for order in range(1, 16):
            ...     for ab in "AB":
            ...         random_kwargs[f"{ab}{order:d}"] = random.randint(0, 20)
            >>> switch_magnetic_errors(madx, **random_kwargs)

        Set a given value for ``B6`` order magnetic errors:

        .. code-block:: python

            >>> switch_magnetic_errors(madx, "B6"=1e-4)
    """
    logger.debug("Setting magnetic errors")
    global_default = kwargs.get("default", False)

    for order in range(1, 16):
        logger.debug(f"Setting up for order {order}")
        order_default = kwargs.get(f"AB{order:d}", global_default)

        for ab in "AB":
            ab_default = kwargs.get(f"{ab}{order:d}", order_default)
            for sr in "sr":
                name = f"{ab}{order:d}{sr}"
                error_value = int(kwargs.get(name, ab_default))
                logger.debug(f"Setting global for 'ON_{name}' to {error_value}")
                madx.globals[f"ON_{name}"] = error_value


# ----- Errors Assignment ----- #


def misalign_lhc_triplets(
    madx: Madx, ip: int, sides: Sequence[str] = ("r", "l"), table: str = "triplet_errors", **kwargs
) -> None:
    """
    .. versionadded:: 0.9.0

    Apply misalignment errors to IR triplet quadrupoles on a given side of a given IP. In case of a
    sliced lattice, this will misalign all slices of each magnet together. This is a convenience wrapper
    around the `~.misalign_lhc_ir_quadrupoles` function, see that function's docstring for more
    information.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ip (int): the interaction point around which to apply errors.
        sides (Sequence[str]): sides of the IP to apply error on the triplets, either L or R or both.
            Case-insensitive. Defaults to both.
        table (str): the name of the internal table that will save the assigned errors. Defaults to
            `triplet_errors`.
        **kwargs: Any keyword argument is given to the ``EALIGN`` command, including the error to apply
            (`DX`, `DY`, `DPSI` etc) as a string, like it would be given directly into ``MAD-X``.

    Examples:

        A random, gaussian truncated ``DX`` misalignment:

        .. code-block:: python

            >>> misalign_lhc_triplets(madx, ip=1, sides="RL", dx="1E-5 * TGAUSS(2.5)")

        A random, gaussian truncated ``DPSI`` misalignment:

        .. code-block:: python

            >>> misalign_lhc_triplets(madx, ip=5, sides="RL", dpsi="0.001 * TGAUSS(2.5)")
    """
    misalign_lhc_ir_quadrupoles(madx, ips=[ip], beam=None, quadrupoles=(1, 2, 3), sides=sides, table=table, **kwargs)


def misalign_lhc_ir_quadrupoles(
    madx: Madx,
    ips: Sequence[int],
    beam: int,
    quadrupoles: Sequence[int],
    sides: Sequence[str] = ("r", "l"),
    table: str = "ir_quads_errors",
    **kwargs,
) -> None:
    """
    .. versionadded:: 0.9.0

    Apply misalignment errors to IR quadrupoles on a given side of given IPs. In case of a sliced
    lattice, this will misalign all slices of each magnet together. According to the
    `Equipment Codes Main System <https://edms5.cern.ch/cedar/plsql/codes.systems>`_,  those are Q1
    to Q10 included, quads beyond are ``MQ`` or ``MQT`` which are considered arc elements.

    One can find a full example use of the function for tracking in the
    :ref:`LHC IR Errors  <demo-ir-errors>` example gallery.

    .. warning::
        This implementation is only valid for LHC IP IRs, which are 1, 2, 5 and 8. Other IRs have
        different layouts incompatible with this function.

    .. warning::
        One should avoid issuing different errors with several uses of this command as it is unclear to me
        how ``MAD-X`` chooses to handle this internally. Instead, it is advised to give all errors in the same
        command, which is guaranteed to work. See the last provided example below.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ips (Sequence[int]): the interaction point(s) around which to apply errors.
        beam (int): beam number to apply the errors to. Unlike triplet quadrupoles which are single
            aperture, Q4 to Q10 are not and will need this information.
        quadrupoles (Sequence[int]): the number of the quadrupoles to apply errors to.
        sides (Sequence[str]): sides of the IP to apply error on the triplets, either L or R or both.
            Case-insensitive. Defaults to both.
        table (str): the name of the internal table that will save the assigned errors. Defaults to
            'ir_quads_errors'.
        **kwargs: Any keyword argument is given to the ``EALIGN`` command, including the error to apply
            (`DX`, `DY`, `DPSI` etc) as a string, like it would be given directly into ``MAD-X``.

    Examples:

        For systematic ``DX`` misalignment:

        .. code-block:: python

            >>> misalign_lhc_ir_quadrupoles(
            ...     madx, ips=[1], quadrupoles=[1, 2, 3, 4, 5, 6], beam=1, sides="RL", dx="1E-5"
            ... )

        For a tilt distribution centered on 1mrad:

        .. code-block:: python

            >>> misalign_lhc_ir_quadrupoles(
            ...     madx, ips=[5],
            ...     quadrupoles=[7, 8, 9, 10],
            ...     beam=1,
            ...     sides="RL",
            ...     dpsi="1E-3 + 8E-4 * TGAUSS(2.5)",
            ... )

        For several error types on the elements, here ``DY`` and ``DPSI``:

        .. code-block:: python

            >>> misalign_lhc_ir_quadrupoles(
            ...     madx,
            ...     ips=[1, 5],
            ...     quadrupoles=list(range(1, 11)),
            ...     beam=1,
            ...     sides="RL",
            ...     dy=1e-5,  # ok too as cpymad converts this to a string first
            ...     dpsi="1E-3 + 8E-4 * TGAUSS(2.5)"
            ... )
    """
    if any(ip not in (1, 2, 5, 8) for ip in ips):
        logger.error("The IP number provided is invalid, not applying any error.")
        raise ValueError("Invalid 'ips' parameter")
    if beam and beam not in (1, 2, 3, 4):
        logger.error("The beam number provided is invalid, not applying any error.")
        raise ValueError("Invalid 'beam' parameter")
    if any(side.upper() not in ("R", "L") for side in sides):
        logger.error("The side provided is invalid, not applying any error.")
        raise ValueError("Invalid 'sides' parameter")

    sides = [side.upper() for side in sides]
    logger.debug("Clearing error flag")
    madx.select(flag="error", clear=True)

    logger.debug(f"Applying alignment errors to IR quads '{quadrupoles}', with arguments {kwargs}")
    for ip in ips:
        logger.debug(f"Applying errors for IR{ip}")
        for side in sides:
            for quad_number in quadrupoles:
                for quad_pattern in LHC_IR_QUADS_PATTERNS[quad_number]:
                    # Triplets are single aperture and don't need beam information, others do
                    if quad_number <= 3:
                        madx.select(flag="error", pattern=quad_pattern.format(side=side, ip=ip))
                    else:
                        madx.select(flag="error", pattern=quad_pattern.format(side=side, ip=ip, beam=beam))
    madx.command.ealign(**kwargs)

    table = table if table else "etable"  # guarantee etable command won't fail if someone gives `table=None`
    logger.debug(f"Saving assigned errors in internal table '{table}'")
    madx.command.etable(table=table)

    logger.debug("Clearing up error flag")
    madx.select(flag="error", clear=True)


# ----- Useful Routines ----- #


def do_kmodulation(
    madx: Madx, ir: int = 1, side: str = "right", steps: int = 100, stepsize: float = 3e-8
) -> tfs.TfsDataFrame:
    r"""
    .. versionadded:: 0.20.0

    Simulates a K-Modulation measurement by varying the powering of Q1 left or
    right of the IP, and returning the tune variations resulting from this
    modulation.

    .. note::
        At the end of the simulation, the powering of the quadrupole is reset
        to the value it had at the time of function call.

    .. tip::
        From these, one can then calculate the :math:`\beta`-functions at the Q1
        and then at the IP, plus the possible waist shift, according to
        :cite:t:`Carlier:AccuracyFeasibilityMeasurement2017`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ir (int): the IR in which to perform the modulation. Defaults to 1.
        side (str): which side of the IP to use the Q1 to perform the modulation.
            Should be either ``right`` or ``left``, case-insensitive. Defaults to
            ``right``.
        steps (int): the number of steps to perform in the modulations, aka the number
            of "measurements". Defaults to 100.
        stepsize (float): the increment in powering for Q1, in direct values of the
            powering variable used in ``MAD-X``. Defaults to 3e-8.

    Returns:
        A `~tfs.TfsDataFrame` containing the tune values at each powering step.

    Example:

        .. code-block:: python

            >>> tune_results = do_kmodulation(madx, ir=1, side="right", steps=100, stepsize=3e-8)
    """
    element = f"MQXA.1R{ir:d}" if side.lower() == "right" else f"MQXA.1L{ir:d}"
    powering_variable = f"KTQX1.R{ir:d}" if side.lower() == "right" else f"KTQX1.L{ir:d}"

    logger.debug(f"Saving current magnet powering for '{element}'")
    old_powering = madx.globals[powering_variable]
    minval = old_powering - steps / 2 * stepsize
    maxval = old_powering + steps / 2 * stepsize
    k_powerings = np.linspace(minval, maxval, steps + 1)
    results = tfs.TfsDataFrame(
        index=k_powerings,
        columns=["K", "TUNEX", "ERRTUNEX", "TUNEY", "ERRTUNEY"],
        headers={
            "TITLE": "K-Modulation",
            "ELEMENT": element,
            "VARIABLE": powering_variable,
            "STEPS": steps,
            "STEP_SIZE": stepsize,
        },
        dtype=float,
    )

    logger.debug(f"Modulating quadrupole '{element}'")
    for powering in k_powerings:
        logger.trace(f"Modulation of '{element}' - Setting '{powering_variable}' to {powering}")
        madx.globals[powering_variable] = powering
        df = get_ir_twiss(madx, ir=ir, centre=True, columns=["k1l", "l"])
        results.loc[powering].K = df.loc[element.lower()].k1l / df.loc[element.lower()].l  # Store K
        results.loc[powering].TUNEX = madx.table.summ.q1[0]  # Store Qx
        results.loc[powering].TUNEY = madx.table.summ.q2[0]  # Store Qy

    logger.debug(f"Resetting '{element}' powering")
    madx.globals[powering_variable] = old_powering

    results.index.name = powering_variable
    results.ERRTUNEX = 0  # No measurement error from MAD-X
    results.ERRTUNEY = 0  # No measurement error from MAD-X
    return results


def correct_lhc_global_coupling(
    madx: Madx, beam: int = 1, telescopic_squeeze: bool = True, calls: int = 100, tolerance: float = 1.0e-21
) -> None:
    """
    .. versionadded:: 0.20.0

    A littly tricky matching routine to perform a decent global coupling correction using
    the ``LHC`` coupling knobs.

    .. important::
        This routine makes use of some matching tricks and uses the ``SUMM`` table's
        ``dqmin`` variable for the matching. It should be considered a helpful little
        trick, but it is not a perfect solution.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        beam (int): which beam you want to perform the matching for, should be `1` or
            `2`. Defaults to `1`.
        telescopic_squeeze (bool): If set to `True`, uses the coupling knobs
            for Telescopic Squeeze configuration. Defaults to `True`.
        calls (int): max number of varying calls to perform when matching. Defaults to 100.
        tolerance (float): tolerance for successfull matching. Defaults to :math:`10^{-21}`.

    Example:
        .. code-block:: python

            >>> correct_lhc_global_coupling(madx, sequence="lhcb1", telescopic_squeeze=True)
    """
    suffix = "_sq" if telescopic_squeeze else ""
    sequence = f"lhcb{beam:d}"
    logger.debug(f"Attempting to correct global coupling through matching, on sequence '{sequence}'")

    real_knob, imag_knob = f"CMRS.b{beam:d}{suffix}", f"CMIS.b{beam:d}{suffix}"
    logger.debug(f"Matching using the coupling knobs '{real_knob}' and '{imag_knob}'")
    madx.command.match(chrom=True, sequence=sequence)
    madx.command.gweight(dqmin=1, Q1=0)
    madx.command.global_(dqmin=0, Q1=62.28)
    madx.command.vary(name=real_knob, step=1.0e-8)
    madx.command.vary(name=imag_knob, step=1.0e-8)
    madx.command.lmdif(calls=calls, tolerance=tolerance)
    madx.command.endmatch()


def correct_lhc_orbit(
    madx: Madx,
    sequence: str,
    orbit_tolerance: float = 1e-14,
    iterations: int = 3,
    mode: str = "micado",
    **kwargs,
) -> None:
    """
    .. versionadded:: 0.9.0

    Routine for orbit correction using ``MCB.*`` elements in the LHC. This uses the
    ``CORRECT`` command in ``MAD-X`` behind the scenes, refer to the
    `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_ for
    usage information.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): which sequence to use the routine on.
        orbit_tolerance (float): the tolerance for the correction. Defaults to 1e-14.
        iterations (int): the number of iterations of the correction to perform.
            Defaults to 3.
        mode (str): the method to use for the correction. Defaults to ``micado`` as in
            the `CORRECT` command.
        **kwargs: Any keyword argument that can be given to the ``MAD-X`` ``CORRECT``
            command, such as ``mode``, ``ncorr``, etc.

    Example:
        .. code-block:: python

            >>> correct_lhc_orbit(madx, sequence="lhcb1", plane="y")
    """
    logger.debug("Starting orbit correction")
    for default_kicker in ("kicker", "hkicker", "vkicker", "virtualcorrector"):
        logger.trace(f"Disabling default corrector class '{default_kicker}'")
        madx.command.usekick(sequence=sequence, status="off", class_=default_kicker)

    logger.debug("Selecting '^MCB.*' correctors")
    madx.command.usekick(sequence=sequence, status="on", pattern="^MCB.*")
    madx.command.usemonitor(sequence=sequence, status="on", class_="monitor")

    for _ in range(iterations):
        logger.trace("Doing orbit correction for Y then X plane")
        madx.twiss(chrom=True)
        madx.command.correct(sequence=sequence, plane="y", flag="ring", error=orbit_tolerance, mode=mode, **kwargs)
        madx.command.correct(sequence=sequence, plane="x", flag="ring", error=orbit_tolerance, mode=mode, **kwargs)


# ----- Elements / Markers Installation ----- #


def install_ac_dipole_as_kicker(
    madx: Madx,
    deltaqx: float,
    deltaqy: float,
    sigma_x: float,
    sigma_y: float,
    beam: int = 1,
    start_turn: int = 100,
    ramp_turns: int = 2000,
    top_turns: int = 6600,
) -> None:
    """
    .. versionadded:: 0.15.0

    Installs an AC dipole as a kicker element in (HL)LHC beam 1 or 2, for tracking. This function
    assumes that you have already defined lhcb1/lhcb2 sequence, made a beam for it (``BEAM``
    command or `~lhc.make_lhc_beams` function), matched to your desired working point and made
    a ``TWISS`` call.

    .. important::
        In a real machine, the AC Dipole does impact the orbit as well as the betatron
        functions when turned on (:cite:t:`Miyamoto:ACD:2008`, part III). In ``MAD-X``
        however, it cannot be modeled to do both at the same time. This routine introduces
        an AC Dipole as a kicker element so that its effect can be seen on particle trajectory
        in tracking. It **does not** affect ``TWISS`` functions.

    One can find a full example use of the function for tracking in the
    :ref:`AC Dipole Tracking <demo-ac-dipole-tracking>` example gallery.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        deltaqx (float): the deltaQx (horizontal tune excitation) used by the AC dipole.
        deltaqy (float): the deltaQy (vertical tune excitation) used by the AC dipole.
        sigma_x (float): the horizontal amplitude to drive the beam to, in bunch sigma.
        sigma_y (float): the vertical amplitude to drive the beam to, in bunch sigma.
        beam (int): the LHC beam to install the AC Dipole into, either 1 or 2. Defaults to 1.
        start_turn (int): the turn at which to start ramping up the AC dipole. Defaults to 100.
        ramp_turns (int): the number of turns to use for the ramp-up and the ramp-down of the AC dipole.
            This number is important in order to preserve the adiabaticity of the cycle. Defaults to 2000
            as in the LHC.
        top_turns (int): the number of turns to drive the beam for. Defaults to 6600 as in the LHC.

    Example:
        .. code-block:: python

    Example:
        .. code-block:: python

            >>> lhc.install_ac_dipole_as_kicker(
            ...     madx,
            ...     deltaqx=-0.01,  # driven horizontal tune to Qxd = 62.31 - 0.01 = 62.30
            ...     deltaqy=0.012,  # driven vertical tune to Qyd = 60.32 + 0.012 = 60.332
            ...     sigma_x=2,  # bunch amplitude kick in the horizontal plane
            ...     sigma_y=2,  # bunch amplitude kick in the vertical plane
            ...     beam=1,  # beam for which to install and kick
            ...     start_turn=100,  # when to turn on the AC Dipole
            ...     ramp_turns=2000,  # how many turns to ramp up/down the AC Dipole
            ...     top_turns=6600,  # how many turns to keep the AC Dipole at full kick
            ... )
    """
    logger.warning("This AC Dipole is implemented as a kicker and will not affect TWISS functions!")
    logger.debug("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam")

    if top_turns > 6600:
        logger.warning(
            f"Configuring the AC Dipole for {top_turns:d} of driving is fine for MAD-X but is "
            "higher than what the device can do in the (HL)LHC! Beware."
        )
    ramp1, ramp2 = start_turn, start_turn + ramp_turns
    ramp3 = ramp2 + top_turns
    ramp4 = ramp3 + ramp_turns

    logger.debug("Retrieving tunes from internal tables")
    q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
    logger.debug(f"Retrieved values are q1 = {q1:.5f}, q2 = {q2:.5f}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    logger.debug("Querying BETX and BETY at AC Dipole location")
    # All below is done as model_creator macros with `.input()` calls
    madx.input(f"pbeam = beam%lhcb{beam:d}->pc;")
    madx.input(f"betxac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, betx);")
    madx.input(f"betyac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, bety);")

    logger.debug("Calculating AC Dipole voltage values")
    madx.input(f"voltx = 0.042 * pbeam * ABS({deltaqx}) / SQRT(180.0 * betxac) * {sigma_x}")
    madx.input(f"volty = 0.042 * pbeam * ABS({deltaqy}) / SQRT(177.0 * betyac) * {sigma_y}")

    logger.debug("Defining kicker elements for transverse planes")
    madx.input(
        f"MKACH.6L4.B{beam:d}: hacdipole, l=0, freq:={q1_dipole}, lag=0, volt=voltx, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )
    madx.input(
        f"MKACV.6L4.B{beam:d}: vacdipole, l=0, freq:={q2_dipole}, lag=0, volt=volty, ramp1={ramp1}, "
        f"ramp2={ramp2}, ramp3={ramp3}, ramp4={ramp4};"
    )

    logger.debug(f"Installing AC Dipole kicker with driven tunes of Qx_D = {q1_dipole:.5f}  |  Qy_D = {q2_dipole:.5f}")
    madx.command.seqedit(sequence=f"lhcb{beam:d}")
    madx.command.flatten()
    # The kicker version is meant for a thin lattice and is installed a right at MKQA.6L4.B[12] (at=0)
    madx.command.install(element=f"MKACH.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element=f"MKACV.6L4.B{beam:d}", at=0, from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-USEd for changes to take effect. Beware that this will reset it, "
        "remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def install_ac_dipole_as_matrix(madx: Madx, deltaqx: float, deltaqy: float, beam: int = 1) -> None:
    """
    .. versionadded:: 0.15.0

    Installs an AC dipole as a matrix element in (HL)LHC beam 1 or 2, to see its effect on TWISS functions
    This function assumes that you have already defined lhcb1/lhcb2 sequence, made a beam for it (``BEAM``
    command or `~lhc.make_lhc_beams` function), matched to your desired working point and made a ``TWISS``
    call.

    This function's use is very similar to that of `~.lhc.install_ac_dipole_as_kicker`.

    .. important::
        In a real machine, the AC Dipole does impact the orbit as well as the betatron
        functions when turned on (:cite:t:`Miyamoto:ACD:2008`, part III). In ``MAD-X``
        however, it cannot be modeled to do both at the same time. This routine introduces
        an AC Dipole as a matrix element so that its effect can be seen on ``TWISS`` functions.
        It **does not** affect tracking.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        deltaqx (float): the deltaQx (horizontal tune excitation) used by the AC dipole.
        deltaqy (float): the deltaQy (vertical tune excitation) used by the AC dipole.
        beam (int): the LHC beam to install the AC Dipole into, either 1 or 2. Defaults to 1.

    Example:
        .. code-block:: python

            >>> install_ac_dipole_as_matrix(madx, deltaqx=-0.01, deltaqy=0.012, beam=1)
    """
    logger.warning("This AC Dipole is implemented as a matrix and will not affect particle tracking!")
    logger.debug("This routine should be done after 'match', 'twiss' and 'makethin' for the appropriate beam.")

    logger.debug("Retrieving tunes from internal tables")
    q1, q2 = madx.table.summ.q1[0], madx.table.summ.q2[0]
    logger.debug(f"Retrieved values are q1 = {q1:.5f}, q2 = {q2:.5f}")
    q1_dipole, q2_dipole = q1 + deltaqx, q2 + deltaqy

    logger.debug("Querying BETX and BETY at AC Dipole location")
    # All below is done as model_creator macros with `.input()` calls
    madx.input(f"betxac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, betx);")
    madx.input(f"betyac = table(twiss, MKQA.6L4.B{beam:d}, BEAM, bety);")

    logger.debug("Calculating AC Dipole matrix terms")
    madx.input(f"hacmap21 = 2 * (cos(2*pi*{q1_dipole}) - cos(2*pi*{q1})) / (betxac * sin(2*pi*{q1}));")
    madx.input(f"vacmap43 = 2 * (cos(2*pi*{q2_dipole}) - cos(2*pi*{q2})) / (betyac * sin(2*pi*{q2}));")

    logger.debug("Defining matrix elements for transverse planes")
    madx.input(f"hacmap: matrix, l=0, rm21=hacmap21;")
    madx.input(f"vacmap: matrix, l=0, rm43=vacmap43;")

    logger.debug(f"Installing AC Dipole matrix with driven tunes of Qx_D = {q1_dipole:.5f}  |  Qy_D = {q2_dipole:.5f}")
    madx.command.seqedit(sequence=f"lhcb{beam:d}")
    madx.command.flatten()
    # The matrix version is meant for a thick lattice and is installed a little after MKQA.6L4.B[12]
    madx.command.install(element="hacmap", at="1.583 / 2", from_=f"MKQA.6L4.B{beam:d}")
    madx.command.install(element="vacmap", at="1.583 / 2", from_=f"MKQA.6L4.B{beam:d}")
    madx.command.endedit()

    logger.warning(
        f"Sequence LHCB{beam:d} is now re-USEd for changes to take effect. Beware that this will reset it, "
        "remove errors etc."
    )
    madx.use(sequence=f"lhcb{beam:d}")


def add_markers_around_lhc_ip(madx: Madx, sequence: str, ip: int, n_markers: int, interval: float) -> None:
    """
    .. versionadded:: 1.0.0

    Adds some simple marker elements left and right of an IP point, to increase the granularity of optics
    functions returned from a ``TWISS`` call.

    .. warning::
        You will most likely need to have sliced the sequence before calling this function,
        as otherwise there is a risk on getting a negative drift depending on the affected
        IP. This would lead to the remote ``MAD-X`` process to crash.

    .. warning::
        After editing the *sequence* to add markers, the ``USE`` command will be run for the changes to apply.
        This means the caveats of ``USE`` apply, for instance the erasing of previously defined errors, orbits
        corrections etc.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): which sequence to use the routine on.
        ip (int): The interaction point around which to add markers.
        n_markers (int): how many markers to add on each side of the IP.
        interval (float): the distance between markers, in [m]. Giving ``interval=0.05`` will
            place a marker every 5cm (starting 5cm away from the IP on each side).

    Example:
        .. code-block:: python

            >>> add_markers_around_lhc_ip(
            ...     madx, sequence=f"lhcb1", ip=1, n_markers=1000, interval=0.001
            ... )
    """
    logger.debug(f"Adding {n_markers:d} markers on each side of IP{ip:d}")
    madx.command.seqedit(sequence=sequence)
    madx.command.flatten()
    for i in range(1, n_markers + 1):
        madx.command.install(
            element=f"MARKER.LEFT.IP{ip:d}.{i:02d}", class_="MARKER", at=-i * interval, from_=f"IP{ip:d}"
        )
        madx.command.install(
            element=f"MARKER.RIGHT.IP{ip:d}.{i:02d}", class_="MARKER", at=i * interval, from_=f"IP{ip:d}"
        )
    madx.command.flatten()
    madx.command.endedit()
    logger.warning(
        f"Sequence '{sequence}' will be USEd for new markers to be taken in consideration, beware that this will erase errors etc."
    )
    madx.use(sequence=sequence)


# ----- Output Utilities ----- #


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


# ----- Querying Utilities ----- #


def get_magnets_powering(
    madx: Madx, patterns: Sequence[str] = [r"^mb\.", r"^mq\.", r"^ms\."], brho: Union[str, float] = None, **kwargs
) -> tfs.TfsDataFrame:
    r"""
    .. versionadded:: 0.17.0

    Gets the twiss table with additional defined columns for the given *patterns*.

    .. note::
        Here are below certain useful patterns for the ``LHC`` and their meaning:

        * ``^mb\.`` :math:`\rightarrow` main bends.
        * ``^mq\.`` :math:`\rightarrow` main quadrupoles.
        * ``^ms\.`` :math:`\rightarrow` main sextupoles.
        * ``^mb[rswx]`` :math:`\rightarrow` separation dipoles.
        * ``^mq[mwxy]`` :math:`\rightarrow` insertion quads.
        * ``^mqt.1[23]`` :math:`\rightarrow` short tuning quads (12 & 13).
        * ``^mqtl`` :math:`\rightarrow` long  tuning quads.
        * ``^mcbx`` :math:`\rightarrow` crossing scheme magnets.
        * ``^mcb[cy]`` :math:`\rightarrow` crossing scheme magnets.

        To make no selection, one can give ``patterns=[""]`` and this will give back
        the results for *all* elements. One can also give a specific magnet's exact
        name to include it in the results.

    .. note::
        The ``TWISS`` flag will be fully cleared after running this function.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        patterns (Sequence[str]): a list of regex patterns to define which elements
            should be selected and included in the returned table. Defaults to selecting
            the main bends, quads and sextupoles. See the note admonition above for
            useful patterns to select specific ``LHC`` magnet families.
        brho (Union[str, float]): optional, an explicit definition for the magnetic
            rigidity in :math:`Tm^{-1}`. If not given, it will be assumed that
            a ``brho`` quantity is defined in the ``MAD-X`` globals.
        **kwargs: any keyword argument will be passed to `~.twiss.get_pattern_twiss` and
            later on to the ``TWISS`` command executed in ``MAD-X``.

    Returns:
        A `~tfs.TfsDataFrame` of the ``TWISS`` table, with the relevant newly defined columns
        and including the elements matching the regex *patterns* that were provided.

    Example:
        .. code-block:: python

            >>> sextupoles_powering = get_magnets_powering(madx, patterns=[r"^ms\."])
    """
    logger.debug("Computing magnets field and powering limits proportions")
    NEW_COLNAMES = ["name", "keyword", "ampere", "imax", "percent", "kn", "kmax", "integrated_field", "L"]
    NEW_COLNAMES = list(set(NEW_COLNAMES + kwargs.pop("columns", [])))  # in case user gives explicit columns
    _list_field_currents(madx, brho=brho)
    return twiss.get_pattern_twiss(madx, columns=NEW_COLNAMES, patterns=patterns, **kwargs)


def query_arc_correctors_powering(madx: Madx) -> Dict[str, float]:
    """
    .. versionadded:: 0.15.0

    Queries for the arc corrector strengths and returns their values as a percentage of
    their max powering. This is a port of one of the **corr_value.madx** file's macros

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object with an
            active (HL)LHC sequence.

    Returns:
        A `dict` with the percentage for each corrector.

    Example:
        .. code-block:: python

            >>> arc_knobs = query_arc_correctors_powering(madx)
    """
    logger.debug("Querying triplets correctors powering")
    result: Dict[str, float] = {}

    logger.debug("Querying arc tune trim quadrupole correctors (MQTs) powering")
    k_mqt_max = 120 / madx.globals.brho  # 120 T/m
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqt_max for knob in LHC_KQTF_KNOBS})

    logger.debug("Querying arc short straight sections skew quadrupole correctors (MQSs) powering")
    k_mqs_max = 120 / madx.globals.brho  # 120 T/m
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqs_max for knob in LHC_KQS_KNOBS})

    logger.debug("Querying arc sextupole correctors (MSs) powering")
    k_ms_max = 1.280 * 2 / 0.017 ** 2 / madx.globals.brho  # 1.28 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_ms_max for knob in LHC_KSF_KNOBS})

    logger.debug("Querying arc skew sextupole correctors (MSSs) powering")
    k_mss_max = 1.280 * 2 / 0.017 ** 2 / madx.globals.brho  # 1.28 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mss_max for knob in LHC_KSS_KNOBS})

    logger.debug("Querying arc spool piece (skew) sextupole correctors (MCSs) powering")
    k_mcs_max = 0.471 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.471 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcs_max for knob in LHC_KCS_KNOBS})

    logger.debug("Querying arc spool piece (skew) octupole correctors (MCOs) powering")
    k_mco_max = 0.040 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.04 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mco_max for knob in LHC_KCO_KNOBS})

    logger.debug("Querying arc spool piece (skew) decapole correctors (MCDs) powering")
    k_mcd_max = 0.100 * 24 / 0.017 ** 4 / madx.globals.brho  # 0.1 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcd_max for knob in LHC_KCD_KNOBS})

    logger.debug("Querying arc short straight sections octupole correctors (MOs) powering")
    k_mo_max = 0.29 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.29 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mo_max for knob in LHC_KO_KNOBS})
    return result


def query_triplet_correctors_powering(madx: Madx) -> Dict[str, float]:
    """
    .. versionadded:: 0.15.0

    Queries for the triplet corrector strengths and returns their values as a percentage of
    their max powering. This is a port of one of the **corr_value.madx** file's macros.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object with an
            active (HL)LHC sequence.

    Returns:
        A `dict` with the percentage for each corrector.

    Example:
        .. code-block:: python

            >>> triplet_knobs = query_triplet_correctors_powering(madx)
    """
    logger.debug("Querying triplets correctors powering")
    result: Dict[str, float] = {}

    logger.debug("Querying triplet skew quadrupole correctors (MQSXs) powering")
    k_mqsx_max = 1.360 / 0.017 / madx.globals.brho  # 1.36 T @ 17mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mqsx_max for knob in LHC_KQSX_KNOBS})

    logger.debug("Querying triplet sextupole correctors (MCSXs) powering")
    k_mcsx_max = 0.028 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.028 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcsx_max for knob in LHC_KCSX_KNOBS})

    logger.debug("Querying triplet skew sextupole correctors (MCSSXs) powering")
    k_mcssx_max = 0.11 * 2 / 0.017 ** 2 / madx.globals.brho  # 0.11 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcssx_max for knob in LHC_KCSSX_KNOBS})

    logger.debug("Querying triplet octupole correctors (MCOXs) powering")
    k_mcox_max = 0.045 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.045 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcox_max for knob in LHC_KCOX_KNOBS})

    logger.debug("Querying triplet skew octupole correctors (MCOSXs) powering")
    k_mcosx_max = 0.048 * 6 / 0.017 ** 3 / madx.globals.brho  # 0.048 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mcosx_max for knob in LHC_KCOSX_KNOBS})

    logger.debug("Querying triplet decapole correctors (MCTXs) powering")
    k_mctx_max = 0.01 * 120 / 0.017 ** 5 / madx.globals.brho  # 0.010 T @ 17 mm
    result.update({knob: 100 * _knob_value(madx, knob) / k_mctx_max for knob in LHC_KCTX_KNOBS})
    return result


def get_current_orbit_setup(madx: Madx) -> Dict[str, float]:
    """
    .. versionadded:: 0.8.0

    Get the current values for the (HL)LHC orbit variables. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A `dict` of all orbit variables set, and their values as set in the ``MAD-X`` globals.

    Example:
        .. code-block:: python

            >>> orbit_setup = get_current_orbit_setup(madx)
    """
    logger.debug("Extracting orbit variables from global table")
    variables, specials = lhc_orbit_variables()
    return {orbit_variable: madx.globals[orbit_variable] for orbit_variable in variables + list(specials.keys())}


# ----- Miscellaneous Utilities ----- #


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


def get_lhc_bpms_twiss_and_rdts(madx: Madx) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.19.0

    Runs a ``TWISS`` on the currently active sequence for all ``LHC`` BPMs. The coupling RDTs
    are also computed through a CMatrix approach via  `optics_functions.coupling.coupling_via_cmatrix`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A `~tfs.frame.TfsDataFrame` of the ``TWISS`` table with basic default columns, as well as one
        new column for each of the coupling RDTs. The coupling RDTs are returned as complex numbers.

    Example:
        .. code-block:: python

            >>> twiss_with_rdts = get_lhc_bpms_twiss_and_rdts(madx)
    """
    twiss_tfs = twiss.get_pattern_twiss(  # need chromatic flag as we're dealing with coupling
        madx, patterns=["^BPM.*B[12]$"], columns=MONITOR_TWISS_COLUMNS, chrom=True
    )
    twiss_tfs.columns = twiss_tfs.columns.str.upper()  # optics_functions needs capitalized names
    twiss_tfs.NAME = twiss_tfs.NAME.str.upper()
    twiss_tfs[["F1001", "F1010"]] = coupling_via_cmatrix(twiss_tfs, output=["rdts"])
    return twiss_tfs


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

    twiss_tfs = twiss.get_twiss_tfs(madx, chrom=True, ripken=True)
    twiss_tfs = _add_beam_size_to_df(twiss_tfs, geom_emit_x, geom_emit_y)
    return twiss_tfs.loc[f"IP{ip:d}"].SIZE_X, twiss_tfs.loc[f"IP{ip:d}"].SIZE_Y


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


# ----- Helpers ----- #


def _all_lhc_arcs(beam: int) -> List[str]:
    """
    Generates and returns the names of all LHC arcs for a given beam.
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Args:
        beam (int): beam to get names for.

    Returns:
        The list of names.
    """
    return [f"A{i+1}{(i+1)%8+1}B{beam:d}" for i in range(8)]


def _list_field_currents(madx: Madx, brho: Union[str, float] = None) -> None:
    """
    Creates additional columns for the ``TWISS`` table with the magnets' total fields
    and currents, to help later on determine which proportion of their maximum powering
    the current setting is using. This is an implementation of the old utility script
    located at **/afs/cern.ch/eng/lhc/optics/V6.503/toolkit/list_fields_currents.madx**.

    .. important::
        Certain quantities are assumed to be defined in the ``MAD-X`` globals, such as
        ``brho``, or available in the magnets definition, such as ``calib``. For this
        reason, this script most likely only works for the ``(HL)LHC`` sequences where
        those are defined.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        brho (Union[str, float]): optional, an explicit definition for the magnetic
            rigidity in :math:`Tm^{-1}`. If not given, it will be assumed that
            a ``brho`` quantity is defined in the ``MAD-X`` globals and this one will
            be used.
    """
    logger.debug("Creating additional TWISS table columns for magnets' fields and currents")

    if brho is not None:
        logger.trace(f"Setting 'brho' to explicitely defined '{brho}'")
        madx.globals["brho"] = brho

    # Define strength := table(twiss, k0l) + ... + table(twiss, k5sl) +  table(twiss, hkick)  +  table(twiss, vkick);
    madx.globals["strength"] = (
        " + ".join(f"table(twiss, {a.lower()})" for a in _get_k_strings(stop=6))
        + " +  table(twiss, hkick)  +  table(twiss, vkick)"
    )

    # All here are given as strings to make it deferred expressions in MAD-X
    madx.globals["epsilon"] = 1e-20  # to avoid divisions by zero
    madx.globals["length"] = "table(twiss, l) + table(twiss, lrad) + epsilon"
    madx.globals["kmaxx"] = "table(twiss, kmax) + epsilon"
    madx.globals["calibration"] = "table(twiss, calib) + epsilon"
    madx.globals["kn"] = "abs(strength) / length"
    # madx.globals["rho"] = "kn / (kn + epsilon) / (kn + epsilon)"

    madx.globals["field"] = "kn * brho"
    madx.globals["percent"] = "field * 100 / (kmaxx + epsilon)"
    madx.globals["ampere"] = "field / calibration"
    madx.globals["imax"] = "kmaxx / calibration"
    madx.globals["integrated_field"] = "field * length"


def _knob_value(madx: Madx, knob: str) -> float:
    """
    Queryies the current value of a given *knob* name in the ``MAD-X`` process, and defaults
    to 0 (as ``MAD-X`` does) in case that knob has not been defined in the current process.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        knob (str): the name the knob.

    Returns:
        The knob value if it was defined, otherwise 0.

    Example:
        .. code-block:: python

            >>> _knob_value(madx, knob="underfined_for_sure")
            0
    """
    try:
        return madx.globals[knob]
    except KeyError:  # cpymad gives a 'Variable not defined: var_name'
        return 0


def _fullpath(filepath: Path) -> str:
    """
    .. versionadded:: 1.0.0

    Returns the full string path to the provided *filepath*.
    """
    return str(filepath.absolute())
