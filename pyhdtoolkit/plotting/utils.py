"""
.. _plotting-utils:

Plotting Utility Functions
--------------------------

Module with functions to used throught the different `~pyhdtoolkit.plotting` modules.
"""
from typing import Dict, Tuple

import matplotlib
import matplotlib.axes
import matplotlib.pyplot as plt
import pandas as pd
import tfs

from cpymad.madx import Madx
from loguru import logger

# ------ General Utilities ----- #


def maybe_get_ax(**kwargs):
    """
    .. versionadded:: 1.0.0

    Convenience function to get the axis, regardless of whether or not it is provided
    to the plotting function itself. It used to be that the first argument of plotting
    functions in this package had to be the 'axis' object, but that's no longer the case.

    Args:
        *args: the arguments passed to the plotting function.
        **kwargs: the keyword arguments passed to the plotting function.

    Returns:
        The `~matplotlib.axes.Axes` object to plot on, the args and the kwargs (without the
        'ax' argument if it initially was present). If no axis was provided, then it will be
        created with a call to `~matplotlib.pyplot.gca`.

    Examples:
        This is to be called at the beginning of your plotting functions:

        .. code-block:: python

            >>> def my_plotting_function(*args, **kwargs):
            ...     ax, kwargs = maybe_get_ax(**kwargs)
            ...     # do stuff with ax
            ...     ax.plot(*args, **kwargs)
            ... )
    """
    logger.debug("Looking for axis object to plot on")
    if "ax" in kwargs:
        logger.debug("Using the provided kwargs 'ax' as the axis to plot one")
        ax = kwargs.pop("ax")
    elif "axis" in kwargs:
        logger.debug("Using the provided kwargs 'axis' as the axis to plot on")
        ax = kwargs.pop("axis")
    else:
        logger.debug("No axis provided, using `plt.gca()`")
        ax = plt.gca()
    return ax, dict(kwargs)


def find_ip_s_from_segment_start(segment_df: tfs.TfsDataFrame, model_df: tfs.TfsDataFrame, ip: int) -> float:
    """
    .. versionadded:: 0.19.0

    Finds the S-offset of the IP from the start of segment by comparing the S-values for the elements in the model.

    Args:
        segment_df (tfs.TfsDataFrame): A `~tfs.TfsDataFrame` of the segment-by-segment result for the given segment.
        model_df (tfs.TfsDataFrame): The `~tfs.TfsDataframe` of the model's TWISS, usually **twiss_elements.dat**.
        ip (int): The ``LHC`` IP number.

    Returns:
        The S-offset of the IP from the BPM at the start of segment.

    Example:
        .. code-block:: python

            >>> ip_offset_in_segment = find_ip_s_from_segment_start(
            ...     segment_df=sbsphaseext_IP1, model_df=twiss_elements, ip=1
            ... )
    """
    logger.debug(f"Determining location of IP{ip:d} from the start of segment.")
    first_element: str = segment_df.NAME.to_numpy()[0]
    first_element_s_in_model = model_df[model_df.NAME == first_element].S.to_numpy()[0]
    ip_s_in_model = model_df[model_df.NAME == f"IP{ip:d}"].S.to_numpy()[0]

    # Handle case where IP segment is cut and by end of sequence and the IP is at beginning of machine
    if ip_s_in_model < first_element_s_in_model:
        # Distance to end of sequence + distance from start to IP s
        logger.debug("IP{ip:d} segment seems cut off by end of sequence, looping around to determine IP location")
        distance = (model_df.S.to_numpy().max() - first_element_s_in_model) + ip_s_in_model
    else:  # just the difference
        distance = ip_s_in_model - first_element_s_in_model
    return distance


