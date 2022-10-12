"""

.. _demo-crossing-schemes:

====================
LHC Crossing Schemes
====================

This example shows how to use the `~.plotting.crossing.plot_two_lhc_ips_crossings`
function to visualise the crossing schemes setup at the LHC IRs.

.. note::
    This is very LHC-specific and will most likely not work with other machines.
"""
import matplotlib.pyplot as plt

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.plotting.crossing import plot_two_lhc_ips_crossings
from pyhdtoolkit.utils import logging

logging.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial


###############################################################################
# Setup a simple LHC simulation in ``MAD-X``, with collision optics (at 7 TeV):

madx = Madx(stdout=False)
madx.option(echo=False, warn=False)
madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collisions optics

###############################################################################
# Let's re-cycle the sequences to avoid having IR1 split at beginning and end of lattice,
# as is the default in the LHC sequence. Note that it is important to re-cycle both
# sequences from the same points for the plots later on.

lhc.re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
lhc.re_cycle_sequence(madx, sequence="lhcb2", start="IP3")
lhc.make_lhc_beams(madx, energy=7000)
madx.command.use(sequence="lhcb1")

###############################################################################
# Now we plot the crossing schemes, here for IP1 and IP5.

plt.figure(figsize=(18, 11))
plot_two_lhc_ips_crossings(madx, first_ip=1, second_ip=5)

###############################################################################
# We can have a look at, say, IP2 and IP8 by simply changing the parameters, and
# for instance also remove the highlighting of MQX and MBX elements:

plt.figure(figsize=(18, 11))
plot_two_lhc_ips_crossings(madx, first_ip=2, second_ip=8, highlight_mqx_and_mbx=False)

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
#    - `~.plotting.crossing`: `~.plotting.crossing.plot_two_lhc_ips_crossings`
