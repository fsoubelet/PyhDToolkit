"""
.. _plotting-crossing:

Crossing Scheme Plotters
------------------------

Module with functions to plot LHC crossing schemes
through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from loguru import logger

if TYPE_CHECKING:
    from cpymad.madx import Madx
    from matplotlib.axes import Axes
    from pandas import DataFrame
    from tfs import TfsDataFrame


def plot_two_lhc_ips_crossings(
    madx: Madx, /, first_ip: int, second_ip: int, ir_limit: float = 275, highlight_mqx_and_mbx: bool = True
) -> None:
    """
    .. versionadded:: 1.0.0

    Creates a plot representing the crossing schemes at the two provided
    IPs. One can find an example use of this function in the :ref:`LHC
    crossing schemes <demo-crossing-schemes>` example gallery.

    Note
    ----
        This function has some heavy logic behind it, especially in how it
        needs to order several axes. The easiest way to go about using it
        is to manually create and empty figure with the desired properties
        (size, etc) then call this function. See the example below or the
        gallery for more details.

    Note
    ----
        This assumes the appropriate LHC sequence and opticsfile have been
        loaded, and both ``lhcb1`` and ``lhcb2`` beams are defined. It is
        very recommended to first re-cycle the sequences so that the desired
        IPs do not happen at beginning or end of the lattice.

    Warning
    -------
        This function will get ``TWISS`` tables for both beams, which means
        it will ``USE`` both the ``lhcb1`` and ``lhcb2`` sequences, erasing
        previously defined errors or orbit corrections. The second sequence
        ``USE`` will be called on is ``lhcb2``, which may not be the one you
        were using before. Please re-``use`` your wanted sequence after you
        have called this function!

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    first_ip : int
        The first of the two IPs to plot crossing schemes for.
    second_ip : int
        The second of the two IPs to plot crossing schemes for.
    ir_limit : float
        The amount of meters to keep left and right of the IP point. Will
        also determine the ``xlimits`` of the plots. Defaults to 275.
    highlight_mqx_and_mbx : bool
        If `True`, will add patches highlighting the zones corresponding
        to ``MBX`` and ``MQX`` elements. Defaults to `True`.
    **kwargs
        If either `ax` or `axis` is found in the kwargs, the corresponding
        value is used as the axis object to plot on.

    Examples
    --------

        .. code-block:: python

            plt.figure(figsize=(18, 12))
            plot_two_lhc_ips_crossings(madx, first_ip=1, second_ip=5)

        .. code-block:: python

            plt.figure(figsize=(16, 11))
            plot_two_lhc_ips_crossings(
                madx, first_ip=2, second_ip=8, highlight_mqx_and_mbx=False
            )
    """
    logger.warning("You should re-call the 'USE' command on your wanted sequence after this plot!")
    # ----- Getting Twiss table dframe for each beam ----- #
    logger.debug("Getting TWISS table for LHCB1")
    madx.use(sequence="lhcb1")
    madx.command.twiss(centre=True)
    twiss_df_b1 = madx.table.twiss.dframe()

    logger.debug("Getting TWISS table for LHCB2")
    madx.use(sequence="lhcb2")
    madx.command.twiss(centre=True)
    twiss_df_b2 = madx.table.twiss.dframe()

    logger.trace("Determining exact locations of IP points")
    first_ip_s = twiss_df_b1.s[f"ip{first_ip}"]
    second_ip_s = twiss_df_b1.s[f"ip{second_ip}"]

    # ----- Plotting figure ----- #
    logger.debug(f"Plotting crossing schemes for IP{first_ip} and IP{second_ip}")
    # figure = plt.gcf()
    first_ip_x_axis = plt.subplot2grid((2, 2), (0, 0), colspan=1, rowspan=1)
    first_ip_y_axis = plt.subplot2grid((2, 2), (1, 0), colspan=1, rowspan=1)
    second_ip_x_axis = plt.subplot2grid((2, 2), (0, 1), colspan=1, rowspan=1)
    second_ip_y_axis = plt.subplot2grid((2, 2), (1, 1), colspan=1, rowspan=1)

    logger.debug(f"Plotting for IP{first_ip}")
    b1_plot = twiss_df_b1[twiss_df_b1.s.between(first_ip_s - ir_limit, first_ip_s + ir_limit)].copy()
    b2_plot = twiss_df_b2[twiss_df_b2.s.between(first_ip_s - ir_limit, first_ip_s + ir_limit)].copy()
    b1_plot.s = b1_plot.s - first_ip_s
    b2_plot.s = b2_plot.s - first_ip_s

    plot_single_ir_crossing(
        first_ip_x_axis,
        b1_plot,
        b2_plot,
        plot_column="x",
        scaling=1e3,
        ylabel="Orbit X $[mm]$",
        title=f"IP{first_ip} Crossing Schemes",
    )
    plot_single_ir_crossing(
        first_ip_y_axis,
        b1_plot,
        b2_plot,
        plot_column="y",
        scaling=1e3,
        ylabel="Orbit Y $[mm]$",
        xlabel=f"Distance to IP{first_ip} $[m]$",
    )

    logger.debug(f"Plotting for IP{second_ip}")
    b1_plot = twiss_df_b1[twiss_df_b1.s.between(second_ip_s - ir_limit, second_ip_s + ir_limit)].copy()
    b2_plot = twiss_df_b2[twiss_df_b2.s.between(second_ip_s - ir_limit, second_ip_s + ir_limit)].copy()
    b1_plot.s = b1_plot.s - second_ip_s
    b2_plot.s = b2_plot.s - second_ip_s

    plot_single_ir_crossing(
        second_ip_x_axis, b1_plot, b2_plot, plot_column="x", scaling=1e3, title=f"IP{second_ip} Crossing Schemes"
    )
    plot_single_ir_crossing(
        second_ip_y_axis, b1_plot, b2_plot, plot_column="y", scaling=1e3, xlabel=f"Distance to IP{second_ip} $[m]$"
    )

    if highlight_mqx_and_mbx:
        logger.debug("Highlighting MQX and MBX areas near IPs")
        _highlight_mbx_and_mqx(first_ip_x_axis, plot_df=b1_plot, ip=first_ip)
        _highlight_mbx_and_mqx(first_ip_y_axis, plot_df=b1_plot, ip=first_ip)
        _highlight_mbx_and_mqx(second_ip_x_axis, plot_df=b1_plot, ip=second_ip)
        _highlight_mbx_and_mqx(second_ip_y_axis, plot_df=b1_plot, ip=second_ip)
    plt.tight_layout()


def plot_single_ir_crossing(
    axis: Axes,
    plot_df_b1: DataFrame,
    plot_df_b2: DataFrame,
    plot_column: str,
    scaling: float = 1,
    xlabel: str | None = None,
    ylabel: str | None = None,
    title: str | None = None,
) -> None:
    """
    .. versionadded:: 1.0.0

    Plots the X or Y orbit for the IR on the given axis.

    Warning
    -------
        This function assumes the provided the *plot_df_b1* and
        *plot_df_b2* are already centered at 0 on the IP point!

    Parameters
    ----------
    axis : matplotlib.axes.Axes
        The `~matplotlib.axes.Axes` on which to plot.
    plot_df_b1 : pd.DataFrame | tfs.TfsDataFrame
        The ``TWISS`` dataframe of the IR zone for beam 1 of the LHC,
        centered on 0 at IP position (this can be achieved very simply
        with ``df.s = df.s - ip_s``).
    plot_df_b2 : pd.DataFrame | tfs.TfsDataFrame
        The ``TWISS`` dataframe of the IR zone for beam 2 of the LHC,
        centered on 0 at IP position (this can be achieved very simply
        with ``df.s = df.s - ip_s``).
    plot_column : str
        Which column (should be ``x`` or ``y``) to plot for the orbit.
    scaling : float
        Scaling factor to apply to the plotted data. Defaults to 1 (no
        change of data).
    xlabel : str, optional
        If given, will be used for the ``xlabel`` of the axis.
    ylabel : str, optional
        If given, will be used for the ``ylabel`` of the axis.
    title : str, optional
        If given, will be used for the ``title`` of the axis.

    Example
    -------
        .. code-block:: python

            plot_single_ir_crossing(
                plt.gca(),
                b1_df,
                b2_df,
                plot_column="x",
                scaling=1e3,
                ylabel="Orbit X $[mm]$",
            )
    """
    logger.trace(f"Plotting orbit '{plot_column}'")
    axis.plot(plot_df_b1.s, plot_df_b1[plot_column] * scaling, "bo", ls="-", mfc="none", alpha=0.8, label="Beam 1")
    axis.plot(plot_df_b2.s, plot_df_b2[plot_column] * scaling, "ro", ls="-", mfc="none", alpha=0.8, label="Beam 2")
    axis.set_ylabel(ylabel)
    axis.set_xlabel(xlabel)
    axis.set_title(title)
    axis.legend()


# ----- Helpers ----- #


def _highlight_mbx_and_mqx(axis: Axes, plot_df: DataFrame | TfsDataFrame, ip: int, **kwargs) -> None:
    """
    .. versionadded:: 1.0.0

    Plots colored pacthes highlighting zones with ``MBX`` and ``MQX``
    elements in a twin of the given axis.

    Warning
    -------
        This function assumes the provided *plot_df* is already
        centered at 0 on the IP point!

    Parameters
    ----------
    axis : matplotlib.axes.Axes
        The `~matplotlib.axes.Axes` to twin before adding patches.
    plot_df : pd.DataFrame | tfs.TfsDataFrame
        The ``TWISS`` dataframe of the IR zone, centered on 0 at
        the IP position (simply done with ``df.s = df.s - ip_s``).
    ip : int
        The IP number of the wanted IR in which to highlight elements
        positions.
    **kwargs
        Any keyword argument is given to the `~matplotlib.axes.Axes.axvspan`
        method called for each patch.
    """
    left_ir = plot_df.query("s < 0")  # no need to copy, we don't touch data
    right_ir = plot_df.query("s > 0")  # no need to copy, we don't touch data

    logger.trace("Determining MBX areas left and right of IP")
    left_mbx_lim = (
        left_ir[left_ir.name.str.contains("mbx")].s.min(),
        left_ir[left_ir.name.str.contains("mbx")].s.max(),
    )
    right_mbx_lim = (
        right_ir[right_ir.name.str.contains("mbx")].s.min(),
        right_ir[right_ir.name.str.contains("mbx")].s.max(),
    )

    logger.trace("Determining MQX areas left and right of IP")
    left_mqx_lim = (
        left_ir[left_ir.name.str.contains("mqx")].s.min(),
        left_ir[left_ir.name.str.contains("mqx")].s.max(),
    )
    right_mqx_lim = (
        right_ir[right_ir.name.str.contains("mqx")].s.min(),
        right_ir[right_ir.name.str.contains("mqx")].s.max(),
    )

    logger.trace("Highlighting MBX and MQX areas on a twin axis")
    patches_axis = axis.twinx()
    patches_axis.get_yaxis().set_visible(False)
    patches_axis.axvspan(*left_mbx_lim, color="orange", lw=2, alpha=0.2, label="MBX", **kwargs)
    patches_axis.axvspan(*left_mqx_lim, color="grey", lw=2, alpha=0.2, label="MQX", **kwargs)
    patches_axis.axvline(x=0, color="grey", ls="--", label=f"IP{ip}")
    patches_axis.axvspan(*right_mqx_lim, color="grey", lw=2, alpha=0.2, **kwargs)  # no label duplication
    patches_axis.axvspan(*right_mbx_lim, color="orange", lw=2, alpha=0.2, **kwargs)  # no label duplication
    patches_axis.legend(loc=4)
