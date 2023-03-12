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
"""
# sphinx_gallery_thumbnail_number = 3
import matplotlib.pyplot as plt

from pyhdtoolkit.cpymadtools import coupling, lhc, twiss
from pyhdtoolkit.plotting.aperture import plot_physical_apertures
from pyhdtoolkit.plotting.envelope import plot_beam_envelope
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.plotting.utils import draw_ip_locations, get_lhc_ips_positions
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")  # keep the output clean
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Preparing the LHC setups
# ------------------------
# Two functions in `pyhdtoolkit.cpymadtools.lhc._setup` provide functionality to
# set up the LHC simulations quickly and effortlessly:
# `~.cpymadtools.lhc._setup.setup_lhc.prepare_lhc_run2` and
# `~.cpymadtools.lhc._setup.setup_lhc.prepare_lhc_run3`.`
# They return a `cpyamad.Madx` instance with the LHC sequence and optics loaded,
# both beams defined.
#
# .. important::
#     As this is a Run 3 setup, it is assumed that the ``acc-models-lhc`` repo
#     is available in the root space, which is needed by the different files in
#     ``acc-models-lhc``.

# We need to give an opticsfile at the very least, other arguments are optional
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
    ax.set_xlabel("S [m]")
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
# It calls the functions seen above internally and works on the same logic:
#
# These quick setups, with context manager option, allow to do quick "one-shot"
# simulations with the LHC. For example, one can very quickly compare apertures
# around say IP5 for two optics files as below:

# One can just give the name of the optics file and it will be found automatically
# assuming the ``acc-models-lhc`` repo structure. Defaults assume Run 3.
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
        axes[1].set_xlabel("S [m]")

        for axis in axes:
            axis.legend()
            axis.yaxis.set_major_locator(plt.MaxNLocator(5))
            draw_ip_locations(ips, location="inside", ax=axis)

        fig.suptitle("LHC Injection Optics")
        fig.align_ylabels(axes)

        plt.tight_layout()
        plt.show()

###############################################################################
# Notice we don't need to call ``madx.exit()`` as the context manager takes care
# of that. Now, the same with betastar = 30cm optics. We can also easily add the
# element apertures on top of the plot:

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
        axes[1].set_xlabel("S [m]")

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
    lhc.apply_lhc_colinearity_knob(madx, colinearity_knob_value=3, ir=5)
    lhc.apply_lhc_coupling_knob(madx, coupling_knob=5e-3)
    rdtsb1 = coupling.get_coupling_rdts(madx)

with lhc.LHCSetup(opticsfile="R2022a_A30cmC30cmA10mL200cm.madx", beam=2, stdout=False) as madx:
    lhc.apply_lhc_colinearity_knob(madx, colinearity_knob_value=3, ir=5)
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
    b2.set_xlabel("S [m]")

    for axis in (b1, b2):
        axis.set_ylabel("|RDT|")
        axis.legend()
    plt.show()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.cpymadtools.coupling`: `~.coupling.get_coupling_rdts`
#    - `~.cpymadtools.lhc`: `~.lhc.apply_lhc_colinearity_knob`, `~.lhc.apply_lhc_coupling_knob`, `~.lhc._setup.LHCSetup`, `~.lhc._setup.prepare_lhc_run3`
#    - `~.plotting.aperture`: `~.plotting.aperture.plot_physical_apertures`
#    - `~.plotting.envelope`: `~.plotting.envelope.plot_beam_envelope`
#    - `~.plotting.utils`:  `~.plotting.utils.draw_ip_locations`, `~.plotting.utils.get_lhc_ips_positions`
