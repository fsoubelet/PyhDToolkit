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
from typing import Dict, List, Tuple

import cpymad
import matplotlib
import pandas

from cpymad.madx import Madx
from loguru import logger
from matplotlib import pyplot as plt

from pyhdtoolkit import __version__
from pyhdtoolkit.cpymadtools import errors, lhc, twiss
from pyhdtoolkit.optics.ripken import _add_beam_size_to_df

# ----- Constants ----- #

CPUS = cpu_count()
HOME = str(Path.home())

# Determine if running on afs or laptop / desktop
RUN_LOCATION = (
    "afs" if "cern.ch" in HOME or "fesoubel" in HOME else ("local" if "Users" in HOME or "/home" in HOME else None)
)

PATHS = {
    "optics2018": Path("/afs/cern.ch/eng/lhc/optics/runII/2018"),
    "local": Path.home() / "cernbox" / "OMC" / "MADX_scripts" / "Local_Coupling",
    "htc_outputdir": Path("Outputdata"),
}


# ----- Path and Runtime Utilities ----- #


def fullpath(filepath: Path) -> str:
    """Returns the full string path to the provided *filepath*, which is necessary for ``AFS`` paths."""
    return str(filepath.absolute())


def get_opticsfiles_paths() -> List[Path]:
    """
    Returns `pathlib.Path` objects to the **opticsfiles** from the appropriate location,
    depending on where the program is running, either on ``AFS`` or locally.

    .. note::
        Only the "normal" configuration **opticsfiles** are returned, so those ending with
        a special suffix such as **_ctpps1** are ignored.

    Returns:
        A `list` of `~pathlib.Path` objects to the opticsfiles.

    Raises:
        ValueError: If the program is running in an unknown location (neither `afs` nor `local`).
    """
    if RUN_LOCATION not in ("afs", "local"):
        logger.error("Unknown runtime location, exiting")
        raise ValueError("The 'RUN_LOCATION' variable should be either 'afs' or 'local'.")

    optics_dir: Path = PATHS["optics2018"] / "PROTON" if RUN_LOCATION == "afs" else PATHS["local"] / "optics"
    optics_files = list(optics_dir.iterdir())
    desired_files = [path for path in optics_files if len(path.suffix) <= 3 and path.name.startswith("opticsfile")]
    return sorted(desired_files, key=lambda x: float(x.suffix[1:]))  # sort by the number after 'opticsfile.'


def log_runtime_versions() -> None:
    """Issues a ``CRITICAL``-level log stating the runtime versions of both `~pyhdtoolkit`, `cpymad` and ``MAD-X``."""
    with Madx(stdout=False) as mad:
        logger.critical(f"Using: pyhdtoolkit {__version__} | cpymad {cpymad.__version__}  | {mad.version}")


# ----- MAD-X Setup Utilities ----- #


def call_lhc_sequence_and_optics(madx: Madx, opticsfile: str = "opticsfile.22") -> None:
    """
    Issues a ``CALL`` to the ``LHC`` sequence and the desired opticsfile, from the appropriate
    location (either on ``AFS`` or locally), based on the runtime location of the code.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        opticsfile (str): name of the optics file to call. Defaults to **opticsfile.22**, which
            holds ``LHC`` collisions optics configuration (`beta*_IP1/2/5/8=  0.300/10.000/0.300/3.000 ;
            ! Telescopic squeeze (with Q6@300A)`).

    Raises:
        ValueError: If the program is running in an unknown location  (neither `afs` nor `local`), and the
            files cannot be found in the expected directories.
    """
    logger.debug("Calling optics")
    if RUN_LOCATION == "afs":
        madx.call(fullpath(PATHS["optics2018"] / "lhc_as-built.seq"))
        madx.call(fullpath(PATHS["optics2018"] / "PROTON" / opticsfile))
    elif RUN_LOCATION == "local":
        madx.call(fullpath(PATHS["local"] / "sequences" / "lhc_as-built.seq"))
        madx.call(fullpath(PATHS["local"] / "optics" / opticsfile))
    else:
        logger.error("Unknown runtime location, exiting")
        raise ValueError("The 'RUN_LOCATION' variable should be either 'afs' or 'local'.")


