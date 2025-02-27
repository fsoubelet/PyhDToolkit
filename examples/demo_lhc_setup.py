"""

.. _demo-lhc-setup:

===============
Quick LHC Setup
===============

These examples show how to use the functions in `pyhdtoolkit.cpymadtools.lhc._setup`
managers to easily and quickly set up LHC simulations. These are exported and
available at the level of the `pyhdtoolkit.cpymadtools.lhc` module.

.. note::
    This is obviously very specific to the LHC machine.

.. important::
    This example requires the `acc-models-lhc` repository to be cloned locally. One
    can get it by running the following command:

    .. code-block:: bash

        git clone -b 2022 https://gitlab.cern.ch/acc-models/acc-models-lhc.git --depth 1

    Here I set the 2022 branch for stability and reproducibility of the documentation
    builds, but you can use any branch you want.
"""

# sphinx_gallery_thumbnail_number = 4
import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import coupling, lhc, twiss
from pyhdtoolkit.plotting.aperture import plot_physical_apertures
from pyhdtoolkit.plotting.envelope import plot_beam_envelope
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.plotting.utils import draw_ip_locations, get_lhc_ips_positions
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")  # keep the output clean
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# One might have different ways that the LHC examples in other pages of this
# gallery are set up, for instance in the :ref:`LHC crossing schemes example
# <demo-crossing-schemes>` or the :ref:`AC Dipole tracking example
# <demo-ac-dipole-tracking>`. Setting up the LHC usually involves the same
# steps every time: calling the sequence, defining beams, calling the optics
# file, potentially slicing the sequence, calling ``use`` on the proper beam
# sequence, etc. See below for a typical B1 example:

madx = Madx(stdout=False)
madx.call("acc-models-lhc/lhc.seq")
lhc.make_lhc_beams(madx, energy=6800)
lhc.make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
lhc.make_lhc_beams(madx, energy=6800)
lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
madx.call("acc-models-lhc/operation/optics/R2022a_A30cmC30cmA10mL200cm.madx")
madx.command.use(sequence="lhcb1")
madx.exit()

###############################################################################
# As this is quite repetitive and involves quite a few places in which to write
# "hard-coded" elements (e.g. lhcb1, the re-cycling start point etc) convenience
# functions are provided.

###############################################################################
# Preparing the LHC setups
# ------------------------
# Two functions in `pyhdtoolkit.cpymadtools.lhc._setup` provide functionality
# to set up the LHC simulations quickly and effortlessly:
# `~.cpymadtools.lhc._setup.setup_lhc.prepare_lhc_run2` and
# `~.cpymadtools.lhc._setup.setup_lhc.prepare_lhc_run3`.
#
# They both return a `cpyamad.Madx` instance with the desired LHC sequence and
# optics loaded, beams defined for both ``lhcb1`` and ``lhcb2`` sequences,
# potentially sliced lattices etc. The very minimum required at function call
# is to provide an opticsfile, other arguments are optional. Keyword arguments
# are passed to the `~cpymad.madx.Madx` creation call. For instance:

# One could give the optics name only and it will be found automatically assuming the
# `acc-models-lhc` repo structure. See lower down for examples.
madx = lhc.prepare_lhc_run3(
    opticsfile="acc-models-lhc/operation/optics/R2022a_A30cmC30cmA10mL200cm.madx",
    stdout=False,
)
df = twiss.get_twiss_tfs(madx)
ips = get_lhc_ips_positions(df)

with plt.rc_context(_SPHINX_GALLERY_PARAMS):
    fig, ax = plt.subplots(figsize=(18, 10))
    ax.plot(df.S, df.BETX / 1e3, label=r"$\beta_x$")
    ax.plot(df.S, df.BETY / 1e3, label=r"$\beta_y$")
    draw_ip_locations(ips)
    ax.set_xlabel("Longitudinal location [m]")
    ax.set_ylabel(r"$\beta_{x,y}$ [km]")
    ax.legend()
    plt.show()

