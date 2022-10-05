"""
.. _cpymadtools-setup:

MAD-X Setup Utilities
---------------------

Module with a few convenient functions and context managers to easily set up machine in ``MAD-X``.
So far functionality is implemented for either Run 2 or Run 3 type simulations of the LHC.
"""
from pathlib import Path

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools import lhc


def prepare_lhc_run2(opticsfile: str, beam: int = 1, energy: float = 6500, slicefactor: int = None, **kwargs) -> Madx:
    """
    .. versionadded:: 1.0.0

    Returns a prepared default ``LHC`` setup for the given *opticsfile*, for a Run 2 setup. Both beams are made with a default Run III
    configuration, and the ``lhcb1`` sequence is re-cycled from ``MSIA.EXIT.B1`` as in the ``OMC`` model_creator, and
    then ``USE``-d. Specific variable settings can be given as keyword arguments.

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

    def _run2_sequence_from_opticsfile(opticsfile: Path) -> Path:
        return opticsfile.parent.parent / "lhc_as-built.seq"

    logger.debug("Creating Run 3 setup MAD-X instance")
    echo, warn = kwargs.pop("echo", False), kwargs.pop("warn", False)

    madx = Madx(**kwargs)
    madx.option(echo=echo, warn=warn)
    logger.debug("Calling sequence")
    madx.call(_fullpath(_run2_sequence_from_opticsfile(Path(opticsfile))))
    lhc.make_lhc_beams(madx, energy=energy)

    if slicefactor:
        logger.debug("A slicefactor was provided, slicing the sequence")
        lhc.make_lhc_thin(madx, sequence=f"lhcb{beam:d}", slicefactor=slicefactor)
        lhc.make_lhc_beams(madx, energy=energy)

    lhc.re_cycle_sequence(madx, sequence=f"lhcb{beam:d}", start=f"MSIA.EXIT.B{beam:d}")

    logger.debug("Calling optics file from the 'operation/optics' folder")
    madx.call(opticsfile)

    lhc.make_lhc_beams(madx, energy=energy)
    madx.command.use(sequence=f"lhcb{beam:d}")
    return madx


def prepare_lhc_run3(opticsfile: str, beam: int = 1, energy: float = 6800, slicefactor: int = None, **kwargs) -> Madx:
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
    logger.debug("Creating Run 3 setup MAD-X instance")
    echo, warn = kwargs.pop("echo", False), kwargs.pop("warn", False)

    madx = Madx(**kwargs)
    madx.option(echo=echo, warn=warn)
    logger.debug("Calling sequence")
    madx.call("acc-models-lhc/lhc.seq")
    lhc.make_lhc_beams(madx, energy=energy)

    if slicefactor:
        logger.debug("A slicefactor was provided, slicing the sequence")
        lhc.make_lhc_thin(madx, sequence=f"lhcb{beam:d}", slicefactor=slicefactor)
        lhc.make_lhc_beams(madx, energy=energy)

    lhc.re_cycle_sequence(madx, sequence=f"lhcb{beam:d}", start=f"MSIA.EXIT.B{beam:d}")

    logger.debug("Calling optics file from the 'operation/optics' folder")
    if Path(opticsfile).is_file():
        madx.call(opticsfile)
    else:
        madx.call(f"acc-models-lhc/operation/optics/{Path(opticsfile).with_suffix('.madx')}")

    lhc.make_lhc_beams(madx, energy=energy)
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

    Args:
        run (int): which run to set up for, should be 2 or 3. Defaults to run 3.
        opticsfile (str): name of the opticsfile to be used. For a Run 2 setup, should be the string path to the file.
            For a Run 3 setup, can be the string path to the file or only the opticsfile name itself, which would be
            looked for at the **acc-models-lhc/operation/optics/** path. Defaults to `None`, which will raise an error.
        beam (int): which beam to set up for. Defaults to beam 1.
        energy (float): beam energy to set up for, in GeV. Defaults to `None`, and is handled by either `~prepare_lhc_run2`
            or `~prepare_lhc_run3`. This means the default actually depends on the value of the **run** argument.
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
        energy: float = 6800,
        slicefactor: int = None,
        **kwargs,
    ):
        assert opticsfile is not None, "An opticsfile must be provided"
        if int(run) not in (2, 3):
            raise NotImplementedError("This setup is only possible for Run 2 and Run 3 configurations.")
        elif run == 2:
            self.madx = prepare_lhc_run2(
                opticsfile=opticsfile, beam=beam, energy=energy, slicefactor=slicefactor, **kwargs
            )
        else:
            self.madx = prepare_lhc_run3(
                opticsfile=opticsfile, beam=beam, energy=energy, slicefactor=slicefactor, **kwargs
            )

    def __enter__(self):
        return self.madx

    def __exit__(self, *exc_info):
        self.madx.quit()


# ----- Helpers ----- #


def _fullpath(filepath: Path) -> str:
    """
    .. versionadded:: 1.0.0

    Returns the full string path to the provided *filepath*.
    """
    return str(filepath.absolute())
