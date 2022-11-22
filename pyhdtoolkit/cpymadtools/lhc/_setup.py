"""
.. _lhc-setup:

**Setup Utilities**

The functions below are setup utilities for the ``LHC``, to easily get simulations ready.
"""
from pathlib import Path
from typing import Dict, List, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.constants import LHC_CROSSING_SCHEMES

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

            >>> re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
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


# ----- Helpers ----- #


def _fullpath(filepath: Path) -> str:
    """
    .. versionadded:: 1.0.0

    Returns the full string path to the provided *filepath*.
    """
    return str(filepath.absolute())
