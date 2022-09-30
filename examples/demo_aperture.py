"""

.. _demo-accelerator-aperture:

====================
Accelerator Aperture
====================

This example shows how to use the `~.plotters.AperturePlotter.plot_aperture` function
to visualise the available aperture in your machine, with the LHC for example.
"""

import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.cpymadtools.plot.aperture import plot_aperture
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

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

twiss_df = madx.table.twiss.dframe().copy()
ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

###############################################################################
# And now we can plot the aperture:

plt.figure(figsize=(13, 9))
plot_aperture(
    madx,
    title="IR5, Collision Optics Aperture Tolerance",
    plot_bpms=True,
    xlimits=(ip5s - 80, ip5s + 80),
    aperture_ylim=(0, 20),
    k0l_lim=(-4e-4, 4e-4),
    k1l_lim=(-0.08, 0.08),
    color="darkslateblue",
)
for axis in plt.gcf().get_axes():
    axis.axvline(x=ip5s, color="red", ls="--", lw=1.5, label="IP5")
plt.gca().legend()
plt.show()

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
#    - `~.cpymadtools.lhc`: `~.lhc.make_lhc_beams`
#    - `~.cpymadtools.plot`: `~.plot.aperture`, `~.plot.aperture.plot_aperture`
