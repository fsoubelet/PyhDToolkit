"""
Module cpymadtools.plotters
---------------------------

Created on 2019.12.08
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions to plot different output results from a cpymad.madx.Madx object's
simulation results.
"""
from functools import partial
from pathlib import Path
from typing import Dict, List, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tfs

from cpymad.madx import Madx
from loguru import logger
from matplotlib import colors as mcolors

from pyhdtoolkit.cpymadtools.latwiss import _plot_machine_layout
from pyhdtoolkit.models.beam import BeamParameters
from pyhdtoolkit.optics.twiss import courant_snyder_transform
from pyhdtoolkit.utils.defaults import PLOT_PARAMS

plt.rcParams.update(PLOT_PARAMS)

COLORS_DICT = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
BY_HSV = sorted(
    (tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name) for name, color in COLORS_DICT.items()
)
SORTED_COLORS = [name for hsv, name in BY_HSV]


class AperturePlotter:
    """A class to plot the aperture of your machine as determined by `MAD-X`'s `APERTURE` command.
    """

    @staticmethod
    def plot_aperture(
        madx: Madx,
        title: str,
        figsize: Tuple[int, int] = (18, 11),
        savefig: str = None,
        xoffset: float = 0,
        xlimits: Tuple[float, float] = None,
        plot_dipoles: bool = True,
        plot_quadrupoles: bool = True,
        plot_bpms: bool = False,
        aperture_ylim: Tuple[float, float] = None,
        k0l_lim: Tuple[float, float] = (-0.25, 0.25),
        k1l_lim: Tuple[float, float] = (-0.08, 0.08),
        k2l_lim: Tuple[float, float] = None,
        color: str = None,
        **kwargs,
    ) -> matplotlib.figure.Figure:
        """
        Provided with an active `cpymad` instance after having ran a script, will create a plot representing
        nicely the lattice layout and the aperture tolerance across the machine. Beware: this function
        assumes the user has previously made a call to the `APERTURE` command in `MAD-X`.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            title (str): title of your plot.
            figsize (Tuple[int, int]): size of the figure, defaults to (18, 1).
            savefig (str): will save the figure if this is not None, using the string value passed.
            xoffset (float): An offset applied to the S coordinate before plotting. This is useful is you want
                to center a plot around a specific point or element, which would then become located at s = 0.
                Beware this offset is applied before applying the `xlimits`. Offset defaults to 0 (no change).
            xlimits (Tuple[float, float]): will implement xlim (for the s coordinate) if this is
                not None, using the tuple passed.
            plot_dipoles (bool): if True, dipole patches will be plotted on the layout subplot of
                the figure. Defaults to True. Dipoles are plotted in blue.
            plot_quadrupoles (bool): if True, quadrupole patches will be plotted on the layout
                subplot of the figure. Defaults to True. Quadrupoles are plotted in red.
            plot_bpms (bool): if True, additional patches will be plotted on the layout subplot to represent
                Beam Position Monitors. BPMs are plotted in dark grey.
            aperture_ylim (Tuple[float, float]): vertical axis limits for the aperture values. Defaults to
                `None`, to be determined by matplotlib based on the provided values.
            k0l_lim (Tuple[float, float]): vertical axis limits for the k0l values used for the
                height of dipole patches. Defaults to (-0.25, 0.25).
            k1l_lim (Tuple[float, float]): vertical axis limits for the k1l values used for the
                height of quadrupole patches. Defaults to (-0.08, 0.08).
            k2l_lim (Tuple[float, float]): if given, sextupole patches will be plotted on the layout subplot of
                the figure, and the provided values act as vertical axis limits for the k2l values used for the
                height of sextupole patches.
            color (str): the color argument given to the aperture lines. Defaults to `None`, and should be
                the first color in your `rcParams`'s cycler.

        Keyword Args:
            Any keyword argument to be transmitted to `_plot_machine_layout`, later on to `plot_lattice_series`
            and then `matplotlib.patches.Rectangle`, such as lw etc.

        WARNING:
            Currently the function tries to plot legends for the different layout patches. The position of the
            different legends has been hardcoded in corners and might require users to tweak the axis limits
            (through `k0l_lim`, `k1l_lim` and `k2l_lim`) to ensure legend labels and plotted elements don't
            overlap.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        # pylint: disable=too-many-arguments
        logger.info("Plotting aperture limits and machine layout")
        logger.debug("Getting Twiss dataframe from cpymad")
        madx.command.twiss(centre=True)
        twiss_df: pd.DataFrame = madx.table.twiss.dframe().copy()
        aperture_df = pd.DataFrame.from_dict(dict(madx.table.aperture))  # slicing -> issues with .dframe()

        # Restrict the span of twiss_df to avoid plotting all elements then cropping when xlimits is given
        twiss_df.s = twiss_df.s - xoffset
        aperture_df.s = aperture_df.s - xoffset
        xlimits = (twiss_df.s.min(), twiss_df.s.max()) if xlimits is None else xlimits
        twiss_df = twiss_df[twiss_df.s.between(*xlimits)] if xlimits else twiss_df
        aperture_df = aperture_df[aperture_df.s.between(*xlimits)] if xlimits else aperture_df

        # Create a subplot for the lattice patches (takes a third of figure)
        figure = plt.figure(figsize=figsize)
        quadrupole_patches_axis = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
        _plot_machine_layout(
            madx,
            quadrupole_patches_axis=quadrupole_patches_axis,
            title=title,
            xoffset=xoffset,
            xlimits=xlimits,
            plot_dipoles=plot_dipoles,
            plot_quadrupoles=plot_quadrupoles,
            plot_bpms=plot_bpms,
            k0l_lim=k0l_lim,
            k1l_lim=k1l_lim,
            k2l_lim=k2l_lim,
            **kwargs,
        )

        # Plotting aperture values on remaining two thirds of the figure
        logger.debug("Plotting aperture values")
        aperture_axis = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=2, sharex=quadrupole_patches_axis)
        aperture_axis.plot(
            aperture_df.s, aperture_df.n1, marker=".", ls="-", lw=0.5, color=color, label="Aperture Limits"
        )
        aperture_axis.fill_between(
            aperture_df.s, aperture_df.n1, aperture_df.n1.max(), interpolate=True, color=color
        )
        aperture_axis.legend
        aperture_axis.set_ylabel(r"$n_{1} \ [\sigma]$")
        aperture_axis.set_xlabel("$S \ [m]$")

        if aperture_ylim:
            logger.debug("Setting ylim for aperture plot")
            aperture_axis.set_ylim(aperture_ylim)

        if xlimits:
            logger.debug("Setting xlim for longitudinal coordinate")
            plt.xlim(xlimits)

        if savefig:
            logger.info(f"Saving latwiss plot as {savefig}")
            plt.savefig(savefig)
        return figure


class BeamEnvelopePlotter:
    """
    A class to plot the estimated beam envelope of your machine.
    """

    @staticmethod
    def plot_envelope(
        madx: Madx,
        beam_params: BeamParameters,
        figsize: Tuple[int, int] = (13, 20),
        xlimits: Tuple[float, float] = None,
        hplane_ylim: Tuple[float, float] = (-0.12, 0.12),
        vplane_ylim: Tuple[float, float] = (-0.12, 0.12),
        savefig: str = None,
    ) -> matplotlib.figure.Figure:
        """
        Provided with an active `cpymad` instance after having ran a script, plots an estimation of the beam
        stay-clear enveloppe in your machine, as well as an estimation of the aperture limits.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            beam_params (BeamParameters): a validated BeamParameters object from
                `pyhdtoolkit.optics.beam.compute_beam_parameters`.
            figsize (Tuple[int, int]): size of the figure, defaults to (13, 20).
            xlimits (Tuple[float, float]): will implement xlim (for the s coordinate) if this is
                not None, using the tuple passed.
            hplane_ylim (Tuple[float, float]): the y limits for the horizontal plane plot (so
                that machine geometry doesn't make the  plot look shrinked). Defaults to (-0.12, 0.12).
            vplane_ylim (Tuple[float, float]): the y limits for the vertical plane plot (so that
                machine geometry doesn't make the plot look shrinked). Defaults to (-0.12, 0.12).
            savefig (str): will save the figure if this is not None, using the string value passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        # pylint: disable=too-many-arguments
        # We need to interpolate in order to get high resolution along the S direction
        logger.info("Plotting estimated machine aperture and beam envelope")
        logger.debug("Running interpolation in MAD-X")
        madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
        madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
        madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
        madx.command.select(flag="interpolate", class_="rbend", slice_=10, range_="#s/#e")
        madx.command.twiss()

        logger.trace("Getting Twiss dframe from MAD-X")
        twiss_hr: pd.DataFrame = madx.table.twiss.dframe().copy()
        twiss_hr["betatronic_envelope_x"] = np.sqrt(twiss_hr.betx * beam_params.eg_y_m)
        twiss_hr["betatronic_envelope_y"] = np.sqrt(twiss_hr.bety * beam_params.eg_y_m)
        twiss_hr["dispersive_envelope_x"] = twiss_hr.dx * beam_params.deltap_p
        twiss_hr["dispersive_envelope_y"] = twiss_hr.dy * beam_params.deltap_p
        twiss_hr["envelope_x"] = np.sqrt(
            twiss_hr.betatronic_envelope_x ** 2 + (twiss_hr.dx * beam_params.deltap_p) ** 2
        )
        twiss_hr["envelope_y"] = np.sqrt(
            twiss_hr.betatronic_envelope_y ** 2 + (twiss_hr.dy * beam_params.deltap_p) ** 2
        )
        machine = twiss_hr[twiss_hr.apertype == "ellipse"]

        figure = plt.figure(figsize=figsize)
        logger.debug("Plotting the horizontal aperture")
        axis1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=1)
        axis1.plot(twiss_hr.s, twiss_hr.envelope_x, color="b")
        axis1.plot(twiss_hr.s, -twiss_hr.envelope_x, color="b")
        axis1.fill_between(twiss_hr.s, twiss_hr.envelope_x, -twiss_hr.envelope_x, color="b", alpha=0.25)
        axis1.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_x, -3 * twiss_hr.envelope_x, color="b", alpha=0.25
        )
        axis1.fill_between(machine.s, machine.aper_1, machine.aper_1 * 100, color="k", alpha=0.5)
        axis1.fill_between(machine.s, -machine.aper_1, -machine.aper_1 * 100, color="k", alpha=0.5)
        axis1.plot(machine.s, machine.aper_1, "k.-")
        axis1.plot(machine.s, -machine.aper_1, "k.-")
        axis1.set_xlim(xlimits)
        axis1.set_ylim(hplane_ylim)
        axis1.set_ylabel(r"$X \ [m]$")
        axis1.set_xlabel(r"$S \ [m]$")
        axis1.set_title(f"Horizontal aperture at {beam_params.pc_GeV} GeV/c")

        logger.debug("Plotting the vertical aperture")
        axis2 = plt.subplot2grid((3, 3), (1, 0), colspan=3, rowspan=1, sharex=axis1)
        axis2.plot(twiss_hr.s, twiss_hr.envelope_y, color="r")
        axis2.plot(twiss_hr.s, -twiss_hr.envelope_y, color="r")
        axis2.fill_between(twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25)
        axis2.fill_between(twiss_hr.s, twiss_hr.envelope_y, -twiss_hr.envelope_y, color="r", alpha=0.25)
        axis2.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25
        )
        axis2.fill_between(
            twiss_hr.s, 3 * twiss_hr.envelope_y, -3 * twiss_hr.envelope_y, color="r", alpha=0.25
        )
        axis2.fill_between(machine.s, machine.aper_2, machine.aper_2 * 100, color="k", alpha=0.5)
        axis2.fill_between(machine.s, -machine.aper_2, -machine.aper_2 * 100, color="k", alpha=0.5)
        axis2.plot(machine.s, machine.aper_2, "k.-")
        axis2.plot(machine.s, -machine.aper_2, "k.-")
        axis2.set_ylim(vplane_ylim)
        axis2.set_ylabel(r"$Y \ [m]$")
        axis2.set_xlabel(r"$S \ [m]$")
        axis2.set_title(f"Vertical aperture at {beam_params.pc_GeV} GeV/c")

        logger.debug("Plotting the stay-clear envelope")
        axis3 = plt.subplot2grid((3, 3), (2, 0), colspan=3, rowspan=1, sharex=axis1)
        axis3.plot(machine.s, machine.aper_1 / machine.envelope_x, ".-b", label="Horizontal plane")
        axis3.plot(machine.s, machine.aper_2 / machine.envelope_y, ".-r", label="Vertical plane")
        axis3.set_xlim(xlimits)
        axis3.set_ylabel("$n1$")
        axis3.set_xlabel(r"$S \ [m]$")
        axis3.legend(loc="best")
        axis3.set_title(f"Stay-clear envelope at {beam_params.pc_GeV} GeV/c")

        if savefig:
            logger.info(f"Saving aperture plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure


class CrossingSchemePlotter:
    """
    A class to plot LHC crossing schemes at provided IPs.
    """

    @staticmethod
    def _highlight_mbx_and_mqx(
        axis: matplotlib.axes.Axes, plot_df: Union[pd.DataFrame, tfs.TfsDataFrame], ip: int, **kwargs
    ) -> None:
        """
        Plot colored pacthes highlighting zones with MBX and MQX elements in a twin of the given axis.
        Assumes that the plot_df s already centered at 0 on the IP point!

        Args:
            axis (matplotlib.axes.Axes): the axis to twin and then on which to add patches.
            plot_df (Union[pd.DataFrame, tfs.TfsDataFrame]): TWISS dataframe of the IR zone, centered on 0
                at IP position (simply done with `df.s = df.s - ip_s`).
            ip (int): the IP number of the given IR.

        Keyword Args:
            Any keyword argument is given to the `axis.axvspan` method called for each patch.
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
        patches_axis.axvspan(*left_mbx_lim, color="orange", lw=2, alpha=0.2, label="MBX")
        patches_axis.axvspan(*left_mqx_lim, color="grey", lw=2, alpha=0.2, label="MQX")
        patches_axis.axvline(x=0, color="grey", ls="--", label=f"IP{ip}")
        patches_axis.axvspan(*right_mqx_lim, color="grey", lw=2, alpha=0.2)  # no label duplication
        patches_axis.axvspan(*right_mbx_lim, color="orange", lw=2, alpha=0.2)  # no label duplication
        patches_axis.legend(loc=4)

    @staticmethod
    def _plot_crossing_in_ir(
        axis: matplotlib.axes.Axes,
        plot_df_b1: pd.DataFrame,
        plot_df_b2: pd.DataFrame,
        plot_column: str,
        scaling: float = 1,
        ylabel: str = None,
        xlabel: str = None,
        title: str = None,
    ) -> None:
        """
        Plot the X or Y orbit for the IR on the given axis. Assumes that the plot_df_b1 and plot_df_b2
        are already centered at 0 on the IP point!

        Args:
            axis (matplotlib.axes.Axes): the axis on which to plot.
            plot_df_b1 (Union[pd.DataFrame, tfs.TfsDataFrame]): TWISS dataframe of the IR zone for beam 1
            of the LHC, centered on 0 at IP position (simply done with `df.s = df.s - ip_s`).
            plot_df_b2 (Union[pd.DataFrame, tfs.TfsDataFrame]): TWISS dataframe of the IR zone for beam 2
            of the LHC, centered on 0 at IP position (simply done with `df.s = df.s - ip_s`).
            plot_column (str): which column (should be `x` or `y`) to plot for the orbit.
            scaling (float): scaling factor to apply to the plotted data. Defaults to 1 (no change of data).
            xlabel (str): if given, will be used for the `xlabel` of the axis. Defaults to `None`.
            ylabel (str): if given, will be used for the `ylabel` of the axis. Defaults to `None`.
            title (str): if given, will be used for the `title` of the axis. Defaults to `None`.
        """
        logger.trace(f"Plotting orbit '{plot_column}'")
        axis.plot(
            plot_df_b1.s,
            plot_df_b1[plot_column] * scaling,
            "bo",
            ls="-",
            mfc="none",
            alpha=0.8,
            label="Beam 1",
        )
        axis.plot(
            plot_df_b2.s,
            plot_df_b2[plot_column] * scaling,
            "ro",
            ls="-",
            mfc="none",
            alpha=0.8,
            label="Beam 2",
        )
        axis.set_ylabel(ylabel)
        axis.set_xlabel(xlabel)
        axis.set_title(title)
        axis.legend()

    @staticmethod
    def plot_two_lhc_ips_crossings(
        madx: Madx,
        first_ip: int,
        second_ip: int,
        figsize: Tuple[int, int] = (18, 12),
        ir_limit: float = 275,
        savefig: str = None,
    ) -> matplotlib.figure.Figure:
        """
        Provided with an active `cpymad.madx.Madx` instance after having ran a script, will create a plot
        representing nicely the crossing schemes at two provided IPs. This assumes the appropriate LHC
        sequence and opticsfile have been loaded, and both `lhcb1` and `lhcb2` beams are defined. It is
        very recommended to re-cycle the sequences from a point which is not an IP

        WARNING: This function will get TWISS tables for both beams, which means it will `USE` both the
        `lhcb1` and `lhcb2` sequences, erasing previously defined errors or orbit corrections. The second
        sequence `USE` will be called on is `lhcb2`, which may not be the one you were using before. Please
        re-`use` your wanted sequence after calling this function!

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            first_ip (int): the first of the two IPs to plot crossing schemes for.
            second_ip (int): the second of the two IPs to plot crossing schemes for.
            figsize (Tuple[int, int]): size of the figure, defaults to (18, 12).
            ir_limit (float): the amount of meters to keep left and right of the IP point. Will also
                determine the xlimits of the plots. Defaults to 275.
            savefig (str): will save the figure if this is not `None`, using the string value passed.
                Defaults to `None`.

        Returns:
            The figure on which the crossing schemes are drawn. One crossing scheme is plotted per IP and
            per plane (orbit X and orbit Y). The underlying axes can be accessed with 'fig.get_axes()'.
            Eventually saves the figure as a file.
        """
        logger.warning("You should re-call the 'USE' command on your wanted sequence after this!")
        # ----- Getting Twiss table dframe for each beam ----- #
        logger.debug("Getting TWISS table for LHCB1")
        madx.use(sequence="lhcb1")
        madx.command.twiss(centre=True)
        twiss_df_b1 = madx.table.twiss.dframe().copy()

        logger.debug("Getting TWISS table for LHCB2")
        madx.use(sequence="lhcb2")
        madx.command.twiss(centre=True)
        twiss_df_b2 = madx.table.twiss.dframe().copy()

        logger.trace("Determining exact locations of IP points")
        first_ip_s = twiss_df_b1.s[f"ip{first_ip}"]
        second_ip_s = twiss_df_b1.s[f"ip{second_ip}"]

        # ----- Plotting figure ----- #
        logger.info(f"Plotting crossing schemes for IP{first_ip} and IP{second_ip}")
        figure, axes = plt.subplots(2, 2, figsize=figsize)

        logger.debug(f"Plotting for IP{first_ip}")
        b1_plot = twiss_df_b1[twiss_df_b1.s.between(first_ip_s - ir_limit, first_ip_s + ir_limit)].copy()
        b2_plot = twiss_df_b2[twiss_df_b2.s.between(first_ip_s - ir_limit, first_ip_s + ir_limit)].copy()
        b1_plot.s = b1_plot.s - first_ip_s
        b2_plot.s = b2_plot.s - first_ip_s

        CrossingSchemePlotter._plot_crossing_in_ir(
            axes[0][0],
            b1_plot,
            b2_plot,
            plot_column="x",
            scaling=1e3,
            ylabel="Orbit X $[mm]$",
            title=f"IP{first_ip} Crossing Schemes",
        )
        CrossingSchemePlotter._plot_crossing_in_ir(
            axes[1][0],
            b1_plot,
            b2_plot,
            plot_column="y",
            scaling=1e3,
            ylabel="Orbit Y $[mm]$",
            xlabel=f"Distance to IP{first_ip} $[m]$",
        )
        CrossingSchemePlotter._highlight_mbx_and_mqx(axes[0][0], b1_plot, f"IP{first_ip}")
        CrossingSchemePlotter._highlight_mbx_and_mqx(axes[1][0], b1_plot, f"IP{first_ip}")

        logger.debug(f"Plotting for IP{second_ip}")
        b1_plot = twiss_df_b1[twiss_df_b1.s.between(second_ip_s - ir_limit, second_ip_s + ir_limit)].copy()
        b2_plot = twiss_df_b2[twiss_df_b2.s.between(second_ip_s - ir_limit, second_ip_s + ir_limit)].copy()
        b1_plot.s = b1_plot.s - second_ip_s
        b2_plot.s = b2_plot.s - second_ip_s

        CrossingSchemePlotter._plot_crossing_in_ir(
            axes[0][1],
            b1_plot,
            b2_plot,
            plot_column="x",
            scaling=1e3,
            title=f"IP{second_ip} Crossing Schemes",
        )
        CrossingSchemePlotter._plot_crossing_in_ir(
            axes[1][1],
            b1_plot,
            b2_plot,
            plot_column="y",
            scaling=1e3,
            xlabel=f"Distance to IP{second_ip} $[m]$",
        )
        CrossingSchemePlotter._highlight_mbx_and_mqx(axes[0][1], b1_plot, f"IP{second_ip}")
        CrossingSchemePlotter._highlight_mbx_and_mqx(axes[1][1], b1_plot, f"IP{second_ip}")
        plt.tight_layout()

        if savefig:
            logger.info(f"Saving crossing schemes for IP{first_ip} and IP{second_ip} plot as '{savefig}'")
            figure.savefig(savefig)
        return figure


class DynamicAperturePlotter:
    """
    This is currently badly named, and will change in the future.
    """

    @staticmethod
    def plot_dynamic_aperture(
        x_coords: np.ndarray, y_coords: np.ndarray, n_particles: int, savefig: str = None
    ) -> matplotlib.figure.Figure:
        """
        Plots a visual aid for the dynamic aperture after a tracking. Initial amplitudes are on the
        vertical axis, and the turn at which they were lost is in the horizontal axis.

        Args:
            x_coords (np.ndarray): numpy array of horizontal coordinates over turns.
            y_coords (np.ndarray): numpy array of vertical coordinates over turns.
            n_particles (int): number of particles simulated.
            savefig (str): will save the figure if this is not None, using the string value passed.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        logger.info(f"Plotting the '{len(x_coords)} turns' aperture")
        figure = plt.figure(figsize=(12, 7))
        turn_lost_at = []
        amp_lost = []

        logger.trace("Determining turns at which particles have been lost")
        for particle in range(n_particles):
            amp_lost.append(x_coords[particle][0] ** 2 + y_coords[particle][0] ** 2)  # initial amplitude
            # this is ok since once coordinates go to `nan` they don't come back, particle is lost
            turn_lost_at.append(
                min(
                    pd.Series(x_coords[particle]).last_valid_index()
                    + 2,  # starts at 0, lost after last valid
                    pd.Series(y_coords[particle]).last_valid_index()
                    + 2,  # starts at 0, lost after last valid
                )
            )
        turn_lost_at = np.array(turn_lost_at)
        amp_lost = np.array(amp_lost)

        plt.scatter(turn_lost_at, amp_lost * 1000, linewidths=0.7, c="darkblue", marker=".")
        plt.title("Amplitudes lost over turns")
        plt.xlabel("Number of Turns Survived")
        plt.ylabel("Initial amplitude $[mm]$")

        if savefig:
            logger.info(f"Saving dynamic aperture plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure


class PhaseSpacePlotter:
    """
    A class to plot Courant-Snyder coordinates phase space.
    """

    @staticmethod
    def plot_courant_snyder_phase_space(
        madx: Madx,
        u_coordinates: np.ndarray,
        pu_coordinates: np.ndarray,
        savefig: str = None,
        size: Tuple[int, int] = (16, 8),
        plane: str = "Horizontal",
    ) -> matplotlib.figure.Figure:
        """
        Plots the Courant-Snyder phase space of a particle distribution when provided by position
        and momentum coordinates for a specific plane.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            u_coordinates (np.ndarray): numpy array of particles' coordinates for the given plane. Here
                u_coordinates[0] should be all tracked coordinates for the first particle and so on.
            pu_coordinates (np.ndarray): numpy array of particles' momentum coordinates for the
                given plane.Here pu_coordinates[0] should be all tracked momenta for the first particle
                and so on.
            savefig (str): will save the figure if this is not None, using the string value passed.
            size (Tuple[int, int]): the wanted matplotlib figure size. Defaults to (16, 8).
            plane (str): the physical plane to plot. Defaults to 'Horizontal'.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        if plane.upper() not in ("HORIZONTAL", "VERTICAL"):
            logger.error(f"Plane should be either Horizontal or Vertical but '{plane}' was given")
            raise ValueError("Invalid plane value")

        logger.info("Plotting phase space for normalized Courant-Snyder coordinates")
        figure = plt.figure(figsize=size)
        plt.title("Courant-Snyder Phase Space")

        # Getting the twiss parameters for the P matrix to compute Courant-Snyder coordinates
        logger.debug("Getting Twiss functions from MAD-X")
        alpha = madx.table.twiss.alfx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.alfy[0]
        beta = madx.table.twiss.betx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.bety[0]

        logger.debug(f"Plotting phase space for the {plane.lower()} plane")
        for index, _ in enumerate(u_coordinates):
            logger.trace(f"Getting and plotting Courant-Snyder coordinates for particle {index}")
            u = np.array([u_coordinates[index], pu_coordinates[index]])
            u_bar = courant_snyder_transform(u, alpha, beta)
            plt.scatter(u_bar[0, :] * 1e3, u_bar[1, :] * 1e3, s=0.1, c="k")
            if plane.upper() == "HORIZONTAL":
                plt.xlabel(r"$\bar{x} \ [mm]$")
                plt.ylabel(r"$\bar{px} \ [mrad]$")
            else:
                plt.xlabel(r"$\bar{y} \ [mm]$")
                plt.ylabel(r"$\bar{py} \ [mrad]$")
            plt.axis("Equal")

        if savefig:
            logger.info(f"Saving Courant-Snyder phase space plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure

    @staticmethod
    def plot_courant_snyder_phase_space_colored(
        madx: Madx,
        u_coordinates: np.ndarray,
        pu_coordinates: np.ndarray,
        savefig: str = None,
        size: Tuple[int, int] = (16, 8),
        plane: str = "Horizontal",
    ) -> matplotlib.figure.Figure:
        """
        Plots the Courant-Snyder phase space of a particle distribution when provided by position
        and momentum coordinates for a specific plane. Each particle trajectory has its own color on
        the plot, within the limit of pyplot's 156 named colors. The sequence repeats after the
        156th color.

        Args:
            madx (cpymad.madx.Madx): an instanciated cpymad Madx object.
            u_coordinates (np.ndarray): numpy array of particles' coordinates for the given plane. Here
                u_coordinates[0] should be all tracked coordinates for the first particle and so on.
            pu_coordinates (np.ndarray): numpy array of particles' momentum coordinates for the
                given plane.Here pu_coordinates[0] should be all tracked momenta for the first particle
                and so on.
            savefig (str): will save the figure if this is not None, using the string value passed.
            size (Tuple[int, int]): the wanted matplotlib figure size. Defaults to (16, 8).
            plane (str): the physical plane to plot. Defaults to 'Horizontal'.

        Returns:
             The figure on which the plots are drawn. The underlying axes can be accessed with
             'fig.get_axes()'. Eventually saves the figure as a file.
        """
        if plane.upper() not in ("HORIZONTAL", "VERTICAL"):
            logger.error(f"Plane should be either horizontal or vertical but '{plane}' was given")
            raise ValueError("Invalid plane value")

        # Getting a sufficiently long array of colors to use
        colors = int(np.floor(len(u_coordinates) / 100)) * SORTED_COLORS
        while len(colors) > len(u_coordinates):
            colors.pop()

        logger.info("Plotting colored phase space for normalized Courant-Snyder coordinates")
        figure = plt.figure(figsize=size)
        plt.title("Courant-Snyder Phase Space")

        # Getting the twiss parameters for the P matrix to compute Courant-Snyder coordinates
        logger.debug("Getting Twiss functions from MAD-X")
        alpha = madx.table.twiss.alfx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.alfy[0]
        beta = madx.table.twiss.betx[0] if plane.upper() == "HORIZONTAL" else madx.table.twiss.bety[0]

        logger.debug(f"Plotting colored phase space for the {plane.lower()} plane")
        for index, _ in enumerate(u_coordinates):
            logger.trace(f"Getting and plotting Courant-Snyder coordinates for particle {index}")
            u = np.array([u_coordinates[index], pu_coordinates[index]])
            u_bar = courant_snyder_transform(u, alpha, beta)
            plt.scatter(u_bar[0, :] * 1e3, u_bar[1, :] * 1e3, s=0.1, c=colors[index])
            if plane.upper() == "HORIZONTAL":
                plt.xlabel(r"$\bar{x} \ [mm]$")
                plt.ylabel(r"$\bar{px} \ [mrad]$")
            else:
                plt.xlabel(r"$\bar{y} \ [mm]$")
                plt.ylabel(r"$\bar{py} \ [mrad]$")
            plt.axis("Equal")

        if savefig:
            logger.info(f"Saving colored Courant-Snyder phase space plot at '{Path(savefig).absolute()}'")
            plt.savefig(Path(savefig))
        return figure


class TuneDiagramPlotter:
    """
    A class to plot a blank tune diagram with Farey sequences, as well as your working points.
    """

    order_to_alpha: Dict[int, float] = {1: 1, 2: 0.75, 3: 0.65, 4: 0.55, 5: 0.45, 6: 0.35}
    order_to_rgb: Dict[int, np.ndarray] = {
        1: np.array([152, 52, 48]) / 255,  # a brown
        2: np.array([57, 119, 175]) / 255,  # a blue
        3: np.array([239, 133, 54]) / 255,  # an orange
        4: np.array([82, 157, 62]) / 255,  # a green
        5: np.array([197, 57, 50]) / 255,  # a red
        6: np.array([141, 107, 184]) / 255,  # a purple
    }
    order_to_linestyle: Dict[int, str] = {
        1: "solid",
        2: "solid",
        3: "solid",
        4: "dashed",
        5: "dashed",
        6: "dashed",
    }
    order_to_linewidth: Dict[int, float] = {1: 2, 2: 1.75, 3: 1.5, 4: 1.25, 5: 1, 6: 0.75}
    order_to_label: Dict[int, str] = {
        1: "1st order",
        2: "2nd order",
        3: "3rd order",
        4: "4th order",
        5: "5th order",
        6: "6th order",
    }

    @staticmethod
    def farey_sequence(order: int) -> List[Tuple[int, int]]:
        """
        Returns the n-th farey_sequence sequence, ascending. Original code from Rogelio Tomás (see Numerical
        Methods 2018 CAS proceedings: https://arxiv.org/abs/2006.10661).

        Args:
            order (int): the order up to which we want to calculate the sequence.

        Returns:
            The sequence as a list of plottable 2D points.
        """
        logger.trace(f"Computing Farey sequence for order {order}")
        seq = [[0, 1]]
        a, b, c, d = 0, 1, 1, order
        while c <= order:
            k = int((order + b) / d)
            a, b, c, d = c, d, k * c - a, k * d - b
            seq.append((a, b))
        return seq

    @staticmethod
    def _plot_resonance_lines_for_order(order: int, axis: matplotlib.axes.Axes, **kwargs) -> None:
        """
        Plot resonance lines from farey sequences of the given order on the current figure.

        Args:
            order (int): the order of the resonance.
            axis (matplotlib.axes.Axes): the axis on which to plot the resonance lines.

        Keyword Args:
            Any keyword argument is given to plt.plot().
        """
        order_label = TuneDiagramPlotter.order_to_label[order]
        logger.debug(f"Plotting {order_label} resonance lines")
        axis.plot([], [], label=order_label, **kwargs)  # to avoid legend duplication in loops below

        x, y = np.linspace(0, 1, 1000), np.linspace(0, 1, 1000)
        farey_sequences = TuneDiagramPlotter.farey_sequence(order)
        clip = partial(np.clip, a_min=0, a_max=1)  # clip all values to plot to [0, 1]

        for node in farey_sequences:
            h, k = node  # Node h/k on the axes
            for sequence in farey_sequences:
                p, q = sequence
                a = float(k * p)  # Resonance line a*Qx + b*Qy = c (linked to p/q)
                if a > 0:
                    b, c = float(q - k * p), float(p * h)
                    axis.plot(x, clip(c / a - x * b / a), **kwargs)
                    axis.plot(x, clip(c / a + x * b / a), **kwargs)
                    axis.plot(clip(c / a - x * b / a), y, **kwargs)
                    axis.plot(clip(c / a + x * b / a), y, **kwargs)
                    axis.plot(clip(c / a - x * b / a), 1 - y, **kwargs)
                    axis.plot(clip(c / a + x * b / a), 1 - y, **kwargs)
                if q == k and p == 1:  # FN elements below 1/k
                    break

    @staticmethod
    def plot_blank_tune_diagram(
        title: str = "",
        legend_title: str = None,
        max_order: int = 6,
        differentiate_orders: bool = False,
        figsize: Tuple[float, float] = (12, 12),
        **kwargs,
    ) -> matplotlib.figure.Figure:
        """
        Plotting the tune diagram up to the 6th order. Original code from Rogelio Tomás.
        The first order lines make up the [(0, 0), (0, 1), (1, 1), (1, 0)] square and will only be seen
        when redefining the limits of the figure, which are by default [0, 1] on each axis.

        Args:
            title (str): title of your plot, to be given to the figure. Defaults to an empty string.
            legend_title (str): if given, will be used as the title of the plot's legend. If set to `None`,
                then creating a legend for the figure will not be done by this function and left up to the
                user's care (a call to `pyplot.legend` will do). Defaults to `None`.
            max_order (int): the order up to which to plot resonance lines for, should not exceed 6.
                Defaults to 6.
            differentiate_orders (bool): if `True`, the lines for each order will be of a different color.
                When set to False, there is still minimal differentation through alpha, linewidth and
                linestyle. Defaults to `False`.
            figsize (Tuple[int, int]): size of the figure, defaults to (12, 12).

        Keyword Args:
            Any keyword argument will be transmitted to the `_plot_resonance_lines_for_order` functino
            and later on to `pyplot.plot`. Be aware that `alpha`, `ls`, `lw`, `color` and `label` are
            already set by this function and providing them as kwargs might lead to errors.

        Returns:
             The figure on which resonance lines from farey sequences are drawn, up to the specified max
             order.
        """
        if max_order > 6 or max_order < 1:
            logger.error("Plotting is not supported outside of 1st-6th order (and not recommended)")
            raise ValueError("The 'max_order' argument should be between 1 and 6 included")

        logger.info(f"Plotting resonance lines up to {TuneDiagramPlotter.order_to_label[max_order]}")
        figure, axis = plt.subplots(figsize=figsize)

        for order in range(max_order, 0, -1):  # high -> low so most importants ones (low) are plotted on top
            alpha, ls, lw, rgb = (
                TuneDiagramPlotter.order_to_alpha[order],
                TuneDiagramPlotter.order_to_linestyle[order],
                TuneDiagramPlotter.order_to_linewidth[order],
                TuneDiagramPlotter.order_to_rgb[order] if differentiate_orders is True else "blue",
            )
            TuneDiagramPlotter._plot_resonance_lines_for_order(
                order, axis, alpha=alpha, ls=ls, lw=lw, color=rgb, **kwargs,
            )

        plt.title(title)
        axis.set_xlim([0, 1])
        axis.set_ylim([0, 1])
        plt.xlabel("$Q_{x}$")
        plt.ylabel("$Q_{y}$")

        if legend_title is not None:
            logger.debug("Adding legend with given title")
            plt.legend(title=legend_title)
        return figure
