import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.plotting.envelope import _interpolate_madx, plot_beam_envelope

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
mpl.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent / "inputs"
GUIDO_LATTICE = INPUTS_DIR / "madx" / "guido_lattice.madx"


def test_plot_enveloppe_raises_on_wrong_plane():
    madx = Madx(stdout=False)

    with pytest.raises(ValueError, match="Invalid 'plane' argument."):
        plot_beam_envelope(madx, "lhcb1", plane="invalid")


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_with_xlimits():
    with Madx(stdout=False) as madx:
        madx.call(str(GUIDO_LATTICE))
        _interpolate_madx(madx)  # let's interpolate for a smoother plot

        figure, ax = plt.subplots(figsize=(12, 7))
        # Let's plot 1 sigma and 2.5 sigma enveloppes
        plot_beam_envelope(madx, "cas19", "x", nsigma=1, xlimits=(200, 300), centre=True)
        plot_beam_envelope(madx, "cas19", "horizontal", nsigma=2.5, xlimits=(200, 300), centre=True)
        plt.setp(ax, xlabel="S [m]", ylabel="X [m]")
        plt.legend()
        return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_horizontal():
    with Madx(stdout=False) as madx:
        madx.call(str(GUIDO_LATTICE))

        figure, ax = plt.subplots(figsize=(12, 7))
        # Let's plot 1 sigma and 2.5 sigma enveloppes
        plot_beam_envelope(madx, "cas19", "x", nsigma=1)
        plot_beam_envelope(madx, "cas19", "horizontal", nsigma=2.5)
        plt.setp(ax, xlabel="S [m]", ylabel="X [m]")
        plt.legend()
        return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_vertical():
    with Madx(stdout=False) as madx:
        madx.call(str(GUIDO_LATTICE))

        figure, ax = plt.subplots(figsize=(12, 7))
        # Let's plot 1 sigma and 2.5 sigma enveloppes
        plot_beam_envelope(madx, "cas19", "y", nsigma=1, scale=1e3)
        plot_beam_envelope(madx, "cas19", "vertical", nsigma=2.5, scale=1e3)
        plt.setp(ax, xlabel="S [m]", ylabel="Y [mm]")
        plt.legend()
        return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_combined():
    with Madx(stdout=False) as madx:
        madx.call(str(GUIDO_LATTICE))
        figure, axes = plt.subplots(2, 1, sharex=True, figsize=(12, 10))

        # First let's plot 1 sigma and 2.5 sigma horizontal enveloppes
        plot_beam_envelope(madx, "cas19", "x", nsigma=1, scale=1e3, ax=axes[0])
        plot_beam_envelope(madx, "cas19", "horizontal", nsigma=2.5, scale=1e3, ax=axes[0])
        plt.setp(axes[0], ylabel="X [mm]")
        axes[0].legend()

        # Then plot 1 sigma and 2.5 sigma vertical enveloppes
        plot_beam_envelope(madx, "cas19", "y", nsigma=1, scale=1e3, ax=axes[1])
        plot_beam_envelope(madx, "cas19", "vertical", nsigma=2.5, scale=1e3, ax=axes[1])
        plt.setp(axes[1], xlabel="S [m]", ylabel="Y [mm]")
        axes[1].legend()

        return figure
