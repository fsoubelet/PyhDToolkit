"""
.. _plotting-utils:

Plotting Utility Functions
--------------------------

Module with functions to used throught the different `~pyhdtoolkit.plotting` modules.
"""

from __future__ import annotations  # important for Sphinx to generate short type signatures!

from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from matplotlib import transforms
from matplotlib.patches import Ellipse

if TYPE_CHECKING:
    import pandas as pd
    from cpymad.madx import Madx
    from matplotlib.text import Annotation
    from numpy.typing import ArrayLike
    from tfs import TfsDataFrame

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

            def my_plotting_function(*args, **kwargs):
                ax, kwargs = maybe_get_ax(**kwargs)
                # do stuff with ax
                ax.plot(*args, **kwargs)
    """
    logger.debug("Looking for axis object to plot on")
    if "ax" in kwargs:
        logger.debug("Using the provided kwargs 'ax' as the axis to plot on")
        ax = kwargs.pop("ax")
    elif "axis" in kwargs:
        logger.debug("Using the provided kwargs 'axis' as the axis to plot on")
        ax = kwargs.pop("axis")
    else:
        logger.debug("No axis provided, using `plt.gca()`")
        ax = plt.gca()
    return ax, dict(kwargs)


def find_ip_s_from_segment_start(segment_df: TfsDataFrame, model_df: TfsDataFrame, ip: int) -> float:
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

            ip_offset_in_segment = find_ip_s_from_segment_start(
                segment_df=sbsphaseext_IP1, model_df=twiss_elements, ip=1
            )
    """
    logger.debug(f"Determining location of IP{ip:d} from the start of segment.")
    first_element: str = segment_df.NAME.to_numpy()[0]
    first_element_s_in_model = model_df[first_element == model_df.NAME].S.to_numpy()[0]
    ip_s_in_model = model_df[f"IP{ip:d}" == model_df.NAME].S.to_numpy()[0]

    # Handle case where IP segment is cut and by end of sequence and the IP is at beginning of machine
    if ip_s_in_model < first_element_s_in_model:
        # Distance to end of sequence + distance from start to IP s
        logger.debug("IP{ip:d} segment seems cut off by end of sequence, looping around to determine IP location")
        distance = (model_df.S.to_numpy().max() - first_element_s_in_model) + ip_s_in_model
    else:  # just the difference
        distance = ip_s_in_model - first_element_s_in_model
    return distance


def get_lhc_ips_positions(dataframe: pd.DataFrame) -> dict[str, float]:
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

            twiss_df = tfs.read("twiss_output.tfs", index="NAME")
            ips = get_lhc_ips_positions(twiss_df)
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
    return dict(zip(ip_names, ip_pos, strict=False))


