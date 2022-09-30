import pathlib

import matplotlib
import matplotlib.pyplot as plt
import pytest

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.plot.beamenvelope import plot_envelope, plot_stay_clear
from pyhdtoolkit.optics.beam import compute_beam_parameters

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR.parent.parent / "inputs"
GUIDO_LATTICE = INPUTS_DIR / "madx" / "guido_lattice.madx"


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_horizontal():
    beam_injection = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
    title = f"Horizontal Aperture at {beam_injection.pc_GeV} GeV/c"

    madx = Madx(stdout=False)
    madx.call(str(GUIDO_LATTICE))

    figure = plt.figure(figsize=(16, 9))
    plot_envelope(madx, beam_injection, ylimits=(-0.12, 0.12), title=title)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_vertical():
    beam_injection = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
    title = f"Vertical Aperture at {beam_injection.pc_GeV} GeV/c"

    madx = Madx(stdout=False)
    madx.call(str(GUIDO_LATTICE))

    figure = plt.figure(figsize=(16, 9))
    plot_envelope(madx, beam_injection, plane="vertical", ylimits=(-0.12, 0.12), title=title)
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_stay_clear():
    beam_injection = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
    title = f"Stay-Clear at {beam_injection.pc_GeV} GeV/c"
    l_cell = 20  # only plot first cell for this one, tests xlimits param

    madx = Madx(stdout=False)
    madx.call(str(GUIDO_LATTICE))

    figure = plt.figure(figsize=(16, 9))
    plot_stay_clear(
        madx,
        beam_injection,
        xlimits=(0, l_cell),
        title=title,
    )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_envelope_combined():
    beam_injection = compute_beam_parameters(1.9, en_x_m=5e-6, en_y_m=5e-6, deltap_p=2e-3)
    madx = Madx(stdout=False)
    madx.call(str(GUIDO_LATTICE))
    figure, axes = plt.subplots(3, 1, figsize=(18, 20))
    plot_envelope(
        madx,
        beam_injection,
        ylimits=(-0.12, 0.12),
        title=f"Horizontal aperture at {beam_injection.pc_GeV} GeV/c",
        axis=axes[0],
    )
    plot_envelope(
        madx,
        beam_injection,
        ylimits=(-0.12, 0.12),
        plane="vertical",
        title=f"Vertical aperture at {beam_injection.pc_GeV} GeV/c",
        axis=axes[1],
    )
    plot_stay_clear(madx, beam_injection, title=f"Stay-Clear at {beam_injection.pc_GeV} GeV/c", axis=axes[2])
    return figure
