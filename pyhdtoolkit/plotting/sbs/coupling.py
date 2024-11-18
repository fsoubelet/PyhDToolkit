"""
.. _plotting-sbs-coupling:

Segment-by-Segment Coupling
---------------------------

Functions to plot coupling components of Segment-by-Segment results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import tfs

from loguru import logger
from matplotlib.legend import _get_legend_handles_labels

from pyhdtoolkit.plotting.utils import _determine_default_sbs_coupling_ylabel, find_ip_s_from_segment_start

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def plot_rdt_component(
    b1_segment_df: tfs.TfsDataFrame,
    b2_segment_df: tfs.TfsDataFrame,
    b1_model: tfs.TfsDataFrame = None,
    b2_model: tfs.TfsDataFrame = None,
    ip: int | None = None,
    rdt: str = "F1001",
    component: str = "ABS",
    **kwargs,
) -> Figure:
    r"""
    .. versionadded:: 0.19.0

    Plots for Beam 1 and Beam 2 vertically a component of the given coupling
    *rdt* over the segment. Optionally highlights the IP location. One can find
    an example use of this function in the :ref:`segment-by-segment plotting
    <demo-sbs-plotting>` example gallery.

    Parameters
    ----------
    b1_segment_df : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment coupling result for
        Beam 1 in the given segment.
    b2_segment_df : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment coupling result for
        Beam 2 in the given segment.
    b1_model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the Beam 1 model used in the analysis. If
        given then the IP location in the segment will be highlighted by a
        vertical grey line.
    b2_model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the Beam 2 model used in the analysis. If
        given then the IP location in the segment will be highlighted by a
        vertical grey line.
    ip : int, optional
        The IP number of the segment. Used for the label of the vertical
        grey line. Requires to have provided the model dataframe.
    rdt : str
        The name of the coupling resonance driving term to plot, either
        ``F1001`` or ``F1010``. Case insensitive.
    component : str
        Which component of the RDT is considered, either ``ABS``, ``RE`` or
        ``IM``, for absolute value or real / imaginary part, respectively.
        Case insensitive.
    **kwargs
        Keyword arguments will be transmitted to the figure creation call to
        `~matplotlib.pyplot.subplots`. If ``b1_ylabel`` or ``b2_ylabel`` are
        found, they will be used as y-label for the respective beams axes.

    Returns
    -------
    matplotlib.figure.Figure
        The `~matplotlib.figure.Figure` on which the plot is created.

    Example
    -------
        .. code-block:: python

            fig = plot_rdt_component(
                b1_segment_df=tfs.read("B1/sbscouple_IP1.out"),
                b2_segment_df=tfs.read("B2/sbscouple_IP1.out"),
                b1_model=b1_model_tfs,
                b2_model=b2_model_tfs,
                ip=1,
                figsize=(8, 8),
                b1_ylabel=r"$\mathrm{Beam\ 1}$ $|f_{1001}|$",
                b2_ylabel=r"$\mathrm{Beam\ 2}$ $|f_{1001}|$",
            )
    """
    logger.debug(f"Plotting the {component.upper()} component of {rdt.upper()} for both beams over the segment.")
    b1_ylabel = kwargs.pop("b1_ylabel", None)
    b2_ylabel = kwargs.pop("b2_ylabel", None)
    fig, (ax1, ax2) = plt.subplots(2, 1, **kwargs)

    _plot_sbs_coupling_rdt_component(
        ax=ax1,
        segment_df=b1_segment_df,
        model_df=b1_model,
        ip=ip,
        rdt=rdt,
        component=component,
        ylabel=b1_ylabel,
    )
    _plot_sbs_coupling_rdt_component(
        ax=ax2,
        segment_df=b2_segment_df,
        model_df=b2_model,
        ip=ip,
        rdt=rdt,
        component=component,
        ylabel=b2_ylabel,
    )

    ax1.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left", ncol=4)
    ax2.set_xlabel(r"$S\ [m]$")
    plt.tight_layout()
    return fig


def plot_full_ip_rdt(
    b1_segment_df: tfs.TfsDataFrame,
    b2_segment_df: tfs.TfsDataFrame,
    b1_model: tfs.TfsDataFrame = None,
    b2_model: tfs.TfsDataFrame = None,
    ip: int | None = None,
    rdt: str = "F1001",
    abs_ylimits: tuple[float, float] | None = None,
    real_ylimits: tuple[float, float] | None = None,
    imag_ylimits: tuple[float, float] | None = None,
    **kwargs,
) -> Figure:
    """
    .. versionadded:: 0.19.0

    Plots all component of the given coupling *rdt* over the segment, for
    both Beam 1 and Beam 2. Optionally highlights the IP location. One can
    find an example use of this function in the :ref:`segment-by-segment
    plotting <demo-sbs-plotting>` example gallery.

    Parameters
    ----------
    b1_segment_df : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment coupling result for
        Beam 1 in the given segment.
    b2_segment_df : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment coupling result for
        Beam 2 in the given segment.
    b1_model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the Beam 1 model used in the analysis. If
        given then the IP location in the segment will be highlighted by a
        vertical grey line.
    b2_model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the Beam 2 model used in the analysis. If
        given then the IP location in the segment will be highlighted by a
        vertical grey line.
    ip : int, optional
        The IP number of the segment. Used for the label of the vertical
        grey line. Requires to have provided the model dataframe.
    rdt : str
        The name of the coupling resonance driving term to plot, either
        ``F1001`` or ``F1010``. Case insensitive.
    **kwargs
        Keyword arguments will be transmitted to the figure creation call to
        `~matplotlib.pyplot.subplots`. If ``b1_ylabel`` or ``b2_ylabel`` are
        found, they will be used as y-label for the respective beams axes.
        If ``bbox_to_anchor`` is found, it will be used to position the legend
        across the whole figure space.

    Returns
    -------
    matplotlib.figure.Figure
        The `~matplotlib.figure.Figure` on which the plot is created.

    Example
    -------
        .. code-block:: python

            fig = plot_full_ip_rdt(
                couple_b1_tfs,
                couple_b2_tfs,
                b1_model_tfs,
                b2_model_tfs,
                ip=1,
                figsize=(18, 9),
                abs_ylimits=(5e-3, 6.5e-2),
                real_ylimits=(-1e-1, 1e-1),
                imag_ylimits=(-1e-1, 1e-1),
            )
    """
    legend_bbox_to_anchor = kwargs.pop("bbox_to_anchor", (0.52, 0.93))
    fig, ((abs_b1, abs_b2), (real_b1, real_b2), (imag_b1, imag_b2)) = plt.subplots(
        3, 2, sharex=True, sharey="row", **kwargs
    )

    # Top row, rdt abs
    _plot_sbs_coupling_rdt_component(
        ax=abs_b1, segment_df=b1_segment_df, model_df=b1_model, ip=ip, rdt=rdt, component="ABS"
    )
    _plot_sbs_coupling_rdt_component(
        ax=abs_b2, segment_df=b2_segment_df, model_df=b2_model, ip=ip, rdt=rdt, component="ABS", ylabel=""
    )
    if abs_ylimits:
        logger.debug(f"Adjusting ylimits of absolute values subplots to {abs_ylimits}")
        abs_b1.set_ylim(abs_ylimits)  # only apply to one as they share ylimits

    # Middle row, rdt real
    _plot_sbs_coupling_rdt_component(
        ax=real_b1, segment_df=b1_segment_df, model_df=b1_model, ip=ip, rdt=rdt, component="RE"
    )
    _plot_sbs_coupling_rdt_component(
        ax=real_b2, segment_df=b2_segment_df, model_df=b2_model, ip=ip, rdt=rdt, component="RE", ylabel=""
    )
    if real_ylimits:
        logger.debug(f"Adjusting ylimits of real values subplots to {real_ylimits}")
        real_b1.set_ylim(real_ylimits)  # only apply to one as they share ylimits

    # Bottom row, rdt imag
    _plot_sbs_coupling_rdt_component(
        ax=imag_b1, segment_df=b1_segment_df, model_df=b1_model, ip=ip, rdt=rdt, component="IM"
    )
    _plot_sbs_coupling_rdt_component(
        ax=imag_b2, segment_df=b2_segment_df, model_df=b2_model, ip=ip, rdt=rdt, component="IM", ylabel=""
    )
    if imag_ylimits:
        logger.debug(f"Adjusting ylimits of imaginary values subplots to {imag_ylimits}")
        imag_b1.set_ylim(imag_ylimits)  # only apply to one as they share ylimits

    # Legend, this is a bit of a hacky way to get it between `Beam 1` and `Beam 2` titles
    fig.legend(*_get_legend_handles_labels([abs_b1]), ncol=2, bbox_to_anchor=legend_bbox_to_anchor, loc="lower center")

    # X axis labels
    imag_b1.set_xlabel(r"$\mathrm{S\ [m]}$")
    imag_b2.set_xlabel(r"$\mathrm{S\ [m]}$")

    # Suptitles
    abs_b1.set_title(r"$\mathrm{Beam\ 1}$", y=1.01)
    abs_b2.set_title(r"$\mathrm{Beam\ 2}$", y=1.01)
    plt.tight_layout()
    return fig


# ----- Workhorse ----- #


def _plot_sbs_coupling_rdt_component(
    ax: Axes,
    segment_df: tfs.TfsDataFrame,
    model_df: tfs.TfsDataFrame = None,
    ip: int | None = None,
    rdt: str = "F1001",
    component: str = "ABS",
    ylabel: str | None = None,
) -> None:
    """
    Plots a component of the given coupling RDT over the segment,
    optionally highlighting the IP location.

    Parameters
    ----------
    ax : Axes
        The `~matplotlib.axes.Axes` to plot on. Will get the current
        axis if no `~matplotlib.axes.Axes` is given.
    segment_df : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment coupling result
        for the given segment.
    model_df : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the model used in the analysis. If
        given, then the IP location in the segment will be determined
        from the two dataframes and will be highlighted in the plot by
        a vertical grey line.
    ip : int, optional
        The IP number of the segment. Used for the label of the vertical
        grey line. Requires to have provided the model dataframe.
    rdt : str
        The name of the coupling resonance driving term to plot, either
        ``F1001`` or ``F1010``. Case insensitive.
    component : str
        Which component of the RDT is considered, either ``ABS``, ``RE`` or
        ``IM``, for absolute value or real / imaginary part, respectively.
        Case insensitive.
    ylabel : str, optional
        A specific string to use as y-label on the axis. If not given, a
        default label will be determined from the provided rdt and component.
    """
    logger.debug(f"Plotting the {component.upper()} component of coupling {rdt.upper()} over the segment.")
    ax = plt.gca() if ax is None else ax
    ylabel = _determine_default_sbs_coupling_ylabel(rdt, component) if ylabel is None else ylabel
    ax.set_ylabel(ylabel)
    ax.errorbar(
        segment_df.S,
        segment_df[f"{rdt.upper()}{component.upper()}MEAS"],
        yerr=segment_df[f"ERR{rdt.upper()}{component.upper()}MEAS"],
        fmt="o-",
        markersize=3,
        capsize=2,
        color="C0",
        label="Measurement",
    )
    ax.errorbar(
        segment_df.S,
        segment_df[f"{rdt.upper()}{component.upper()}COR"],
        yerr=segment_df[f"ERR{rdt.upper()}{component.upper()}COR"],
        fmt="o-",
        markersize=3,
        capsize=2,
        color="C1",
        label="Correction",
    )
    if model_df is not None and isinstance(model_df, tfs.TfsDataFrame):
        # If model dataframe is given, find S location of IP and highlight it
        logger.debug("Plotting the IP location in the segment.")
        ips = find_ip_s_from_segment_start(segment_df=segment_df, model_df=model_df, ip=ip)
        ax.axvline(ips, ls="--", color="grey")
