"""

.. _demo-beam-enveloppe:

==============
Beam Enveloppe
==============

This example shows how to use the `~.plotters.BeamEnvelopePlotter.plot_envelope` function
to visualise the particle beam's enveloppe in your machine.

In this example we will use a very simple lattice, hard-coded below.
"""
# sphinx_gallery_thumbnail_number = 1
import matplotlib.pyplot as plt
import numpy as np

from cpymad.madx import Madx

from pyhdtoolkit.cpymadtools.plotters import BeamEnvelopePlotter
from pyhdtoolkit.models.beam import BeamParameters
from pyhdtoolkit.utils import defaults

defaults.config_logger(level="warning")
plt.rcParams.update(defaults._SPHINX_GALLERY_PARAMS)  # for readability of this tutorial

###############################################################################
# Define beam parameters for injection and top energy (1.9 GeV -> 19 GeV):

beam_injection = BeamParameters(
    charge=1,
    pc_GeV=1.9,
    E_0_GeV=0.9382720813,
    en_x_m=5e-6,
    en_y_m=5e-6,
    deltap_p=2e-3,
)
beam_flattop = BeamParameters(
    charge=1,
    pc_GeV=19,
    E_0_GeV=0.9382720813,
    en_x_m=5e-6,
    en_y_m=5e-6,
    deltap_p=2e-4,
)

###############################################################################
# Define relevant constants.

circumference = 500.0  # machine circumference [m]
n_cells = 25
l_quad = 0.5  # quadrupole length [m]
l_bend = 3.5  # dipole length [m]
l_cell = circumference / n_cells  # cell length [m]

f_m = l_cell / (2 * np.sqrt(2))  # pi/2 phase advance in thin lens approximation (no dipoles)

n_quadrupoles = 2 * n_cells
n_dipoles = 4 * n_cells  # four dipoles per cell
dipole_angle = 2 * np.pi / n_dipoles  # [rad]
dipole_field = dipole_angle * beam_flattop.B_rho_Tm / l_bend  # [T]
quadrupole_gradient = 1 / f_m * beam_flattop.B_rho_Tm / l_quad  # [T/m]

r_quadrupole = 0.065  # [m]
v_gap_dipole = 0.065  # [m]
h_gap_dipole = 0.09  # [m]


###############################################################################
# Now let's setup ``MAD-X`` and input a very simple lattice.

madx = Madx(stdout=False)
madx.input(
    f"""
circum = {circumference};
n_cells = {n_cells}; ! Number of cells 
lcell = {l_cell};
lq = {l_quad}; ! Length of a quadrupole
ldip = {l_bend};

! ELEMENT DEFINITIONS
! Define bending magnet as multipole, we have 4 bending magnets per cell
!mb:multipole, knl={{2.0*pi/(4*n_cells)}};

mb: sbend, l=ldip, angle=2.0*pi/(4*n_cells), apertype=ellipse, aperture= {{{h_gap_dipole}, {v_gap_dipole}}};
f = {f_m};

! Define quadrupoles as multipoles 
qf: multipole, knl:={{0,1/f+qtrim_f}}; 
qd: multipole, knl:={{0,-1/f+qtrim_d}};
qf: quadrupole, l=lq, K1:=1/f/lq  + qtrim_f/lq, apertype=ellipse, aperture={{{r_quadrupole}, {r_quadrupole}}}; 
qd: quadrupole, l=lq, K1:=-1/f/lq + qtrim_d/lq, apertype=ellipse, aperture={{{r_quadrupole}, {r_quadrupole}}};

! Define the sextupoles as multipole
!ATTENTION: must use knl:= and NOT knl= to match later! 
lsex = 0.00001; ! dummy length, only used in the sequence
msf: multipole, knl:={{0,0,ksf}};
msd: multipole, knl:={{0,0,ksd}};

! SEQUENCE DECLARATION
! Switch off the warning to limit outputs (use this option with moderation)
option, warn=false;
cas19: sequence, refer=centre, l=circum;
   start_machine: marker, at = 0;
   n = 1;
   while (n < n_cells+1) {{
    qf: qf,   at=(n-1)*lcell+ lq/2.0;
    msf: msf, at=(n-1)*lcell + lsex/2.0+lq/1.0;
    mb: mb,   at=(n-1)*lcell + 0.15*lcell;
    mb: mb,   at=(n-1)*lcell + 0.35*lcell;
    qd: qd,   at=(n-1)*lcell + 0.50*lcell+ lq/2.0;
    msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0+lq/1.0;
    mb: mb,   at=(n-1)*lcell + 0.65*lcell;
    mb: mb,   at=(n-1)*lcell + 0.85*lcell;
    n = n + 1;
}}
end_machine: marker at=circum;
endsequence;
option, warn=true;

! DEFINE BEAM PARAMETERS AND PROPERTIES
beam, particle=proton, sequence=cas19, energy={beam_injection.E_tot_GeV}, exn={beam_injection.en_x_m}, eyn={beam_injection.en_y_m}, sige={beam_injection.en_y_m};
use, sequence=cas19;
select, flag=twiss, column=apertype, aper_1, aper_2;

ksf=0;
ksd=0;
twiss;
"""
)

###############################################################################
# Now let's run an interpolation to be able to see the value of the optics functions
# inside the elements:

madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
madx.command.twiss()

###############################################################################
# We can now plot the beam enveloppe at injection, for a single cell:

BeamEnvelopePlotter.plot_envelope(madx, beam_injection, figsize=(18, 20))
plt.show()

###############################################################################
# In order to have a look at the enveloppe inside a single cell, we can specify *xlimits*.
# Here we will plot the enveloppe for the first cell only.

BeamEnvelopePlotter.plot_envelope(madx, beam_injection, xlimits=(0, l_cell), figsize=(18, 20))
plt.show()

###############################################################################
# And similarly at top energy:

BeamEnvelopePlotter.plot_envelope(madx, beam_flattop, xlimits=(0, l_cell), figsize=(18, 20))
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
#    - `~.cpymadtools.plotters`: `~.plotters.BeamEnvelopePlotter`, `~.plotters.BeamEnvelopePlotter.plot_envelope`
#    - `~.models.beam`: `~.models.beam.BeamParameters`