def make_elements_groups(
    madx: Madx, /, xoffset: float = 0, xlimits: tuple[float, float] | None = None
) -> dict[str, pd.DataFrame]:
    """
    .. versionadded:: 1.0.0

    Provided with an active `cpymad` instance after having ran a script, will returns different portions of
    the twiss table's dataframe for different magnetic elements.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object. Positional only.
        xoffset (float): An offset applied to the S coordinate before plotting. This is useful is you want
            to center a plot around a specific point or element, which would then become located at s = 0.
        xlimits (tuple[float, float]): will only consider elements within xlim (for the s coordinate) if this
            is not None, using the tuple passed.

    Returns:
        A `dict` containing a `pd.DataFrame` for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.

    Example:
        .. code-block:: python

            element_dfs = make_elements_groups(madx)
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


def make_survey_groups(madx: Madx, /) -> dict[str, pd.DataFrame]:
    """
    .. versionadded:: 1.0.0

    Provided with an active `cpymad` instance after having ran a script, will returns different portions of
    the survey table's dataframe for different magnetic elements.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object. Positional only.

    Returns:
        A `dict` containing a `pd.DataFrame` for dipoles, focusing quadrupoles, defocusing
        quadrupoles, sextupoles and octupoles. The keys are self-explanatory.

    Example:
        .. code-block:: python

            survey_dfs = make_survey_groups(madx)
    """
    element_dfs = make_elements_groups(madx)
    quadrupoles_focusing_df = element_dfs["quadrupoles"].query("k1l > 0")
    quadrupoles_defocusing_df = element_dfs["quadrupoles"].query("k1l < 0")

    logger.debug("Getting different element groups dframes from MAD-X survey")
    madx.command.survey()

    survey_df = madx.table.survey.dframe()
    return {
        "dipoles": survey_df[survey_df.index.isin(element_dfs["dipoles"].index.tolist())],
        "quad_foc": survey_df[survey_df.index.isin(quadrupoles_focusing_df.index.tolist())],
        "quad_defoc": survey_df[survey_df.index.isin(quadrupoles_defocusing_df.index.tolist())],
        "sextupoles": survey_df[survey_df.index.isin(element_dfs["sextupoles"].index.tolist())],
        "octupoles": survey_df[survey_df.index.isin(element_dfs["octupoles"].index.tolist())],
    }


# ----- Plotting Utilities -----#


def draw_ip_locations(
    ip_positions: dict[str, float] | None = None,
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

            twiss_df = tfs.read("twiss_output.tfs", index="NAME")
            twiss_df.plot(x="S", y=["BETX", "BETY"])
            ips = get_lhc_ips_positions(twiss_df)
            draw_ip_locations(ip_positions=ips)
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
                c = "grey" if inside else mpl.rcParams["text.color"]  # match axis ticks color
                fontsize = plt.rcParams["xtick.labelsize"]  # match the xticks size
                axis.text(ip_xpos, ypos, ip_name, color=c, ha="center", va="bottom", size=fontsize)

        else:
            logger.debug(f"Skipping {ip_name} as its position is outside of the plot's xlimits")

    axis.set_xlim(xlimits)
    axis.set_ylim(ylimits)


def set_arrow_label(
    label: str,
    arrow_position: tuple[float, float],
    label_position: tuple[float, float],
    color: str = "k",
    arrow_arc_rad: float = -0.2,
    fontsize: int = 20,
    **kwargs,
) -> Annotation:
    """
    .. versionadded:: 0.6.0

    Adds on the provided `matplotlib.axes.Axes` a label box with text and an arrow from the box to a specified position.
    Original code from :user:`Guido Sterbini <sterbini>`.

    Args:
        axis (matplotlib.axes.Axes): a `matplotlib.axes.Axes` to plot on.
        label (str): label text to print on the axis.
        arrow_position (tuple[float, float]): where on the plot to point the tip of the arrow.
        label_position (tuple[float, float]): where on the plot the text label (and thus start
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

            set_arrow_label(
                label="Your label",
                arrow_position=(1, 2),
                label_position=(1.1 * some_value, 0.75 * another_value),
                color="indianred",
                arrow_arc_rad=0.3,
                fontsize=25,
            )
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
        bbox={"boxstyle": "round4", "fc": "w", "color": color},
        arrowprops={
            "arrowstyle": "-|>",
            "connectionstyle": "arc3,rad=" + str(arrow_arc_rad),
            "fc": "w",
            "color": color,
        },
        **kwargs,
    )


