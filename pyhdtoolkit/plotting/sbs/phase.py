"""
.. _plotting-sbs-phase:

Segment-by-Segment Phase
------------------------

Functions to plot phase values of Segment-by-Segment results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import tfs

from loguru import logger
from matplotlib.legend import _get_legend_handles_labels

from pyhdtoolkit.plotting.utils import find_ip_s_from_segment_start

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def plot_phase_segment_one_beam(
    phase_x: tfs.TfsDataFrame,
    phase_y: tfs.TfsDataFrame,
    model: tfs.TfsDataFrame = None,
    ip: int | None = None,
    **kwargs,
) -> Figure:
    """
    .. versionadded:: 0.19.0

    Plots the propagated measured phase and the propagated corrected phase
    for the given IP segment, for both planes for a given beam. Optionally
    highlights the IP location in the segment. One can find an example use
    of this function in the :ref:`segment-by-segment plotting
    <demo-sbs-plotting>` example gallery.

    Parameters
    ----------
    phase_x : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment phase result for the
        horizontal plane in the given segment.
    phase_y : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment phase result for the
        vertical plane in the given segment.
    model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the model used in the analysis. If given, the
        IP location in the segment will be highlighted by a vertical grey line.
    ip : int, optional
        The IP number of the segment. Used for the label of the vertical
        grey line. Requires to have provided the model dataframe.
    **kwargs
        Keyword arguments will be transmitted to the figure creation call to
        `~matplotlib.pyplot.subplots`. If ``bbox_to_anchor`` is found, it will
        be used to position the legend across the whole figure space.

    Returns
    -------
    matplotlib.figure.Figure
        The `~matplotlib.figure.Figure` on which the plot is created.

    Example
    -------
        .. code-block:: python

            fig = plot_phase_segment_one_beam(
                sbs_phasex, sbs_phasey, model=b2_model_tfs, ip=5, figsize=(8, 8)
            )
    """
    logger.debug("Plotting the phase for both planes over the segment.")
    # legend_bbox_to_anchor = kwargs.pop("bbox_to_anchor", (0.535, 0.97))
    figure, (ax1, ax2) = plt.subplots(2, 1, **kwargs)

    plot_phase_segment(ax1, segment_df=phase_x, model_df=model, plane="x", ip=ip)
    plot_phase_segment(ax2, segment_df=phase_y, model_df=model, plane="y", ip=ip)

    ax1.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left", ncol=4)
    ax2.set_xlabel(r"$\mathrm{S\ [m]}$")
    plt.tight_layout()
    return figure


def plot_phase_segment_both_beams(
    b1_phase_x: tfs.TfsDataFrame,
    b1_phase_y: tfs.TfsDataFrame,
    b2_phase_x: tfs.TfsDataFrame,
    b2_phase_y: tfs.TfsDataFrame,
    b1_model: tfs.TfsDataFrame = None,
    b2_model: tfs.TfsDataFrame = None,
    ip: int | None = None,
    **kwargs,
) -> Figure:
    """
    .. versionadded:: 0.19.0

    Plots the propagated measured phase and the propagated corrected phase
    for the given IP segment, for both planes and both beams. Optionally
    highlights the IP location in the segment. One can find an example use
    of this function in the :ref:`segment-by-segment plotting
    <demo-sbs-plotting>` example gallery.

    Parameters
    ----------
    b1_phase_x : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment phase result for
        the horizontal plane in the given segment, for Beam 1.
    b1_phase_y : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment phase result for
        the vertical plane in the given segment, for Beam 1.
    b2_phase_x : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment phase result for
        the horizontal plane in the given segment, for Beam 2.
    b2_phase_x : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment phase result for
        the vertical plane in the given segment, for Beam 2.
    b1_model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the Beam 1 model used in the analysis.
        If given, then the IP location in the segment will be highlighted
        by a vertical grey line.
    b2_model : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the Beam 2 model used in the analysis.
        If given, then the IP location in the segment will be highlighted
        by a vertical grey line.
    ip : int, optional
        The IP number of the segment. Used for the label of the vertical
        grey line. Requires to have provided the model dataframe.

    Returns
    -------
    matplotlib.figure.Figure
        The `~matplotlib.figure.Figure` on which the plot is created.

    Example
    -------
        .. code-block:: python

            fig = plot_phase_segment_both_beams(
                phasex_b1_tfs,
                phasey_b1_tfs,
                phasex_b2_tfs,
                phasey_b2_tfs,
                b1_model_tfs,
                b2_model_tfs,
                ip=1,
                figsize=(18, 9),
                bbox_to_anchor=(0.535, 0.94),
            )
    """
    logger.debug("Plotting the phase for both planes over the segment.")
    legend_bbox_to_anchor = kwargs.pop("bbox_to_anchor", (0.535, 0.97))
    figure, ((b1x, b2x), (b1y, b2y)) = plt.subplots(2, 2, sharex=True, sharey="row", **kwargs)

    # Plotting B1 data
    plot_phase_segment(b1x, segment_df=b1_phase_x, model_df=b1_model, plane="x", ip=ip)
    plot_phase_segment(b1y, segment_df=b1_phase_y, model_df=b1_model, plane="y", ip=ip)

    # Plotting B2 data
    plot_phase_segment(b2x, segment_df=b2_phase_x, model_df=b2_model, plane="x", ip=ip)
    plot_phase_segment(b2y, segment_df=b2_phase_y, model_df=b2_model, plane="y", ip=ip)

    # X axis labels
    b1y.set_xlabel(r"$\mathrm{S\ [m]}$")
    b2y.set_xlabel(r"$\mathrm{S\ [m]}$")

    # Erasing Y labels of B2 (on the right)
    b2x.set_ylabel(None)
    b2y.set_ylabel(None)

    # Suptitles
    b1x.set_title(r"$\mathrm{Beam\ 1}$", y=1.01)
    b2x.set_title(r"$\mathrm{Beam\ 2}$", y=1.01)

    figure.legend(*_get_legend_handles_labels([b1x]), ncol=2, bbox_to_anchor=legend_bbox_to_anchor, loc="lower center")
    plt.tight_layout()
    return figure


# ----- Workhorse ----- #


def plot_phase_segment(
    ax: Axes = None,
    segment_df: tfs.TfsDataFrame = None,
    model_df: tfs.TfsDataFrame = None,
    plane: str = "x",
    ip: int | None = None,
) -> None:
    """
    .. versionadded:: 0.19.0

    Plots a the phase for a given plane over the segment, optionally
    highlighting the IP location. One can find an example use of this
    function in the :ref:`segment-by-segment plotting <demo-sbs-plotting>`
    example gallery.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        The `~matplotlib.axes.Axes` to plot on. Will get the current axis
        if no `~matplotlib.axes.Axes` is given.
    segment_df : tfs.TfsDataFrame
        A `~tfs.TfsDataFrame` of the segment-by-segment coupling result for
        the given segment.
    model_df : tfs.TfsDataFrame, optional
        A `~tfs.TfsDataFrame` of the model used in the analysis. If given,
        then the IP location in the segment will be determined from the two
        dataframes and will be highlighted in the plot by a vertical grey
        line.
    plane : str
        The plane the data is is for in the provided *segment_df*. Will be
        used for the ylabel. Should be either "x" or "y", case-insensitive.
    ip : int, optional
        The IP number of the segment. Used for the label of the vertical
        grey line. Requires to have provided the model dataframe.

    Example
    -------
        .. code-block:: python

            plot_phase_segment(ax, segment_df, b1_model_tfs, plane="x", ip=1)
    """
    if plane.upper() not in ("X", "Y"):
        logger.error("The provided plane is invalid, should be either 'x' or 'y', case-insensitively.")
        msg = "Invalid 'plane' argument."
        raise ValueError(msg)
    plane = plane.upper()

    logger.debug(f"Plotting phase for plane {plane.upper()} over the segment")
    ax = plt.gca() if ax is None else ax
    ax.set_ylabel(r"$\mathrm{\Delta \phi_{" + plane + "}}$")

    ax.errorbar(
        segment_df.S,
        segment_df[f"PROPPHASE{plane}"],
        yerr=segment_df[f"ERRPROPPHASE{plane}"],
        fmt="o-",
        markersize=3,
        capsize=2,
        color="C0",
        label="Measurement",
    )
    ax.errorbar(
        segment_df.S,
        segment_df[f"CORPHASE{plane}"],
        yerr=segment_df[f"ERRCORPHASE{plane}"],
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
