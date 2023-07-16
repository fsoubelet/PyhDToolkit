"""

.. _demo-crossing-schemes:

====================
LHC Crossing Schemes
====================

This example shows how to use the `~.plotting.crossing.plot_two_lhc_ips_crossings`
function to visualise the crossing schemes setup at the LHC IRs.

.. note::
    This is very LHC-specific and will not work with other machines.
"""
import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.plotting.crossing import plot_two_lhc_ips_crossings
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial


###############################################################################
# Setup a simple LHC simulation in ``MAD-X``, with collision optics (at 6.8 TeV):

madx = Madx(stdout=False)
madx.option(echo=False, warn=False)
madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collisions optics

###############################################################################
# Let's explicitely re-cycle both sequences to avoid having IR1 split at beginning
# and end of lattice. Note that it is important to re-cycle both sequences from 
# the same points for the plots later on.

lhc.re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
lhc.re_cycle_sequence(madx, sequence="lhcb2", start="IP3")
lhc.make_lhc_beams(madx, energy=6800)  # necessary after re-cycling sequences
madx.command.use(sequence="lhcb1")

###############################################################################
# Now we plot the crossing schemes, here for IP1 and IP5.

fig1 = plt.figure(figsize=(18, 11))
plot_two_lhc_ips_crossings(madx, first_ip=1, second_ip=5)
fig1.align_ylabels([fig1.axes[0], fig1.axes[1]])
plt.show()

###############################################################################
# We can have a look at, say, IP2 and IP8 by simply changing the parameters, and
# for instance also remove the highlighting of MQX and MBX elements:

fig2 = plt.figure(figsize=(18, 11))
plot_two_lhc_ips_crossings(madx, first_ip=2, second_ip=8, highlight_mqx_and_mbx=False)
fig2.align_ylabels([fig2.axes[0], fig2.axes[1]])
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
#    - `~.cpymadtools.lhc`: `~.lhc._setup.make_lhc_beams`, `~.lhc._setup.re_cycle_sequence`
#    - `~.plotting.crossing`: `~.plotting.crossing.plot_two_lhc_ips_crossings`