def prepare_lhc_setup(opticsfile: str = "opticsfile.22", stdout: bool = False, stderr: bool = False, **kwargs) -> Madx:
    """
    Returns a prepared default ``LHC`` setup for the given *opticsfile*. Both beams are made with a default Run III
    configuration, and the ``lhcb1`` sequence is re-cycled from ``MSIA.EXIT.B1`` as in the ``OMC`` model_creator, and
    then ``USE``-d. Specific variable settings can be given as keyword arguments.

    .. important::
        Matching is **not** performed by this function and should be taken care of by the user, but the working point
        should be set by the definitions in the *opticsfile*. Beware that passing specific variables as keyword arguments
        might change that working point.

    Args:
        opticsfile (str): name of the optics file to be used. Defaults to **opticsfile.22**.
        **kwargs: any keyword argument pair will be used to update the ``MAD-X`` globals.

    Returns:
        An instanciated `~cpymad.madx.Madx` object with the required configuration.
    """
    madx = Madx(stdout=stdout, stderr=stderr)
    madx.option(echo=False, warn=False)
    call_lhc_sequence_and_optics(madx, opticsfile)
    lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
    lhc.make_lhc_beams(madx, energy=7000, emittance=3.75e-6)
    madx.command.use(sequence="lhcb1")
    madx.globals.update(kwargs)
    return madx


def prepare_lhc_run3(opticsfile: str, beam: int = 1, slicefactor: int = None, **kwargs) -> Madx:
    """
    Returns a prepared default ``LHC`` setup for the given *opticsfile*, for a Run 3 setup. Both beams
    are made with a default Run 3 configuration, and the provided sequence is re-cycled from ``MSIA.EXIT.[B12]``
    as in the ``OMC`` model_creator, then ``USE``-d. Specific variable settings can be given as keyword arguments.

    .. important::
        As this is a Run 3 setup, it is assumed that the ``acc-models-lhc`` repo is available in the root space.

    .. note::
        Matching is **not** performed by this function and should be taken care of by the user, but the working point
        should be set by the definitions in the *opticsfile*. Beware that passing specific variables as keyword arguments
        might change that working point.

    Args:
        opticsfile (str): name of the optics file to be used. Can be the string path to the file or only the opticsfile
            name itself, which would be looked for at the **acc-models-lhc/operation/optics/** path.
        beam (int): which beam to set up for. Defaults to beam 1.
        slicefactor (int): if provided, the sequence will be sliced and made thin. Defaults to `None`,
            which leads to an unsliced sequence.

    Returns:
        An instanciated `~cpymad.madx.Madx` object with the required configuration.
    """
    logger.debug("Creating Run 3 setup MAD-X instance")
    madx = Madx(**kwargs)
    madx.option(echo=False, warn=False)
    logger.debug("Calling sequence")
    madx.call("acc-models-lhc/lhc.seq")
    lhc.make_lhc_beams(madx, energy=6800)

    if slicefactor:
        logger.debug("A slicefactor was provided, slicing the sequence")
        lhc.make_lhc_thin(madx, sequence=f"lhcb{beam:d}", slicefactor=slicefactor)
        lhc.make_lhc_beams(madx, energy=6800)

    lhc.re_cycle_sequence(madx, sequence=f"lhcb{beam:d}", start=f"MSIA.EXIT.B{beam:d}")
    logger.debug("Calling optics file from the 'operation/optics' folder")

    if Path(opticsfile).is_file():
        madx.call(opticsfile)
    else:
        madx.call(f"acc-models-lhc/operation/optics/{Path(opticsfile).with_suffix('.madx')}")
    lhc.make_lhc_beams(madx, energy=6800)
    madx.command.use(sequence=f"lhcb{beam:d}")
    return madx


def add_markers_around_lhc_ip(madx: Madx, sequence: str, ip: int, n_markers: int, interval: float) -> None:
    """
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


def apply_colin_corrs_balance(madx: Madx) -> None:
    """
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