###############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()

###############################################################################
# As a context manager
# --------------------
# In order to not have to close the ``MAD-X`` instance everytime, we can use the
# context manager options from `cpymad`. To apply this to an LHC setup, there is
# `pyhdtoolkit.cpymadtools.lhc._setup.LHCSetup` to be used as a context manager.
# It calls the functions seen above internally and works on the same logic. The
# above becomes:

with lhc.LHCSetup(run=3, opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", stdout=False) as madx:
    df = twiss.get_twiss_tfs(madx)
    ips = get_lhc_ips_positions(df)

    with plt.rc_context(_SPHINX_GALLERY_PARAMS):
        fig, ax = plt.subplots(figsize=(18, 10))
        ax.plot(df.S, df.BETX / 1e3, label=r"$\beta_x$")
        ax.plot(df.S, df.BETY / 1e3, label=r"$\beta_y$")
        draw_ip_locations(ips)
        ax.set_xlabel("Longitudinal location [m]")
        ax.set_ylabel(r"$\beta_{x,y}$ [km]")
        ax.legend()
        plt.show()

###############################################################################
# Notice we don't need to call ``madx.exit()`` as the context manager takes care
# of that.
#
# These quick setups, with context manager option, allow to do quick "one-shot"
# simulations. For example, one can very quickly compare beam sizes around say
# IP5 for two different optics. Here below for the 2022 proton injection optics:

with lhc.LHCSetup(run=3, opticsfile="R2022a_A11mC11mA10mL10m.madx", stdout=False) as madx:
    df = twiss.get_twiss_tfs(madx)
    ips = get_lhc_ips_positions(df)
    limits = (ips["IP5"] - 500, ips["IP5"] + 500)

    with plt.rc_context(_SPHINX_GALLERY_PARAMS):
        fig, axes = plt.subplots(2, 1, sharex=True, figsize=(18, 10))

        plot_beam_envelope(madx, "lhcb1", "x", 1, scale=1e3, xlimits=limits, ax=axes[0])
        plot_beam_envelope(madx, "lhcb1", "x", 3, scale=1e3, xlimits=limits, ax=axes[0])
        plot_beam_envelope(madx, "lhcb1", "x", 5, scale=1e3, xlimits=limits, ax=axes[0])
        axes[0].set_ylabel("X [mm]")

        plot_beam_envelope(madx, "lhcb1", "y", 1, scale=1e3, xlimits=limits, ax=axes[1])
        plot_beam_envelope(madx, "lhcb1", "y", 3, scale=1e3, xlimits=limits, ax=axes[1])
        plot_beam_envelope(madx, "lhcb1", "y", 5, scale=1e3, xlimits=limits, ax=axes[1])
        axes[1].set_ylabel("Y [mm]")
        axes[1].set_xlabel("Longitudinal location [m]")

        for axis in axes:
            axis.legend()
            axis.yaxis.set_major_locator(plt.MaxNLocator(5))
            draw_ip_locations(ips, location="inside", ax=axis)

        fig.suptitle("LHC Injection Optics")
        fig.align_ylabels(axes)

        plt.tight_layout()
        plt.show()

###############################################################################
# Now, the same with betastar = 30cm optics. We can also easily add the
# element apertures on top of the plot (notice how we get this result with only
# 28 lines of code!):

with lhc.LHCSetup(opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", stdout=False) as madx:
    # We'll need to call these to have aperture limitations
    madx.call("lhc/aperture.b1.madx")
    madx.call("lhc/aper_tol.b1.madx")

    df = twiss.get_twiss_tfs(madx)
    ips = get_lhc_ips_positions(df)
    limits = (ips["IP5"] - 350, ips["IP5"] + 350)

    with plt.rc_context(_SPHINX_GALLERY_PARAMS):
        fig, axes = plt.subplots(2, 1, sharex=True, figsize=(18, 13))

        plot_physical_apertures(madx, plane="x", scale=1e3, xlimits=limits, ax=axes[0])
        plot_beam_envelope(madx, "lhcb1", "x", 3, scale=1e3, xlimits=limits, ax=axes[0])
        plot_beam_envelope(madx, "lhcb1", "x", 6, scale=1e3, xlimits=limits, ax=axes[0])
        plot_beam_envelope(madx, "lhcb1", "x", 11, scale=1e3, xlimits=limits, ax=axes[0])
        axes[0].set_ylabel("X [mm]")

        plot_physical_apertures(madx, plane="y", scale=1e3, xlimits=limits, ax=axes[1])
        plot_beam_envelope(madx, "lhcb1", "y", 3, scale=1e3, xlimits=limits, ax=axes[1])
        plot_beam_envelope(madx, "lhcb1", "y", 6, scale=1e3, xlimits=limits, ax=axes[1])
        plot_beam_envelope(madx, "lhcb1", "y", 11, scale=1e3, xlimits=limits, ax=axes[1])
        axes[1].set_ylabel("Y [mm]")
        axes[1].set_xlabel("Longitudinal location [m]")

        for axis in axes:
            axis.legend()
            axis.set_ylim(-45, 45)
            axis.yaxis.set_major_locator(plt.MaxNLocator(5))
            draw_ip_locations(ips, ax=axis)

        fig.suptitle(r"LHC $\beta^{\ast} = 30$cm Optics")
        fig.align_ylabels(axes)

        plt.tight_layout()
        plt.show()

###############################################################################
# If one wants to have a look at, say, coupling RDTs throughout the machine, for
# both beams when applying the coupling knob:

with lhc.LHCSetup(opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", stdout=False) as madx:
    lhc.apply_lhc_coupling_knob(madx, coupling_knob=5e-3)
    rdtsb1 = coupling.get_coupling_rdts(madx)

with lhc.LHCSetup(opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", beam=2, stdout=False) as madx:
    lhc.apply_lhc_coupling_knob(madx, coupling_knob=5e-3, beam=2)
    rdtsb2 = coupling.get_coupling_rdts(madx)

ipsb1 = get_lhc_ips_positions(rdtsb1)
ipsb2 = get_lhc_ips_positions(rdtsb2)

with plt.rc_context(_SPHINX_GALLERY_PARAMS):
    fig, (b1, b2) = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(15, 10))
    b1.plot(rdtsb1.S, rdtsb1.F1001.abs(), label=r"$f_{1001}$")
    b1.plot(rdtsb1.S, rdtsb1.F1010.abs(), label=r"$f_{1010}$")
    b1.set_title("Beam 1")
    draw_ip_locations(ipsb1, location="inside", ax=b1)

    b2.plot(rdtsb2.S, rdtsb2.F1001.abs(), label=r"$f_{1001}$")
    b2.plot(rdtsb2.S, rdtsb2.F1010.abs(), label=r"$f_{1010}$")
    draw_ip_locations(ipsb2, location="inside", ax=b2)
    b2.set_title("Beam 2")
    b2.set_xlabel("Longitudinal location [m]")

    for axis in (b1, b2):
        axis.set_ylabel("|RDT|")
        axis.legend()
    plt.show()

###############################################################################
# That's it, happy simulations!
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.coupling`: `~.coupling.get_coupling_rdts`
#    - `~.cpymadtools.lhc`: `~.lhc.apply_lhc_coupling_knob`, `~.lhc._setup.LHCSetup`, `~.lhc._setup.prepare_lhc_run3`, `~.lhc._setup.prepare_lhc_run2`
#    - `~.plotting.aperture`: `~.plotting.aperture.plot_physical_apertures`
#    - `~.plotting.envelope`: `~.plotting.envelope.plot_beam_envelope`
#    - `~.plotting.utils`:  `~.plotting.utils.draw_ip_locations`, `~.plotting.utils.get_lhc_ips_positions`
