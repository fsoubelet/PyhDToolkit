"""

.. _demo-ir-errors:

=========================
LHC IR Errors Assignments
=========================

This example shows how to use the `~.errors.misalign_lhc_ir_quadrupoles` function
to assign magnet errors in the Insertion Region magnets of the LHC.

.. warning::
    The implementation of this function makes it valid only for LHC IP IRs, which are 
    1, 2, 5 and 8. Other IRs have different layouts that are incompatible.
"""
# sphinx_gallery_thumbnail_number = 1
import matplotlib.pyplot as plt
import numpy as np

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools import errors, lhc, matching
from pyhdtoolkit.utils import logging

logging.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Setup a simple LHC simulation in ``MAD-X``, at injection energy (450 GeV)

madx = Madx(stdout=False)
madx.option(echo=False, warn=False)

madx.call("lhc/lhc_as-built.seq")
madx.call("lhc/opticsfile.22")  # collision optics

###############################################################################
# Importantly in ``MAD-X``, when dealing with RNG one should set a generator and
# seed, which we do below:

madx.option(rand="best", randid=np.random.randint(1, 11))  # random number generator
madx.eoption(seed=np.random.randint(1, 999999999))  # not using default seed

###############################################################################
# Let's define beams and use the **lhcb1** sequence.

lhc.make_lhc_beams(madx, energy=7000)
madx.command.use(sequence="lhcb1")

###############################################################################
# We can now install errors in the IR quadrupoles. Note that this function accepts
# keyword arguments for the error definition, and any *kwarg* will be passed to the
# ``EALIGN`` command of ``MAD-X``.
#
# Here let's apply systematic horizontal misalignment errors and tilt errors to the
# quadrupoles Q1 to Q6 (first to sixth) on both sides of IP1:

errors.misalign_lhc_ir_quadrupoles(
    madx,
    ips=[1],
    beam=1,
    quadrupoles=[1, 2, 3, 4, 5, 6],
    sides="RL",
    dx="0.001*TGAUSS(2.5)",
    dpsi="0.003*GAUSS(2.5)",
)

###############################################################################
# Let's match to our working point, and retrieve the errors directly through the
# internal ``MAD-X`` tables through `~cpymad`:

madx.command.use(sequence="lhcb1")
matching.match_tunes_and_chromaticities(madx, "lhc", "lhcb1", 62.31, 60.32, 2.0, 2.0)
error_table = madx.table.ir_quads_errors.dframe().copy()

###############################################################################
# Let's quickly re-arrange the resulting `~pandas.DataFrame` to align with the
# order in which they are in the machine:

error_table.name = error_table.name.apply(lambda x: x[:-2])
error_table = error_table.set_index("name", drop=True)
error_table = error_table[["dx", "dy", "dpsi", "dtheta"]]  # only keep those
error_table = error_table.reindex(  # their order in the machine
    [
        "mqml.6l1.b1",
        "mqml.5l1.b1",
        "mqy.4l1.b1",
        "mqxa.3l1",
        "mqxb.b2l1",
        "mqxb.a2l1",
        "mqxa.1l1",
        "mqxa.1r1",
        "mqxb.a2r1",
        "mqxb.b2r1",
        "mqxa.3r1",
        "mqy.4r1.b1",
        "mqml.5r1.b1",
        "mqml.6r1.b1",
    ]
)
error_table

###############################################################################
# We can also check that all these elements have been correctly affected:

assert all(error_table["dx"] != 0)
assert all(error_table["dpsi"] != 0)

###############################################################################
# We can visualise the distribution of errors across these magnets with a bar
# chart, making use of the `~pandas.DataFrame` plotting capabilities:

axes = error_table.plot(
    y=["dx", "dpsi"],
    kind="bar",
    title="Applied Errors",
    xlabel="Magnet Name",
    figsize=(20, 11),
    subplots=True,
    rot=45,
)

axes[0].set_title("")
axes[0].set_ylabel("dx [m]")
axes[1].set_title("")
axes[1].set_ylabel("dpsi [rad]")
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
#    - `~.cpymadtools.errors`: `~.errors.misalign_lhc_ir_quadrupoles`
#    - `~.cpymadtools.lhc`: `~.lhc.make_lhc_beams`
#    - `~.cpymadtools.matching`: `~.matching.match_tunes_and_chromaticities`
