"""

.. _demo-sbs-plotting:

==========================
Segment-by-Segment Results
==========================

This example shows how to use the modules in `pyhdtoolkit.plotting.sbs` and their various functions
to easily visualize results of segment-by-segment runs.
"""

# sphinx_gallery_thumbnail_number = 2
import matplotlib.pyplot as plt
import tfs

from pyhdtoolkit.plotting.sbs import coupling, phase
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# The functions in `.pyhdtoolkit.plotting.sbs` modules usually need to be provided
# different dataframes corresponding to specific components of segment-by-segment
# results, which can be obtained by directly loading the output **TFS** files.
# Let's load below the coupling results of a segment-by-segment run and related
# model files.

b1_model_tfs = tfs.read("sbs/b1_twiss_elements.dat")
b2_model_tfs = tfs.read("sbs/b2_twiss_elements.dat")

couple_b1_tfs = tfs.read("sbs/b1_sbscouple_IP1.out")
couple_b2_tfs = tfs.read("sbs/b2_sbscouple_IP1.out")

###############################################################################
# One can now easily plot these results in a few lines with functions from the
# `.plotting.sbs.coupling` module. Here we will plot a single component of a
# given coupling RDT through the segment.
#
# .. tip::
#     Providing a dataframe with the model information is optional. If it is given, it is
#     used to determine the position of the IP point in the segment, and this position
#     will then be highlighted in the plot.

# Here we plot the real part of the f1001 coupling resonance driving term (default rdt plotted)
coupling.plot_rdt_component(
    couple_b1_tfs,
    couple_b2_tfs,
    b1_model_tfs,
    b2_model_tfs,
    ip=1,
    component="RE",
    figsize=(12, 12),
    b1_ylabel=r"$\mathrm{Beam\ 1}$ $\Re f_{1001}$",
    b2_ylabel=r"$\mathrm{Beam\ 2}$ $\Re f_{1001}$",
)
# We can set specific limits to the axes by accessing them through the returned Figure
for ax in plt.gcf().axes:
    ax.set_ylim(-0.1, 0.1)
plt.show()

###############################################################################
# One can plot all components of a given coupling RDT for both beams with the
# `~.plotting.sbs.coupling.plot_full_ip_rdt` function.
#
# .. tip::
#     Specific limits can be provided for different components of the RDT. At the
#     moment, these limits apply to the plots of both beams as they share their y
#     axis. Keyword arguments can be used to specify properties of the figure and
#     set the position of the legend.


coupling.plot_full_ip_rdt(
    couple_b1_tfs,
    couple_b2_tfs,
    b1_model_tfs,
    b2_model_tfs,
    ip=1,
    figsize=(20, 11),
    abs_ylimits=(5e-3, 6.5e-2),
    real_ylimits=(-1e-1, 1e-1),
    imag_ylimits=(-1e-1, 1e-1),
    bbox_to_anchor=(0.535, 0.945),
)
plt.show()

###############################################################################
# Similarly, one can plot the phase results of a segment-by-segment run with the
# functions in `~.plotting.sbs.phase`. The plotting logic is the same as above,
# with the simplification that no component has to be chosen. Let's load data for
# this example: one dataframe for each plane for Beam 2.

sbs_phasex = tfs.read("sbs/b2sbsphasext_IP5.out")
sbs_phasey = tfs.read("sbs/b2sbsphaseyt_IP5.out")

phase.plot_phase_segment_one_beam(
    phase_x=sbs_phasex,
    phase_y=sbs_phasey,
    model=b2_model_tfs,
    ip=5,
    figsize=(12, 12),
)
plt.show()

###############################################################################
# Similarly to the coupling example, one can plot the results for both beams in
# a single call with the `~.plotting.sbs.phase.plot_phase_segment_both_beams`
# function, as demonstrated below.

phase.plot_phase_segment_both_beams(
    b1_phase_x=sbs_phasex,
    b1_phase_y=sbs_phasey,
    b2_phase_x=sbs_phasex,
    b2_phase_y=sbs_phasey,
    b1_model=b2_model_tfs,
    b2_model=b2_model_tfs,
    ip=5,
    figsize=(20, 11),
    bbox_to_anchor=(0.535, 0.945),
)
plt.show()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `~.plotting.sbs.coupling`: `~.plotting.sbs.coupling.plot_rdt_component`, `~.plotting.sbs.coupling.plot_full_ip_rdt`
#    - `~.plotting.sbs.phase`: `~.plotting.sbs.phase.plot_phase_segment_one_beam`, `~.plotting.sbs.phase.plot_phase_segment_both_beams`
