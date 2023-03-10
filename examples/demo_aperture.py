"""

.. _demo-accelerator-aperture:

====================
Accelerator Aperture
====================

This example shows how to use the `~.plotting.aperture.plot_aperture` function
to visualise the available aperture in your machine, with the LHC for example.
"""

import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.plotting.aperture import plot_aperture, plot_real_apertures
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Setup a simple LHC simulation in ``MAD-X``, at injection energy (450 GeV)

madx = Madx(stdout=False)
madx.option(echo=False, warn=False)

madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.1")  # injection optics

lhc.make_lhc_beams(madx, energy=450)
madx.command.use(sequence="lhcb1")

###############################################################################
# We now call the aperture definitions and tolerances, then task ``MAD-X`` with
# computing the available aperture:

madx.call("lhc/aperture.b1.madx")
madx.call("lhc/aper_tol.b1.madx")

madx.command.twiss()
madx.command.aperture(cor=0.002, dp=8.6e-4, halo="{6,6,6,6}", bbeat=1.05, dparx=0.14, dpary=0.14)

###############################################################################
# We can now determine the exact position of the IP5 point and plot the LHC
# injection aperture:

twiss_df = madx.table.twiss.dframe()
ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

###############################################################################
# And now we can plot the aperture:

plt.figure(figsize=(20, 13))
plot_aperture(
    madx,
    title="IR5, Collision Optics - Beam 1 Aperture Tolerance",
    plot_bpms=True,
    xlimits=(ip5s - 80, ip5s + 80),
    aperture_ylim=(0, 25),
    k0l_lim=(-4e-4, 4e-4),
    k1l_lim=(-0.08, 0.08),
    color="darkslateblue",
)
for axis in plt.gcf().get_axes():
    axis.axvline(x=ip5s, color="red", ls="--", lw=1.5, label="IP5")
plt.gca().legend()
plt.show()


###############################################################################
# We can also go for a different type of aperture plot, which tries to give 
# the elements' real physical apertures, with the `~.plotting.aperture.plot_real_apertures`
# function:

plt.figure(figsize=(18, 10))
plot_real_apertures(madx, plane="x")
plt.setp(plt.gca(), xlabel="S [m]", ylabel="X [m]")
plt.ylim(-0.035, 0.035)

###############################################################################
# We can give a ``scale`` argument to change the scale of the Y-axis. Let's make
# it in centimeters here:

plt.figure(figsize=(18, 10))
plot_real_apertures(madx, plane="x", scale=1e2)  # just give the scaling factor
plt.setp(plt.gca(), xlabel="S [m]", ylabel="Y [cm]")
plt.ylim(-4, 4)
plt.xlim(9000, 11_000)

###############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.lhc`: `~.lhc._setup.make_lhc_beams`
#    - `~.plotting.aperture`: `~.plotting.aperture.plot_aperture`
