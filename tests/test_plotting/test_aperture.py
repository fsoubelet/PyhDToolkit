import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from cpymad.madx import Madx

from pyhdtoolkit.plotting.aperture import plot_aperture, plot_physical_apertures

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
mpl.use("Agg")


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_aperture_cell_injection(_injection_aperture_tolerances_lhc_madx):
    madx = _injection_aperture_tolerances_lhc_madx
    madx.command.twiss(centre=True)

    figure = plt.figure(figsize=(18, 11))
    plot_aperture(
        madx,
        title="Arc 56 Cell, Injection Optics Aperture Tolerance",
        plot_bpms=True,
        xlimits=(14_084.5, 14_191.3),  # cell somewhere in arc 56
        aperture_ylim=(0, 25),
        k0l_lim=(-3e-2, 3e-2),
        k1l_lim=(-4e-2, 4e-2),
        k2l_lim=(-5e-2, 5e-2),
        color="brown",
    )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_aperture_ir5_collision(_collision_aperture_tolerances_lhc_madx):
    madx = _collision_aperture_tolerances_lhc_madx
    madx.command.twiss(centre=True)
    twiss_df = madx.table.twiss.dframe()
    ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

    figure = plt.figure(figsize=(18, 11))
    plot_aperture(
        madx,
        title="IR 5, Injection Optics Aperture Tolerance",
        plot_bpms=True,
        xlimits=(ip5s - 80, ip5s + 80),
        aperture_ylim=(0, 25),
        k0l_lim=(-4e-4, 4e-4),
        k1l_lim=(-6e-2, 6e-2),
        color="brown",
    )
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_physical_apertures_ir5_collision_hozirontal(_collision_aperture_tolerances_lhc_madx):
    madx = _collision_aperture_tolerances_lhc_madx
    madx.command.twiss()
    twiss_df = madx.table.twiss.dframe()
    ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

    figure = plt.figure(figsize=(18, 11))
    limits = (ip5s - 350, ip5s + 350)
    plot_physical_apertures(madx, plane="x", xlimits=limits, scale=1e2)

    plt.ylim(-5, 5)
    plt.ylabel("X [cm]")
    plt.xlabel("S [m]")
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_physical_apertures_ir5_collision_vertical(_collision_aperture_tolerances_lhc_madx):
    madx = _collision_aperture_tolerances_lhc_madx
    madx.command.twiss()
    twiss_df = madx.table.twiss.dframe()
    ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

    figure = plt.figure(figsize=(18, 11))
    limits = (ip5s - 350, ip5s + 350)
    plot_physical_apertures(madx, plane="y", xlimits=limits, scale=1e3)

    plt.ylim(-50, 50)
    plt.ylabel("Y [mm]")
    plt.xlabel("S [m]")
    return figure


def test_plot_physical_apertures_raises_on_wrong_plane():
    madx = Madx(stdout=False)

    with pytest.raises(ValueError, match=r"Invalid 'plane' argument."):
        plot_physical_apertures(madx, plane="invalid")
