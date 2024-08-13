"""

.. _demo-beam-enveloppe:

==============
Beam Enveloppe
==============

This example shows how to use the `~.plotting.envelope.plot_envelope` function
to visualise the particle beam's enveloppe in your machine.

In this example we will use a very simple lattice, hard-coded below.
"""
# sphinx_gallery_thumbnail_number = 1
import matplotlib.pyplot as plt
import numpy as np
from cpymad.madx import Madx

from pyhdtoolkit.plotting.envelope import plot_beam_envelope
from pyhdtoolkit.plotting.styles import _SPHINX_GALLERY_PARAMS
from pyhdtoolkit.utils import logging

logging.config_logger(level="error")
plt.rcParams.update(_SPHINX_GALLERY_PARAMS)  # for readability of this tutorial


###############################################################################
# Define relevant constants.

pc_GeV = 19  # Beam momentum [GeV]
B_rho_Tm = pc_GeV / 0.3  # Magnetic rigidity [Tm]
E_0_GeV = 0.9382720813  # proton rest mass [GeV]
E_tot_GeV = np.sqrt(pc_GeV**2 + E_0_GeV**2)

circumference = 500.0  # machine circumference [m]
n_cells = 25
l_quad = 0.5  # quadrupole length [m]
l_bend = 3.5  # dipole length [m]
l_cell = circumference / n_cells  # cell length [m]

f_m = l_cell / (2 * np.sqrt(2))  # pi/2 phase advance in thin lens approximation (no dipoles)

n_quadrupoles = 2 * n_cells
n_dipoles = 4 * n_cells  # four dipoles per cell
dipole_angle = 2 * np.pi / n_dipoles  # [rad]
dipole_field = dipole_angle * B_rho_Tm / l_bend  # [T]
quadrupole_gradient = 1 / f_m * B_rho_Tm / l_quad  # [T/m]

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

mb: sbend, l=ldip, angle=2.0*pi/(4*n_cells), apertype=ellipse, aperture={{{h_gap_dipole}, {v_gap_dipole}}};
f = {f_m};

! Define quadrupoles as multipoles
qf: multipole, knl:={{0,1/f+qtrim_f}};
qd: multipole, knl:={{0,-1/f+qtrim_d}};
qf: quadrupole, l=lq, K1:=1/f/lq  + qtrim_f/lq, apertype=ellipse, aperture={{{r_quadrupole}, {r_quadrupole}}};
qd: quadrupole, l=lq, K1:=-1/f/lq + qtrim_d/lq, apertype=ellipse, aperture={{{r_quadrupole}, {r_quadrupole}}};

! Define the sextupoles as multipole
! ATTENTION: must use knl:= and NOT knl= to match later!
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
beam, particle=proton, sequence=cas19, energy={E_tot_GeV}, exn=5e-6, eyn=5e-6, sige=5e-6;
use, sequence=cas19;
select, flag=twiss, column=apertype, aper_1, aper_2;

ksf=0;
ksd=0;
twiss;
"""
)

###############################################################################
# Now let's run an interpolation to be able to see the value of the optics functions
# inside the elements, this gives us higher resolution:

madx.command.select(flag="interpolate", class_="drift", slice_=4, range_="#s/#e")
madx.command.select(flag="interpolate", class_="quadrupole", slice_=8, range_="#s/#e")
madx.command.select(flag="interpolate", class_="sbend", slice_=10, range_="#s/#e")
madx.command.twiss()

###############################################################################
# We can now plot the beam enveloppe for the whole machine. Here notice we use
# the *scale* argument to convert the units to mm, this makes for nicer yticks
# values:
figure, axes = plt.subplots(2, 1, sharex=True, figsize=(16, 11))

# First let's plot 1 sigma and 2.5 sigma horizontal enveloppes
plot_beam_envelope(madx, "cas19", "x", nsigma=1, scale=1e3, ax=axes[0])
plot_beam_envelope(madx, "cas19", "horizontal", nsigma=2.5, scale=1e3, ax=axes[0])
plt.setp(axes[0], ylabel="X [mm]")
axes[0].legend()

# Then plot 1 sigma and 2.5 sigma vertical enveloppes
plot_beam_envelope(madx, "cas19", "y", nsigma=1, scale=1e3, ax=axes[1])
plot_beam_envelope(madx, "cas19", "vertical", nsigma=2.5, scale=1e3, ax=axes[1])
plt.setp(axes[1], xlabel="S [m]", ylabel="Y [mm]")
axes[1].legend()

plt.show()

###############################################################################
# Notice how the shading automatically adapts based on the *nsigma* argument.
# In order to have a look at the enveloppe in a specific region, we can give the
# *xlimits* argument. Here we will plot the horizontal enveloppe for the first
# 5 cells only.

fig, ax = plt.subplots(figsize=(16, 9))
plot_beam_envelope(madx, "cas19", "x", nsigma=1, scale=1e3, xlimits=(0, 5 * l_cell))
plot_beam_envelope(madx, "cas19", "x", nsigma=2.5, scale=1e3, xlimits=(0, 5 * l_cell))
plt.setp(ax, xlabel="S [m]", ylabel="X [mm]", title="First 5 Cells Horizontal Enveloppe")
ax.legend()
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
#    - `~.plotting.envelope`: `~.plotting.envelope.plot_beam_envelope`
