"""
Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for generating different lattices for cpymad.MadX input.
"""


class LatticeGenerator:
    """
    A simple class to handle said functions.
    """

    @staticmethod
    def generate_base_cas_lattice() -> str:
        """
        Simple function to help unclutter the notebook.
        :return: string you can input into your cpymadtools instance.
        """
        mystring = """
option, -info, -warn;
TITLE, ’CAS2019 Project Team 3’;

! PARAMETERS
circum = 1000.0;
ncell = 24;
lcell = circum/ncell;
lq = 3.00;
angleBending = 2.0*pi/(4*ncell);

! STRENGTHS
kqf = 0.0228 * lq;
kqd = -0.0228 * lq;
lsex = 0.00001;

! ELEMENTS
mb:multipole, knl:={angleBending};
qf: multipole, knl:={0, kqf}; 
qd: multipole, knl:={0, kqd};
msf: multipole, knl:={0, 0, ksf};
msd: multipole, knl:={0, 0, ksd};

! DECLARE SEQUENCE
CAS3: sequence, refer=centre, l=circum;
   start_machine: marker, at = 0;
   n = 1;
   while (n < ncell+1) {
    qf: qf,   at=(n-1)*lcell;
    msf: msf, at=(n-1)*lcell + lsex/2.0;
    mb: mb,   at=(n-1)*lcell + 0.15*lcell;
    mb: mb,   at=(n-1)*lcell + 0.35*lcell;
    qd: qd,   at=(n-1)*lcell + 0.50*lcell;
    msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0;
    mb: mb,   at=(n-1)*lcell + 0.65*lcell;
    mb: mb,   at=(n-1)*lcell + 0.85*lcell;
    at=(n-1)*lcell;
    n = n + 1;
}
end_machine: marker at=circum;
endsequence;

! MAKE BEAM
beam, particle=proton, sequence=CAS3, energy=20.0;

! ACTIVATE SEQUENCE
use, sequence=CAS3;

select,flag=interpolate, class=drift, slice=5, range=#s/#e;

ksf = 0;
ksd = 0;

! INTERPOLATE
select, flag=interpolate, class=drift, slice=10, range=#s/#e;
select, flag=interpolate, class=quadrupole, slice=5, range=#s/#e;
select, flag=interpolate, class=sbend, slice=10, range=#s/#e;

! TWISS
select,flag=twiss, clear;
select,flag=twiss, column=name ,s, x, y, betx, bety, mux, muy, dx, dy;
twiss;
    """
        return mystring

    @staticmethod
    def generate_onesext_cas_lattice() -> str:
        """
        Simple function to help unclutter the notebook.
        :return: string you can input into your cpymadtools instance.
        """
        mystring = """
option, -info, -warn;
TITLE, ’CAS2019 Project Team 3’;

! PARAMETERS
circum = 1000.0;
ncell = 24;
lcell = circum/ncell;
lq = 3.00;
angleBending = 2.0*pi/(4*ncell);

! STRENGTHS
kqf = 0.0228 * lq;
kqd = -0.0228 * lq;
lsex = 0.00001;
ks1 = 0;
ks2 = 0;

! ELEMENTS
mb:multipole, knl:={angleBending};
qf: multipole, knl:={0, kqf}; 
qd: multipole, knl:={0, kqd};
msf: multipole, knl:={0, 0, ksf};
msd: multipole, knl:={0, 0, ksd};

mof: multipole, knl:={0, 0, ks1, 0};
mod: multipole, knl:={0, 0, ks2, 0};

! DECLARE SEQUENCE
CAS3: sequence, refer=centre, l=circum;
   start_machine: marker, at = 0;
   n = 1;
   qf: qf,   at=(n-1)*lcell;
   msf: msf, at=(n-1)*lcell + lsex/2.0;
   mof: mof, at=(n-1)*lcell + 3*lsex/2.0;
   mb: mb,   at=(n-1)*lcell + 0.15*lcell;
   mb: mb,   at=(n-1)*lcell + 0.35*lcell;
   qd: qd,   at=(n-1)*lcell + 0.50*lcell;
   msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0;
   mod: mod, at=(n-1)*lcell + 0.50*lcell + 3*lsex/2.0;
   mb: mb,   at=(n-1)*lcell + 0.65*lcell;
   mb: mb,   at=(n-1)*lcell + 0.85*lcell;
   at=(n-1)*lcell;
   n = n + 1;
   while (n < ncell+1) {
    qf: qf,   at=(n-1)*lcell;
    msf: msf, at=(n-1)*lcell + lsex/2.0;
    mb: mb,   at=(n-1)*lcell + 0.15*lcell;
    mb: mb,   at=(n-1)*lcell + 0.35*lcell;
    qd: qd,   at=(n-1)*lcell + 0.50*lcell;
    msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0;
    mb: mb,   at=(n-1)*lcell + 0.65*lcell;
    mb: mb,   at=(n-1)*lcell + 0.85*lcell;
    at=(n-1)*lcell;
    n = n + 1;
   }
end_machine: marker at=circum;
endsequence;

! MAKE BEAM
beam, particle=proton, sequence=CAS3, energy=20.0;

! ACTIVATE SEQUENCE
use, sequence=CAS3;

select,flag=interpolate, class=drift, slice=5, range=#s/#e;

ksf = 0;
ksd = 0;

! INTERPOLATE
select, flag=interpolate, class=drift, slice=10, range=#s/#e;
select, flag=interpolate, class=quadrupole, slice=5, range=#s/#e;
select, flag=interpolate, class=sbend, slice=10, range=#s/#e;

! TWISS
select,flag=twiss, clear;
select,flag=twiss, column=name ,s, x, y, betx, bety, mux, muy, dx, dy;
twiss;
    """
        return mystring

    @staticmethod
    def generate_oneoct_cas_lattice() -> str:
        """
        Simple function to help unclutter the notebook.
        :return: string you can input into your cpymadtools instance.
        """
        mystring = """
option, -info, -warn;
TITLE, ’CAS2019 Project Team 3’;

! PARAMETERS
circum = 1000.0;
ncell = 24;
lcell = circum/ncell;
lq = 3.00;
angleBending = 2.0*pi/(4*ncell);

! STRENGTHS
kqf = 0.0228 * lq;
kqd = -0.0228 * lq;
lsex = 0.00001;
ks1 = 0;
ks2 = 0;

! ELEMENTS
mb:multipole, knl:={angleBending};
qf: multipole, knl:={0, kqf}; 
qd: multipole, knl:={0, kqd};
msf: multipole, knl:={0, 0, ksf};
msd: multipole, knl:={0, 0, ksd};

mof: multipole, knl:={0, 0, 0, koct};
mod: multipole, knl:={0, 0, 0, 0};

! DECLARE SEQUENCE
CAS3: sequence, refer=centre, l=circum;
   start_machine: marker, at = 0;
   n = 1;
   qf: qf,   at=(n-1)*lcell;
   msf: msf, at=(n-1)*lcell + lsex/2.0;
   mof: mof, at=(n-1)*lcell + 3*lsex/2.0;
   mb: mb,   at=(n-1)*lcell + 0.15*lcell;
   mb: mb,   at=(n-1)*lcell + 0.35*lcell;
   qd: qd,   at=(n-1)*lcell + 0.50*lcell;
   msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0;
   mod: mod, at=(n-1)*lcell + 0.50*lcell + 3*lsex/2.0;
   mb: mb,   at=(n-1)*lcell + 0.65*lcell;
   mb: mb,   at=(n-1)*lcell + 0.85*lcell;
   at=(n-1)*lcell;
   n = n + 1;
   while (n < ncell+1) {
    qf: qf,   at=(n-1)*lcell;
    msf: msf, at=(n-1)*lcell + lsex/2.0;
    mb: mb,   at=(n-1)*lcell + 0.15*lcell;
    mb: mb,   at=(n-1)*lcell + 0.35*lcell;
    qd: qd,   at=(n-1)*lcell + 0.50*lcell;
    msd: msd, at=(n-1)*lcell + 0.50*lcell + lsex/2.0;
    mb: mb,   at=(n-1)*lcell + 0.65*lcell;
    mb: mb,   at=(n-1)*lcell + 0.85*lcell;
    at=(n-1)*lcell;
    n = n + 1;
   }
end_machine: marker at=circum;
endsequence;

! MAKE BEAM
beam, particle=proton, sequence=CAS3, energy=20.0;

! ACTIVATE SEQUENCE
use, sequence=CAS3;

select,flag=interpolate, class=drift, slice=5, range=#s/#e;

ksf = 0;
ksd = 0;

! INTERPOLATE
select, flag=interpolate, class=drift, slice=10, range=#s/#e;
select, flag=interpolate, class=quadrupole, slice=5, range=#s/#e;
select, flag=interpolate, class=sbend, slice=10, range=#s/#e;

! TWISS
select,flag=twiss, clear;
select,flag=twiss, column=name ,s, x, y, betx, bety, mux, muy, dx, dy;
twiss;
    """
        return mystring


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
