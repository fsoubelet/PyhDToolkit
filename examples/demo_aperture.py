"""

.. _demo-accelerator-aperture:

====================
Accelerator Aperture
====================

This example shows how to use the `~.plotting.aperture.plot_aperture` and 
`~.plotting.aperture.plot_physical_apertures` functions to visualise the
available aperture in your machine, with the LHC used for this example.

.. important::
    This example requires the `acc-models-lhc` repository to be cloned locally. One
    can get it by running the following command:

    .. code-block:: bash

        git clone -b 2022 https://gitlab.cern.ch/acc-models/acc-models-lhc.git --depth 1

    Here I set the 2022 branch for stability and reproducibility of the documentation
    builds, but you can use any branch you want.
"""

import matplotlib.pyplot as plt
from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.plotting.aperture import plot_aperture, plot_physical_apertures
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Let's start by setting up the LHC in ``MAD-X``, in this case at injection
# optics and energy. To understand the function below have a look at the
# :ref:`lhc setup example <demo-lhc-setup>`.

madx: Madx = lhc.prepare_lhc_run3(
    opticsfile="acc-models-lhc/operation/optics/R2022a_A11mC11mA10mL10m.madx",
    energy=450,  # given in GeV
    stdout=False
)

###############################################################################
# We now call the aperture definitions and tolerances, then task ``MAD-X`` with
# computing the available aperture:

madx.call("lhc/aperture.b1.madx")
madx.call("lhc/aper_tol.b1.madx")

madx.command.twiss()
madx.command.aperture(cor=0.002, dp=8.6e-4, halo="{6,6,6,6}", bbeat=1.05, dparx=0.14, dpary=0.14)

###############################################################################
# The details for the ``MAD-X`` ``aperture`` command can be found in the manual.
# We can now determine the exact position of the IP5 point and plot the LHC
# injection aperture:

twiss_df = madx.table.twiss.dframe()
ip5s = twiss_df.s[twiss_df.name.str.contains("ip5")].to_numpy()[0]

###############################################################################
# And now we can plot the aperture around IP5 with the `~.plotting.aperture.plot_aperture`
# function. This uses the values in the ``APERTURE`` table of ``MAD-X``, which
# gives aperture information in terms of beam sigma.

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
# the elements' real physical apertures, with the `~.plotting.aperture.plot_physical_apertures`
# function:

plt.figure(figsize=(18, 10))
plot_physical_apertures(madx, plane="x")
plt.setp(plt.gca(), xlabel="S [m]", ylabel="X [m]")
plt.ylim(-0.035, 0.035)
plt.show()

###############################################################################
# We can give a ``scale`` argument to change the scale of the Y-axis. Let's make
# it in centimeters here:

plt.figure(figsize=(18, 10))
plot_physical_apertures(madx, plane="x", scale=1e2)  # just give the scaling factor
plt.setp(plt.gca(), xlabel="S [m]", ylabel="Y [cm]")
plt.ylim(-4, 4)
plt.xlim(9000, 11_000)
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
#    - `~.cpymadtools.lhc`: `~.lhc._setup.prepare_lhc_run3`
#    - `~.plotting.aperture`: `~.plotting.aperture.plot_aperture`, `~.plotting.aperture.plot_physical_apertures`