def get_lhc_ips_positions(dataframe: pd.DataFrame) -> Dict[str, float]:
    """
    .. versionadded:: 1.0.0

    Returns a `dict` of LHC IPs and their positions from the provided *dataframe*.

    .. important::
        This function expects the IP names to be in the dataframe's index,
        and cased as the longitudinal coordinate column: aka uppercase names
        (``IP1``, ``IP2``, etc) and ``S`` column; or lowercase names
        (``ip1``, ``ip2``, etc) and ``s`` column.

    Args:
        dataframe (pandas.DataFrame): a `~pandas.DataFrame` containing at least
            IP positions. A typical example is a ``TWISS`` call output.

    Returns:
        A `dict` with IP names as keys and their longitudinal locations as values.

    Example:
        .. code-block:: python

            >>> twiss_df = tfs.read("twiss_output.tfs", index="NAME")
            >>> ips = get_lhc_ips_positions(twiss_df)
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


def make_elements_groups(
    madx: Madx, xoffset: float = 0, xlimits: Tuple[float, float] = None
) -> Dict[str, pd.DataFrame]:
    """
    .. versionadded:: 1.0.0

    Provided with an active `cpymad` instance after having ran a script, will returns different portions of
    the twiss table's dataframe for different magnetic elements.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        xoffset (float): An offset applied to the S coordinate before plotting. This is useful is you want
            to center a plot around a specific point or element, which would then become located at s = 0.
        xlimits (Tuple[float, float]): will only consider elements within xlim (for the s coordinate) if this
            is not None, using the tuple passed.

    Returns:
        A `dict` containing a `pd.DataFrame` for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.

    Example:
        .. code-block:: python

            >>> element_dfs = make_elements_groups(madx)
    """
    twiss_df = _get_twiss_table_with_offsets_and_limits(madx, xoffset, xlimits)

    logger.debug("Getting different element groups dframes from MAD-X twiss table")
    # Elements are detected by their keyword being either 'multipole' or their specific element type,
    # and having a non-zero component (knl / knsl) in their given order (or 'angle' for dipoles)
    return {
        "dipoles": twiss_df[twiss_df.keyword.isin(["multipole", "rbend", "sbend"])].query(
            "k0l != 0 or k0sl != 0 or angle != 0"
        ),
        "quadrupoles": twiss_df[twiss_df.keyword.isin(["multipole", "quadrupole"])].query("k1l != 0 or k1sl != 0"),
        "sextupoles": twiss_df[twiss_df.keyword.isin(["multipole", "sextupole"])].query("k2l != 0 or k2sl " "!= 0"),
        "octupoles": twiss_df[twiss_df.keyword.isin(["multipole", "octupole"])].query("k3l != 0 or k3sl != " "0"),
        "bpms": twiss_df[(twiss_df.keyword.isin(["monitor"])) & (twiss_df.name.str.contains("BPM", case=False))],
    }


def make_survey_groups(madx: Madx) -> Dict[str, pd.DataFrame]:
    """
    .. versionadded:: 1.0.0

    Provided with an active `cpymad` instance after having ran a script, will returns different portions of
    the survey table's dataframe for different magnetic elements.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A `dict` containing a `pd.DataFrame` for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.

    Example:
        .. code-block:: python

            >>> survey_dfs = make_survey_groups(madx)
    """
    element_dfs = make_elements_groups(madx)
    quadrupoles_focusing_df = element_dfs["quadrupoles"].query("k1l > 0")
    quadrupoles_defocusing_df = element_dfs["quadrupoles"].query("k1l < 0")

    logger.debug("Getting different element groups dframes from MAD-X survey")
    madx.command.survey()

    survey_df = madx.table.survey.dframe().copy()
    return {
        "dipoles": survey_df[survey_df.index.isin(element_dfs["dipoles"].index.tolist())],
        "quad_foc": survey_df[survey_df.index.isin(quadrupoles_focusing_df.index.tolist())],
        "quad_defoc": survey_df[survey_df.index.isin(quadrupoles_defocusing_df.index.tolist())],
        "sextupoles": survey_df[survey_df.index.isin(element_dfs["sextupoles"].index.tolist())],
        "octupoles": survey_df[survey_df.index.isin(element_dfs["octupoles"].index.tolist())],
    }


# ----- Plotting Utilities -----#


def draw_ip_locations(
    ip_positions: Dict[str, float] = None,
    lines: bool = True,
    location: str = "outside",
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.0.0

    Plots the interaction points' locations into the background of your `~matplotlib.axes.Axes`.

    Args:
        ip_positions (dict): a `dict` containing IP names as keys and their longitudinal positions
            as values, as returned by `~.get_lhc_ips_positions`.
        lines (bool): whether to also draw vertical lines at the IP positions. Defaults to `True`.
        location: where to show the IP names on the provided *axis*, either ``inside`` (will draw text
            at the bottom of the axis) or ``outside`` (will draw text on top of the axis). If `None` is
            given, then no labels are drawn. Defaults to ``outside``.
        **kwargs: If either `ax` or `axis` is found in the kwargs, the corresponding value is used as
            the axis object to plot on.

    Example:
        .. code-block:: python

            >>> twiss_df = tfs.read("twiss_output.tfs", index="NAME")
            >>> twiss_df.plot(x="S", y=["BETX", "BETY"])
            >>> ips = get_lhc_ips_positions(twiss_df)
            >>> draw_ip_locations(ip_positions=ips)
    """
    axis, kwargs = maybe_get_ax(**kwargs)
    xlimits = axis.get_xlim()
    ylimits = axis.get_ylim()

    # Draw for each IP
    for ip_name, ip_xpos in ip_positions.items():
        if xlimits[0] <= ip_xpos <= xlimits[1]:  # only plot if within plot's xlimits
            if lines:
                logger.debug(f"Drawing dashed axvline at location of {ip_name}")
                axis.axvline(ip_xpos, linestyle=":", color="grey", marker="", zorder=0)

            if location is not None and isinstance(location, str):
                inside: bool = location.lower() == "inside"
                logger.debug(f"Drawing name indicator for {ip_name}")
                # drawing ypos is lower end of ylimits if drawing inside, higher end if drawing outside
                ypos = ylimits[not inside] + (ylimits[1] + ylimits[0]) * 0.01
                c = "grey" if inside else matplotlib.rcParams["text.color"]  # match axis ticks color
                fontsize = plt.rcParams["xtick.labelsize"]  # match the xticks size
                axis.text(ip_xpos, ypos, ip_name, color=c, ha="center", va="bottom", size=fontsize)

        else:
            logger.debug(f"Skipping {ip_name} as its position is outside of the plot's xlimits")

    axis.set_xlim(xlimits)
    axis.set_ylim(ylimits)


