"""
======================
Free Tracking Spectrum
======================

This example shows how to use the `~pyhdtoolkit.cpymadtools.track.track_single_particle` function to track a 
particle with the ``TRACK`` command of ``MAD-X``, and visualise its coordinates and spectrum.

In this example we will generate a dummy lattice, set its working point and track particles to plot their phase space coordinates.
"""
# sphinx_gallery_thumbnail_number = -1
import matplotlib.pyplot as plt
import numpy as np

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc, track
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")

###############################################################################
# Let's start by setting up the LHC in ``MAD-X``, in this case at top energy:

madx = Madx(stdout=False)
madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collision optics

lhc.make_lhc_beams(madx)
lhc.re_cycle_sequence(madx, sequence="lhcb1", start="MSIA.EXIT.B1")  # as done in OMC

madx.command.use(sequence="lhcb1")

###############################################################################
# Slicing is necessary in ``MAD-X`` in order to perform tracking, so let's do so.

lhc.make_lhc_thin(madx, sequence="lhcb1", slicefactor=4)
madx.use(sequence="lhcb1")

###############################################################################
# Now we can track a particle. By default, the "start of machine" as ``MAD-X`` sees it
# is where coordinates will be registered each turn. It is possible with this function
# to provide additional elements at which to record coordinates. In our example, we'll
# provide two BPMs for demonstration purposes.
#
# The function accepts many other options that will be provided to the ``TRACK`` command,
# please refer to the API reference for more information.
#
# .. note::
#     When providing additional observation points, each element must be a string,
#     and be the exact name of the element as given to ``MAD-X``.

tracks_dict = track.track_single_particle(
    madx,
    nturns=1023,
    initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0),  # this is actually quite high!
    observation_points=["BPMSW.1L1.B1_DOROS", "BPMSW.1R1.B1_DOROS"],
    # RECLOSS=True,  # Create an internal table recording lost particles
    # ONEPASS=True,  # Do not search closed orbit and give coordinates relatively to the reference orbit
    # DUMP=True,  # Write to file
    # FILE="track",  # File for export if DUMP=True, MAD-X appends "one" to this name if we set ONETABLE to True
    # ONETABLE=True,  # Gather all observation points data into a single table (and file if DUMP set to True)
)

###############################################################################
# The function returns a dictionary with an entry per observation point, named
# **observation_point_n** where *n* is the number of the observation point, in the
# order they are provided. In our example, we will have three observation points: the
# start of machine and the two provided BPMs.
#
# Each key holds as value a `~pandas.DataFrame` with the following columns: *number*, *turn*,
# *x*, *px*, *y*, *py*, *t*, *pt*, *s*, *e*. See for instance below:

tracks_dict["observation_point_2"]

###############################################################################
# Once tracking data is obtained, one can easily plot the coordinates and spectrum
# using the convenience `~pandas.DataFrame` plotting methods. Here it is for the
# first obeservation BPM we provided above:

tracks = tracks_dict["observation_point_2"]  # point 1 for MAD-X is start of machine as defined
tracks.plot(
    x="turn",
    y=["x", "y"],
    marker=".",
    xlabel="Turn Number",
    ylabel="Transverse Positions $[m]$",
    figsize=(18, 10),
)
plt.show()

###############################################################################
# In order to plot the spectra of the particle motion, one should first compute
# them. This is the matter of a simple fast fourier transform:

tracks["horizontal"] = np.abs(np.fft.fft(tracks["x"]))  # x spectrum
tracks["vertical"] = np.abs(np.fft.fft(tracks["y"]))  # y spectrum
tracks["tunes"] = np.linspace(0, 1, len(tracks))  # used for x-axis when plotting

###############################################################################
# .. tip::
#     To get the tunes of the particle, one can find the peak of the spectra.
#
#     .. code-block:: python
#
#      qx = tracks.tunes[tracks.horizontal == tracks.horizontal.max()].to_numpy()[0]
#      qy = tracks.tunes[tracks.vertical == tracks.vertical.max()].to_numpy()[0]
#
# One can then plot the spectra by plotting the computed values against the tune space:

tracks.plot(
    x="tunes",
    y=["horizontal", "vertical"],
    marker=".",
    xlim=(0.25, 0.4),
    xlabel="Tunes",
    ylabel="Spectrum [a.u]",
    figsize=(18, 10),
)


###############################################################################
# In case the user provided ``ONETABLE=True`` to the tracking function, then all
# observation points data will be stored in a single `~pandas.DataFrame` that can
# be accessed with the **trackone** key in the returned dictionary. In that case,
# accessing the coordinates at a given observation point is done by making use of
# the DataFrame indexing syntax:

tracks_dict = track.track_single_particle(
    madx,
    nturns=10,  # few turns to speedup the example
    initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0),
    observation_points=["BPMSW.1L1.B1_DOROS", "BPMSW.1R1.B1_DOROS"],
    ONETABLE=True,  # Gather all observation points data into a single table (and file if DUMP set to True)
)

observation_point = "BPMSW.1L1.B1_DOROS"
tracks = tracks_dict["trackone"]
tracks[tracks.index == observation_point.lower()]  # cpymad lower-cases the names

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
#    - `~.cpymadtools.lhc`: `~.lhc.make_lhc_beams`, `~.lhc.re_cycle_sequence`
#    - `~.cpymadtools.track`: `~.track.track_single_particle`