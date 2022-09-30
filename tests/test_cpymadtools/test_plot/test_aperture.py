import matplotlib
import matplotlib.pyplot as plt
import pytest

from pyhdtoolkit.cpymadtools.plot.aperture import plot_aperture

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")


@pytest.mark.mpl_image_compare(tolerance=20, savefig_kwargs={"dpi": 200})
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


@pytest.mark.mpl_image_compare(tolerance=20, style="seaborn-pastel", savefig_kwargs={"dpi": 200})
def test_plot_aperture_ir5_collision(_collision_aperture_tolerances_lhc_madx):

    madx = _collision_aperture_tolerances_lhc_madx
    madx.command.twiss(centre=True)
    twiss_df = madx.table.twiss.dframe().copy()
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