def set_arrow_label(
    axis: matplotlib.axes.Axes,
    label: str,
    arrow_position: Tuple[float, float],
    label_position: Tuple[float, float],
    color: str = "k",
    arrow_arc_rad: float = -0.2,
    fontsize: int = 20,
    **kwargs,
) -> matplotlib.text.Annotation:
    """
    .. versionadded:: 0.6.0

    Adds on the provided `matplotlib.axes.Axes` a label box with text and an arrow from the box to a specified position.
    Original code from :user:`Guido Sterbini <sterbini>`.

    Args:
        axis (matplotlib.axes.Axes): a `matplotlib.axes.Axes` to plot on.
        label (str): label text to print on the axis.
        arrow_position (Tuple[float, float]): where on the plot to point the tip of the arrow.
        label_position (Tuple[float, float]): where on the plot the text label (and thus start
            of the arrow) is.
        color (str): color parameter for your arrow and label. Defaults to "k".
        arrow_arc_rad (float): angle value defining the upwards / downwards shape of and
            bending of the arrow.
        fontsize (int): text size in the box.
        **kwargs: additional keyword arguments are transmitted to `~matplotlib.axes.Axes.annotate`.
            If either `ax` or `axis` is found in the kwargs, the corresponding value is used as the
            axis object to plot on.

    Returns:
        A `matploblit.text.Annotation` of the created annotation.

    Example:
        .. code-block:: python

            >>> set_arrow_label(
            ...     label="Your label",
            ...     arrow_position=(1, 2),
            ...     label_position=(1.1 * some_value, 0.75 * another_value),
            ...     color="indianred",
            ...     arrow_arc_rad=0.3,
            ...     fontsize=25,
            ... )
    """
    axis, kwargs = maybe_get_ax(**kwargs)
    return axis.annotate(
        label,
        xy=arrow_position,
        xycoords="data",
        xytext=label_position,
        textcoords="data",
        size=fontsize,
        color=color,
        va="center",
        ha="center",
        bbox=dict(boxstyle="round4", fc="w", color=color),
        arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=" + str(arrow_arc_rad), fc="w", color=color),
        **kwargs,
    )


