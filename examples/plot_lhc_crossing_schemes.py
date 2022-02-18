"""
==================================
LHC Crossing Schemes Plotting Demo
==================================

This example shows how to use the `~pyhdtoolkit.cpymadtools.plotters.CrossingSchemePlotter.plot_two_lhc_ips_crossings` function
to visualise the crossing schemes setup at the LHC IRs.

.. note::
    This is very LHC-specific and will most likely not work with other machines.
"""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import lhc
from pyhdtoolkit.cpymadtools.plotters import CrossingSchemePlotter
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")


###############################################################################
# Setup a simple LHC simulation in ``MAD-X``, with collision optics (at 7 TeV):

madx = Madx(stdout=False)
madx.option(echo=False, warn=False)
madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collisions optics

###############################################################################
# Let's re-cycle the sequences to avoid having IR1 split at beginning and end of lattice,
# as is the default in the LHC sequence:

lhc.re_cycle_sequence(madx, sequence="lhcb1", start="IP3")
lhc.re_cycle_sequence(madx, sequence="lhcb2", start="IP3")
lhc.make_lhc_beams(madx, energy=7000)
madx.command.use(sequence="lhcb1")

###############################################################################
# Now we plot the crossing schemes, here for IP1 and IP5.

CrossingSchemePlotter.plot_two_lhc_ips_crossings(madx, first_ip=1, second_ip=5)
plt.show()

###############################################################################
# We can have a look at, say, IP2 and IP8 by simply changing the parameters, and
# for instance also remove the highlighting of MQX and MBX elements:

CrossingSchemePlotter.plot_two_lhc_ips_crossings(
    madx, first_ip=2, second_ip=8, highlight_mqx_and_mbx=False
)

###############################################################################
# Let's not forget to close the rpc connection to ``MAD-X``:

madx.exit()
