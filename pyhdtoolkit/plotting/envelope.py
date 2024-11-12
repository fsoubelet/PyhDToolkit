"""
.. _plotting-envelope:

Beam Enveloppe Plotters
-----------------------

Module with functions to create beam enveloppe plots
through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from loguru import logger

from pyhdtoolkit.plotting.utils import maybe_get_ax

if TYPE_CHECKING:
    from cpymad.madx import Madx


def plot_beam_envelope(
    madx: Madx,
    /,
    sequence: str,
    plane: str,
    nsigma: float = 1,
    scale: float = 1,
    xoffset: float = 0,
    xlimits: tuple[float, float] | None = None,
    **kwargs,
) -> None:
    """
    .. versionadded:: 1.2.0

    Draws the beam enveloppe around the beam orbit on the given
    *axis*. The enveloppe is determined from the active sequence's
    beam's parameters.

    One can find an example use of this function in the :ref:`beam
    enveloppe <demo-beam-enveloppe>` example gallery.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.
    sequence : str
        The name of the sequence to plot the beam enveloppe for, which
        should be the active sequence. Case insensitive.
    plane : str
        The physical plane to plot for, which should be either `x`,
        `horizontal`, `y` or `vertical`. Case insensitive.
    nsigma : float
        The standard deviation to use for the beam enveloppe calculation.
        For instance, providing a value of 3 will draw the 3 sigma beam
        enveloppe. Defaults to 1.
    scale : float
        A scaling factor to apply to the beam orbit and beam enveloppe,
        for the user to adjust to their wanted scale. Defaults to 1
        (meaning values are assumed in [m]).
    xoffset : float
        An offset applied to the ``S`` coordinate before plotting. This
        is useful if you want to center a plot around a specific point
        or element, which would then become located at :math:`s = 0`.
        Beware this offset is applied before applying the *xlimits*.
        Defaults to 0.
    xlimits : tuple[float, float], optional
        If given, will be used for the xlim (for the ``s`` coordinate),
        using the tuple passed.
    **kwargs
        Any keyword argument that can be given to the ``MAD-X``
        ``TWISS`` command. If either `ax` or `axis` is found in the
        kwargs, the corresponding value is used as the axis object to
        plot on.

    Raises
    ------
    ValueError
        If the *plane* argument is not one of `x`, `horizontal`,
        `y` or `vertical`.

    Examples
    --------

        .. code-block:: python

            fig, ax = plt.subplots(figsize=(10, 9))
            plot_beam_envelope(madx, "lhcb1", "x", nsigma=3)
            plt.show()

        In order to do the same plot but have all values in millimeters:

        .. code-block:: python

            fig, ax = plt.subplots(figsize=(10, 9))
            plot_beam_envelope(madx, "lhcb1", "x", nsigma=3, scale=1e3)
            plt.setp(ax, xlabel="S [m]", ylabel="X [mm]")
            plt.show()
    """
    # pylint: disable=too-many-arguments
    if plane.lower() not in ("x", "y", "horizontal", "vertical"):
        logger.error(f"'plane' argument should be 'x', 'horizontal', 'y' or 'vertical' not '{plane}'")
        msg = "Invalid 'plane' argument."
        raise ValueError(msg)

    logger.debug(f"Plotting machine orbit and {nsigma:.2f}sigma beam envelope")
    axis, kwargs = maybe_get_ax(**kwargs)

    logger.debug("Getting Twiss dframe from MAD-X")
    plane_letter = "x" if plane.lower() in ("x", "horizontal") else "y"
    twiss_df = madx.twiss(**kwargs).dframe()
    twiss_df.s = twiss_df.s - xoffset

    if xlimits is not None:
        axis.set_xlim(xlimits)
        twiss_df = twiss_df[twiss_df.s.between(*xlimits)]

    logger.debug(f"Extracting beam parameters for the '{sequence}' sequence")
    geom_emit = madx.sequence[sequence].beam[f"e{plane_letter}"]
    sige = madx.sequence[sequence].beam.sige
    orbit = twiss_df[plane_letter] * scale  # with scaling factor, by default 1

    logger.debug("Calculating beam enveloppe")
    one_sigma = np.sqrt(geom_emit * twiss_df[f"bet{plane_letter}"] + (sige * twiss_df[f"d{plane_letter}"]) ** 2)
    enveloppe = nsigma * one_sigma * scale  # with scaling factor, by default 1

    # Plot a line for the orbit, then fill between orbit + enveloppe and orbit - enveloppe
    logger.debug("Plotting orbit and beam enveloppe")
    alpha = np.clip(1 - (1 - np.exp(-nsigma / 2.35)), 0.05, 0.8)  # lighter shade for higher sigma
    plane_color = "b" if plane_letter == "x" else "r"  # blue for horizontal, red for vertical
    axis.plot(twiss_df.s, twiss_df[plane_letter], color=plane_color)
    axis.fill_between(
        twiss_df.s,
        orbit + enveloppe,
        orbit - enveloppe,
        alpha=alpha,
        color=plane_color,
        label=rf"{nsigma}$\sigma$",
    )


# ----- Helpers ----- #


def _interpolate_madx(madx: Madx, /) -> None:
    """
    Run interpolation on the provided MAD-X
    instance with default slice values.
    """
    logger.debug("Running interpolation in MAD-X")
    madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
    madx.command.select(flag="interpolate", class_="rbend", slice_=10, range_="#s/#e")
    madx.command.twiss()