# ----- Private Helpers ----- #


def _get_twiss_table_with_offsets_and_limits(
    madx: Madx, xoffset: float = 0, xlimits: Tuple[float, float] = None
) -> pd.DataFrame:
    """
    .. versionadded:: 1.0.0

    Get the twiss dataframe from madx, only within the provided `xlimits` and with the s axis shifted by
    the given `xoffset`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        xoffset (float): An offset applied to the S coordinate in the dataframe.
        xlimits (Tuple[float, float]): will only consider elements within xlimits (for the s coordinate) if
            this is not `None`, using the tuple passed.

    Returns:
        The ``TWISS`` dataframe from ``MAD-X``, with the limits and offset applied, if any.
    """
    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    logger.trace("Getting TWISS table from MAD-X")
    madx.command.twiss()
    twiss_df = madx.table.twiss.dframe().copy()
    twiss_df.s = twiss_df.s - xoffset
    twiss_df = twiss_df[twiss_df.s.between(*xlimits)] if xlimits else twiss_df
    return twiss_df


def _determine_default_sbs_coupling_ylabel(rdt: str, component: str) -> str:
    """
    .. versionadded:: 0.19.0

    Creates the ``LaTeX``-compatible label for the Y-axis based on the given coupling *rdt* and its *component*.

    Args:
        rdt (str): The name of the coupling resonance driving term, either ``F1001`` or ``F1010``.
            Case insensitive.
        component (str): Which component of the RDT is considered, either ``ABS``, ``RE`` or ``IM``,
            for absolute value or real / imaginary part, respectively. Case insensitive.

    Returns:
        The label string.

    Example:
        .. code-block:: python

            >>> coupling_label = _determine_default_sbs_coupling_ylabel(rdt="f1001", component="RE")
    """
    logger.debug(f"Determining a default label for the {component.upper()} component of coupling {rdt.upper()}.")
    assert rdt.upper() in ("F1001", "F1010")
    assert component.upper() in ("ABS", "RE", "IM")

    if component.upper() == "ABS":
        opening = closing = "|"
    elif component.upper() == "RE":
        opening, closing = r"\Re ", ""
    else:
        opening, closing = r"\Im ", ""

    rdt_latex = r"f_{1001}" if rdt.upper() == "F1001" else r"f_{1010}"
    return r"$" + opening + rdt_latex + closing + r"$"


def _determine_default_sbs_phase_ylabel(plane: str) -> str:
    """
    .. versionadded:: 0.19.0

    Creates the ``LaTeX``-compatible label for the phase Y-axis based on the given *plane*.

    Args:
        plane (str): The plane of the phase, either ``X`` or ``Y``. Case insensitive.

    Returns:
        The label string.

    Example:
        .. code-block:: python

            >>> phase_label = _determine_default_sbs_phase_ylabel(plane="X")
    """
    logger.debug(f"Determining a default label for the {plane.upper()} phase plane.")
    assert plane.upper() in ("X", "Y")

    beginning = r"\Delta "
    term = r"\phi_{x}" if plane.upper() == "X" else r"\phi_{y}"
    return r"$" + beginning + term + r"$"