def get_size_at_ip(madx: Madx, ip: int, geom_emit: float = None) -> Tuple[float, float]:
    """
    Get the Lebedev beam sides at the provided *IP*.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ip (int): the IP to get the sizes at.
        geom_emit (float): the geometrical emittance to use for the calculation.
            If not provided, will look for the value of the ``geometric_emit``
            variable in ``MAD-X`` itself.

    Returns:
        A tuple of the horizontal and vertical beam sizes at the provided *IP*.

    Example:
        .. code-block:: python

            >>> ip5_x, ip5_y = get_size_at_ip(madx, ip=5)
    """
    logger.debug("Getting ")
    twiss_tfs = twiss.get_twiss_tfs(madx, chrom=True, ripken=True)
    twiss_tfs = _add_beam_size_to_df(twiss_tfs, madx.globals["geometric_emit"])
    return twiss_tfs.loc[f"IP{ip:d}"].SIZE_X, twiss_tfs.loc[f"IP{ip:d}"].SIZE_Y


# ----- Here for now for testing ----- #


def get_lhc_ips_positions(dataframe: pandas.DataFrame) -> Dict[str, float]:
    """
    Returns a `dict` of LHC IP and their positions from the provided *dataframe*.

    .. important::
        This function expects the IP names to be in the dataframe's index,
        and cased as the longitudinal coordinate column: aka uppercase names
        (``IP1``, ``IP2``, etc) and ``S`` column; or lowercase names
        (``ip1``, ip2``, etc) and ``s`` column.

    Args:
        dataframe (pandas.DataFrame): a `~pandas.DataFrame` containing IP positions.

    Returns:
        A `dict` with IP names as keys and their longitudinal locations as values.
    """
    logger.debug("Extracting IP positions from dataframe")
    try:
        ip_names = [f"IP{i:d}" for i in range(1, 9)]
        ip_pos = dataframe.loc[ip_names, "S"].to_numpy()
    except KeyError:
        logger.trace("Attempting to extract with lowercase names")
        ip_names = [f"ip{i:d}" for i in range(1, 9)]
        ip_pos = dataframe.loc[ip_names, "s"].to_numpy()
    ip_names = [name.upper() for name in ip_names]  # make sure to uppercase now
    return dict(zip(ip_names, ip_pos))


def draw_ip_locations(
    axis: matplotlib.axes.Axes = None,
    ip_positions: Dict[str, float] = None,
    lines: bool = True,
    location: str = "outside",
) -> None:
    """
    Plots the interaction points' locations into the background of the provided *axis*.

    Args:
        axis:  `~matplotlib.axes.Axes` to put the labels on. Defaults to `plt.gca()`.
        ip_positions (dict): a `dict` containing IP names as keys and their longitudinal positions
            as values, as returned by `~.get_lhc_ips_positions`.
        lines (bool): whether to also draw vertical lines at the IP positions. Defaults to `True`.
        location: where to show the IP names on the provided *axis*, either ``inside`` (will draw text
            at the bottom of the axis) or ``outside`` (will draw text on top of the axis). If `None` is
            given, then no labels are drawn. Defaults to ``outside``.
    """
    if axis is None:
        axis = plt.gca()

    xlimits = axis.get_xlim()
    ylimits = axis.get_ylim()

    # Draw for each IP
    for ip_name, ip_xpos in ip_positions.items():
        if xlimits[0] <= ip_xpos <= xlimits[1]:  # only plot if within plot's xlimits
            if lines:
                logger.trace(f"Drawing dashed axvline at location of {ip_name}")
                axis.axvline(ip_xpos, linestyle=":", color="grey", marker="", zorder=0)

            if location is not None and isinstance(location, str):
                inside: bool = location.lower() == "inside"
                logger.trace(f"Drawing name indicator for {ip_name}")
                # drawing ypos is lower end of ylimits if drawing inside, higher end if drawing outside
                ypos = ylimits[not inside] + (ylimits[1] + ylimits[0]) * 0.01
                c = "grey" if inside else matplotlib.rcParams["text.color"]  # match axis ticks color
                fontsize = plt.rcParams["xtick.labelsize"]  # match the xticks size
                axis.text(ip_xpos, ypos, ip_name, color=c, ha="center", va="bottom", size=fontsize)

        else:
            logger.trace(f"Skipping {ip_name} as its position is outside of the plot's xlimits")

    axis.set_xlim(xlimits)
    axis.set_ylim(ylimits)
