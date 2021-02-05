"""
Module cpymadtools.generators
-----------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for generating different lattices for cpymad.madx.Madx input.
"""


# ----- Utlites ----- #


class LatticeGenerator:
    """
    A simple class to handle said functions.
    """

    @staticmethod
    def generate_base_cas_lattice() -> str:
        """
        Simple function to help unclutter the notebook.

        Returns:
            A string you can input into your `cpymad.madx.Madx` object.
        """
        return """
option, -info, -warn;
TITLE, ’CAS2019 Project Team 3’;

! PARAMETERS
circumference = 1000.0;
ncell = 24;
lcell = circumference/ncell;
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
CAS3: sequence, refer=centre, l=circumference;
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
end_machine: marker at=circumference;
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

    @staticmethod
    def generate_onesext_cas_lattice() -> str:
        """
        Simple function to help unclutter the notebook.

        Returns:
            A string you can input into your `cpymad.madx.Madx` object.
        """
        return """
option, -info, -warn;
TITLE, ’CAS2019 Project Team 3’;

! PARAMETERS
circumference = 1000.0;
ncell = 24;
lcell = circumference/ncell;
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
CAS3: sequence, refer=centre, l=circumference;
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
end_machine: marker at=circumference;
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

    @staticmethod
    def generate_oneoct_cas_lattice() -> str:
        """
        Simple function to help unclutter the notebook.

        Returns:
            A string you can input into your `cpymad.madx.Madx` object.
        """
        return """
option, -info, -warn;
TITLE, ’CAS2019 Project Team 3’;

! PARAMETERS
circumference = 1000.0;
ncell = 24;
lcell = circumference/ncell;
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
CAS3: sequence, refer=centre, l=circumference;
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
end_machine: marker at=circumference;
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

    @staticmethod
    def generate_tripleterrors_study_reference() -> str:
        """
        Generate generic script for reference Twiss, to use in a `cpymad.madx.Madx` object.

        Returns:
            A string you can input into your `cpymad.madx.Madx` object.
        """
        return """
!####################### Make macros available #######################

option, -echo, -warn, -info;
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/beta_beat.macros.madx";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/lhc.macros.madx";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/hllhc.macros.madx";

title, "HLLHC Triplet TFErrors to Beta-Beating";

!####################### Call optics files #######################

call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/model/accelerators/lhc/hllhc1.3/lhcrunIII.seq";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/model/accelerators/lhc/hllhc1.3/main.seq";
call, file = "/afs/cern.ch/eng/lhc/optics/V6.5/errors/Esubroutines.madx";

!####################### Calling modifiers for 15cm optics #######################

call, file = "/afs/cern.ch/eng/lhc/optics/HLLHCV1.3/opt_150_150_150_150.madx";

!####################### Create beam #######################

exec, define_nominal_beams();

!####################### Flatten and set START point at ? #######################

exec, cycle_sequences();

!####################### Default crossing scheme #######################

exec, set_default_crossing_scheme();

!####################### Selecting to use Beam 1 #######################

use, period = LHCB1;

!####################### Tune matching and Twiss nominal #######################

option, echo, warn, info;
exec, match_tunes(62.31, 60.32, 1);     ! Since we're using beam 1
twiss;
"""

    @staticmethod
    def generate_tripleterrors_study_tferror_job(rand_seed: str, tf_error: str) -> str:
        """
        Generate generic script for tf_error Twiss, to use in a `cpymad.madx.Madx` object.

        Args:
            rand_seed (str): the random seed to provide MAD for the errors distributions.
            tf_error (str): the misalignment error value (along the s axis).

        Returns:
            A string you can input into your `cpymad.madx.Madx` object.
        """
        return f"""
!####################### Make macros available #######################

option, -echo, -warn, -info;
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/beta_beat.macros.madx";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/lhc.macros.madx";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/hllhc.macros.madx";

title, "HLLHC Triplet TFErrors to Beta-Beating";

!####################### Call optics files #######################

call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/model/accelerators/lhc/hllhc1.3/lhcrunIII.seq";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/model/accelerators/lhc/hllhc1.3/main.seq";
call, file = "/afs/cern.ch/eng/lhc/optics/V6.5/errors/Esubroutines.madx";

!####################### Calling modifiers for 15cm optics #######################

