"""

.. _demo-ac-dipole-tracking:

==================================
AC Dipole Driven Tracking Spectrum
==================================

This example shows how to use the `~.lhc.install_ac_dipole_as_kicker` and 
`~.track.track_single_particle` function to track a  particle with the 
``TRACK`` command of ``MAD-X``, and visualise its coordinates and spectrum.

In this example we will use the LHC lattice to illustrate the ACD tracking 
workflow when using `~pyhdtoolkit.cpymadtools`.

.. note::
    This is very similar to the :ref:`free tracking example <demo-free-tracking>` 
    with the difference that there is special care to take to install the AC Dipole 
    element. It is recommended to read that tutorial first as this one will focus 
    on the specificities of the AC Dipole setup.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc, matching, track
from pyhdtoolkit.utils import logging

logging.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Let's start by setting up the LHC in ``MAD-X``, in this case at top energy:

madx = Madx(stdout=False)
madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collision optics

lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")
lhc.make_lhc_beams(madx)
madx.command.use(sequence="lhcb1")
matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)

###############################################################################
# Slicing is necessary in ``MAD-X`` in order to perform tracking, so let's do so.

lhc.make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
madx.use(sequence="lhcb1")

###############################################################################
# Before tracking, we need to install the AC dipole element. We need to specify
# the driven tunes, the kick amplitude, and the ramp-up, flat-top and ramp-down
# turns. Note that in a real machine, the ramping process should respect some
# constaints to stay adiabatic with regards to the emittance (:cite:t:`Tomas:ACDAdiabaticity:2005`)
#
# .. important::
#     In a real machine, the AC Dipole does impact the orbit as well as the betatron
#     functions when turned on (:cite:t:`Miyamoto:ACD:2008`, part III). In ``MAD-X``
#     however, it cannot be modeled to do both at the same time. This routine introduces
#     an AC Dipole as a kicker element so that its effect can be seen on particle trajectory
#     in tracking. It **does not** affect ``TWISS`` functions.
#
# Here we will choose for the settings the same values as we use in operation in the LHC:

lhc.install_ac_dipole_as_kicker(
    madx,
    deltaqx=-0.01,  # driven horizontal tune to Qxd = 62.31 - 0.01 = 62.30
    deltaqy=0.012,  # driven vertical tune to Qyd = 60.32 + 0.012 = 60.332
    sigma_x=2,  # bunch amplitude kick in the horizontal plane
    sigma_y=2,  # bunch amplitude kick in the vertical plane
    beam=1,  # beam for which to install and kick
    start_turn=100,  # when to turn on the AC Dipole
    ramp_turns=2000,  # how many turns to ramp up/down the AC Dipole
    top_turns=6600,  # how many turns to keep the AC Dipole at full kick
)

###############################################################################
# Now we can track a particle. The process is fully similar to what was described
# in the :ref:`free tracking example <demo-free-tracking>`.

tracks_dict = track.track_single_particle(
    madx,
    nturns=10_800,  # give at least (start + ramp + flat-top + ramp + margin)
    initial_coordinates=(0, 0, 0, 0, 0, 0),
    observation_points=["BPM.15L2.B1"],
)

###############################################################################
# Let's have a look at the trajectory of the particle at the **BPM.15L2.B1**
# element through the turns, here in the horizontal plane:

tracks = tracks_dict["observation_point_2"]  # this is BPM.15L2.B1
tracks.plot(
    x="turn",
    y=["x"],
    figsize=(25, 10),
    title="Driven Motion Under AC Dipole",
    xlabel="Turn Number",
    ylabel="Transverse Positions $[m]$",
)
plt.show()

###############################################################################
# We can see the AC Dipole did its job: the amplitude of the particle stays
# at 0 for the first 100 turns, then ramps up for 2000 turns, stays at full
# kick strength for 6600 turns, then ramps down during another 2000 turns.
#
# In order to plot the spectra of the particle motion, let's first determine it.
# Take in consideration that here, we are interested in the driven motion, so
# we need to compute the ``np.fft.fft`` on a subset of the tracking data. In our
# case, the flat-top starts at turn :math:`100 + 2000 = 2100`, and ends at turn
# :math:`100 + 2000 + 6600 = 8700`.

spectrum = pd.DataFrame()
spectrum["horizontal"] = np.abs(np.fft.fft(tracks.x.to_numpy()[2100:8700]))  # top turns
spectrum["vertical"] = np.abs(np.fft.fft(tracks.y.to_numpy()[2100:8700]))  # top turns
spectrum["tunes"] = np.linspace(0, 1, len(spectrum))
spectrum = spectrum[spectrum.tunes.between(0, 0.5)]  # do not care about other half

###############################################################################
# .. tip::
#     To get the tunes of the particle, one can find the peak of the spectra. Below
#     is how we get the fractional part of the tunes. One can check that those values
#     are indeed the desired driven fractional tunes (0.30, 0.332):
#
#     .. code-block:: python
#
#      >>> qxd = spectrum.tunes[spectrum.horizontal == spectrum.horizontal.max()].to_numpy()[0]
#      >>> qyd = spectrum.tunes[spectrum.vertical == spectrum.vertical.max()].to_numpy()[0]
#
# One can now plot the spectra, and here we will add two stem lines at the position of the
# determined driven tunes to highlight them.

qxd = spectrum.tunes[spectrum.horizontal == spectrum.horizontal.max()].to_numpy()[0]
qyd = spectrum.tunes[spectrum.vertical == spectrum.vertical.max()].to_numpy()[0]

spectrum.plot(
    x="tunes",
    y=["horizontal", "vertical"],
    figsize=(18, 10),
    xlim=(0.28, 0.38),
    title="Driven Motion Spectrum",
    xlabel="Tunes",
    ylabel="Spectrum [a.u]",
    logy=True,
)
plt.stem(qxd, spectrum.horizontal.max(), linefmt="C0--", markerfmt="C0o", label=r"$Q_{xD}$")
plt.stem(qyd, spectrum.vertical.max(), linefmt="C1--", markerfmt="C1o", label=r"$Q_{yD}$")
plt.legend()
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
#    - `~.cpymadtools.lhc`: `~.lhc.make_lhc_beams`, `~.lhc.re_cycle_sequence`, `~.lhc.make_lhc_thin`, `~.lhc.install_ac_dipole_as_kicker`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
#    - `~.cpymadtools.track`: `~.track.track_single_particle`
