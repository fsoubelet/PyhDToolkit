"""
cpymadtools package
~~~~~~~~~~~~~~~~~~~
cpymadtools is a collection of utilities that integrate within my workflow with the `cpymad` library.

:copyright: (c) 2019 by Felix Soubelet.
:license: MIT, see LICENSE for more details.
"""

from .errors import misalign_lhc_ir_quadrupoles, misalign_lhc_triplets, switch_magnetic_errors
from .generators import LatticeGenerator
from .latwiss import plot_latwiss, plot_machine_survey
from .matching import get_closest_tune_approach, get_lhc_tune_and_chroma_knobs, match_tunes_and_chromaticities
from .orbit import correct_lhc_orbit, get_current_orbit_setup, lhc_orbit_variables, setup_lhc_orbit
from .parameters import query_beam_attributes
from .plotters import AperturePlotter, DynamicAperturePlotter, PhaseSpacePlotter, TuneDiagramPlotter
from .ptc import get_amplitude_detuning, get_rdts
from .special import (
    apply_lhc_colinearity_knob,
    apply_lhc_coupling_knob,
    apply_lhc_rigidity_waist_shift_knob,
    deactivate_lhc_arc_sextupoles,
    install_ac_dipole,
    make_lhc_beams,
    make_lhc_thin,
    make_sixtrack_output,
    power_landau_octupoles,
    re_cycle_sequence,
    vary_independent_ir_quadrupoles,
)
from .track import track_single_particle
from .tune import make_footprint_table
from .twiss import get_ips_twiss, get_ir_twiss, get_twiss_tfs
from .utils import get_table_tfs