def draw_confidence_ellipse(x: ArrayLike, y: ArrayLike, n_std: float = 3.0, facecolor="none", **kwargs) -> Ellipse:
    """
    .. versionadded:: 1.2.0

    Plot the covariance confidence ellipse of *x* and *y*. This code is taken from the
    `matplotlib gallery <https://matplotlib.org/stable/gallery/statistics/confidence_ellipse.html>`_.

    .. note::
        One might want to provide the `edgecolor` to this function.

    Args:
        x (ArrayLike): array-like, should be of shape (n,).
        y (ArrayLike): array-like, should be of shape (n,).
        n_std (float): The number of standard deviations of the data to
            highlight, to determine the ellipse's radiuses.
        facecolor (str): The facecolor of the ellipse.
        **kwargs: Any keyword argument will be forwarded to `~matplotlib.patches.Ellipse`.
            If either `ax` or `axis` is found in the kwargs, the corresponding value is
            used as the axis object to plot on.

    Returns:
        The corresponding `~matplotlib.patches.Ellipse` object added to the axis.

    Example:
        .. code-block:: python

            x = np.random.normal(size=1000)
            y = np.random.normal(size=1000)
            plt.plot(x, y, ".", markersize=0.8)
            draw_confidence_ellipse(x, y, n_std=2.5, edgecolor="red")
    """
    axis, kwargs = maybe_get_ax(**kwargs)
    x = np.array(x)
    y = np.array(y)

    if x.size != y.size:
        logger.error(f"x and y must be the same size, but shapes {x.shape} and {y.shape} were given.")
        msg = f"x and y must be the same size, but shapes {x.shape} and {y.shape} were given."
        raise ValueError(msg)

    logger.debug("Computing covariance matrix and pearson correlation coefficient")
    covariance_matrix = np.cov(x, y)
    pearson = covariance_matrix[0, 1] / np.sqrt(covariance_matrix[0, 0] * covariance_matrix[1, 1])

    # Using a special case to obtain the eigenvalues of this two-dimensionl dataset.
    logger.debug("Computing radiuses of the ellipse")
    radius_x = np.sqrt(1 + pearson)
    radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0), width=radius_x * 2, height=radius_y * 2, facecolor=facecolor, **kwargs)

    # Calculating the stdev of x from the square root of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(covariance_matrix[0, 0]) * n_std
    mean_x = np.mean(x)

    # Calculating the stdev of y from the square root of the variance and multiplying
    # with the given number of standard deviations.
    scale_y = np.sqrt(covariance_matrix[1, 1]) * n_std
    mean_y = np.mean(y)

    logger.debug("Preparing and drawing ellipse patch")
    transf = transforms.Affine2D().rotate_deg(45).scale(scale_x, scale_y).translate(mean_x, mean_y)
    ellipse.set_transform(transf + axis.transData)
    return axis.add_patch(ellipse)


# ----- Private Helpers ----- #


def _get_twiss_table_with_offsets_and_limits(
    madx: Madx, /, xoffset: float = 0, xlimits: tuple[float, float] | None = None, **kwargs
) -> pd.DataFrame:
    """
    .. versionadded:: 1.0.0

    Get the twiss dataframe from madx, only within the provided `xlimits` and with the s axis shifted by
    the given `xoffset`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object. Positional only.
        xoffset (float): An offset applied to the S coordinate in the dataframe.
        xlimits (tuple[float, float]): will only consider elements within xlimits (for the s coordinate) if
            this is not `None`, using the tuple passed.
        **kwargs: any keyword argument will be transmitted to the ``MAD-X`` ``TWISS` command.

    Returns:
        The ``TWISS`` dataframe from ``MAD-X``, with the limits and offset applied, if any.
    """
    # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
    logger.trace("Getting TWISS table from MAD-X")
    madx.command.twiss(**kwargs)
    twiss_df = madx.table.twiss.dframe()
    twiss_df.s = twiss_df.s - xoffset
    return twiss_df[twiss_df.s.between(*xlimits)] if xlimits else twiss_df


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

            coupling_label = _determine_default_sbs_coupling_ylabel(
                rdt="f1001", component="RE"
            )
    """
    logger.debug(f"Determining a default label for the {component.upper()} component of coupling {rdt.upper()}.")
    if rdt.upper() not in ("F1001", "F1010"):
        msg = "Invalid RDT for coupling plot."
        raise ValueError(msg)
    if component.upper() not in ("ABS", "RE", "IM"):
        msg = "Invalid component for coupling RDT."
        raise ValueError(msg)

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

            phase_label = _determine_default_sbs_phase_ylabel(plane="X")
    """
    logger.debug(f"Determining a default label for the {plane.upper()} phase plane.")
    if plane.upper() not in ("X", "Y"):
        msg = "Invalid plane for phase plot."
        raise ValueError(msg)

    beginning = r"\Delta "
    term = r"\phi_{x}" if plane.upper() == "X" else r"\phi_{y}"
    return r"$" + beginning + term + r"$"


# ----- Sphinx Gallery Scraper ----- #


# To use SVG outputs when scraping matplotlib figures for the sphinx-gallery, see:
# https://sphinx-gallery.github.io/stable/advanced.html#example-3-matplotlib-with-svg-format
def _matplotlib_svg_scraper(*args, **kwargs):
    from sphinx_gallery.scrapers import matplotlib_scraper

    kwargs.pop("format", None)
    return matplotlib_scraper(*args, format="svg", **kwargs)