call, file = "/afs/cern.ch/eng/lhc/optics/HLLHCV1.3/opt_150_150_150_150.madx";

!####################### Create beam #######################

exec, define_nominal_beams();

!####################### Flatten and set START point at ? #######################

exec, cycle_sequences();

!####################### Default crossing scheme #######################

exec, set_default_crossing_scheme();

!####################### Selecting to use Beam 1 #######################

use, period = LHCB1;

!####################### Tune matching and Twiss nominal #######################

option, echo, warn, info;
exec, match_tunes(62.31, 60.32, 1);     ! Since we're using beam 1
exec, do_twiss_elements(LHCB1, "./twiss_nominal.dat", 0.0);

!####################### For field errors #######################

eoption, add, seed = {rand_seed};  ! Different seed every time
select, flag=error, clear;
select, flag=error, pattern = ^MQXF.*[RL][15]; ! Only triplets quadrupoles around IP1 and IP5
GCUTR = 3;                 ! Cut gaussians at 3 sigma
Rr = 0.05;             ! Radius for field errors (??)
ON_B2R = 1;            ! Activate field errors
B2r = {tf_error};       ! Set field errors magnitude -> Units of B2 error (will be in 1E-4)
exec, SetEfcomp_Q;     ! Assign field errors

!####################### Saving errors to file #######################

!esave, file="./errors_file.dat"; ! Will save the errors of chosen type.

!####################### Tune matching and Twiss with errors #######################

exec, match_tunes(62.31, 60.32, 1);
exec, do_twiss_elements(LHCB1, "./twiss_errors.dat", 0.0);
"""

    @staticmethod
    def generate_tripleterrors_study_mserror_job(rand_seed: str, ms_error: str) -> str:
        """
        Generate generic script for ms_error Twiss, to use in a `cpymad.madx.Madx` object.

        Args:
            rand_seed (str): the random seed to provide MAD for the errors distributions.
            ms_error (str): the misalignment error value (along the s axis).

        Returns:
            A string you can input into your `cpymad.madx.Madx` object.
        """
        return f"""
!####################### Make macros available #######################

option, -echo, -warn, -info;
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/beta_beat.macros.madx";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/lhc.macros.madx";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/madx/lib/hllhc.macros.madx";

title, "HLLHC Triplet MSErrors to Beta-Beating";

!####################### Call optics files #######################

call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/model/accelerators/lhc/hllhc1.3/lhcrunIII.seq";
call, file = "/afs/cern.ch/work/f/fesoubel/public/Repositories/Beta-Beat.src/model/accelerators/lhc/hllhc1.3/main.seq";
call, file = "/afs/cern.ch/eng/lhc/optics/V6.5/errors/Esubroutines.madx";

!####################### Calling modifiers for 15cm optics #######################

call, file = "/afs/cern.ch/eng/lhc/optics/HLLHCV1.3/opt_150_150_150_150.madx";

!####################### Create beam #######################

exec, define_nominal_beams();

!####################### Flatten and set START point at ? #######################

exec, cycle_sequences();

!####################### Default crossing scheme #######################

exec, set_default_crossing_scheme();

!####################### Selecting to use Beam 1 #######################

use, period = LHCB1;

!####################### Tune matching and Twiss nominal #######################

option, echo, warn, info;
exec, match_tunes(62.31, 60.32, 1);     ! Since we're using beam 1
exec, do_twiss_elements(LHCB1, "./twiss_nominal.dat", 0.0);

!####################### For longitudinal missalignments #######################

eoption, add, seed = {rand_seed};  ! Different seed every time
select, flag=error, clear;
select, flag=error, pattern = ^MQXF.*[RL][15]; ! Only triplets quadrupoles around IP1 and IP5
GCUTR = 3;                 ! Cut gaussians at 3 sigma
ealign, ds := {ms_error} * 1E-3 * TGAUSS(GCUTR);  ! Gaussian missalignments in meters

!####################### Saving errors to file #######################

!esave, file="./errors_file.dat"; ! Will save the errors of chosen type.

!####################### Tune matching and Twiss with errors #######################

exec, match_tunes(62.31, 60.32, 1);
exec, do_twiss_elements(LHCB1, "./twiss_errors.dat", 0.0);
"""
