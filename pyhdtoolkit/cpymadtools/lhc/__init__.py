"""
.. _cpymadtools-lhc:

LHC-Specific Utilities
----------------------

Module with functions to perform ``MAD-X`` actions through a
`~cpymad.madx.Madx` object, that are specific to the ``LHC``
and ``HLLHC`` machines.

Important
---------
    The functions documented below are shown as coming from private
    modules (**_coupling**, **_misc**, **_setup** etc). They are all
    accessible at the `pyhdtoolkit.cpymadtools.lhc` level, but one is
    free to import and use them directly from the private modules should
    they wish to do so. In short, the two options below are both valid:

    .. tab-set::

        .. tab-item:: Importing from the lhc module

            .. code-block:: python
        
                from pyhdtoolkit.cpymadtools.lhc import LHCSetup
                # use this now

        .. tab-item:: Importing from the private module

            .. code-block:: python
        
                from pyhdtoolkit.cpymadtools.lhc._setup import LHCSetup
                # use this now
"""

from ._coupling import get_lhc_bpms_twiss_and_rdts
from ._elements import add_markers_around_lhc_ip, install_ac_dipole_as_kicker, install_ac_dipole_as_matrix
from ._errors import misalign_lhc_ir_quadrupoles, misalign_lhc_triplets
from ._misc import (
    get_lhc_bpms_list,
    get_lhc_tune_and_chroma_knobs,
    get_sizes_at_ip,
    make_sixtrack_output,
    reset_lhc_bump_flags,
)
from ._powering import (
    apply_lhc_colinearity_knob,
    apply_lhc_colinearity_knob_delta,
    apply_lhc_coupling_knob,
    apply_lhc_rigidity_waist_shift_knob,
    carry_colinearity_knob_over,
    deactivate_lhc_arc_sextupoles,
    power_landau_octupoles,
    switch_magnetic_errors,
    vary_independent_ir_quadrupoles,
)
from ._queries import (
    get_current_orbit_setup,
    get_magnets_powering,
    query_arc_correctors_powering,
    query_triplet_correctors_powering,
)
from ._routines import correct_lhc_global_coupling, correct_lhc_orbit, do_kmodulation
from ._setup import (
    LHCSetup,
    lhc_orbit_variables,
    make_lhc_beams,
    make_lhc_thin,
    prepare_lhc_run2,
    prepare_lhc_run3,
    re_cycle_sequence,
    setup_lhc_orbit,
)
from ._twiss import get_ips_twiss, get_ir_twiss
