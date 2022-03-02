"""
.. _cpymadtools-orbit:

Orbit Handling
--------------

Module with functions to perform ``MAD-X`` orbit setup through a `~cpymad.madx.Madx` object,
mainly for LHC and HLLHC machines.
"""
from typing import Dict, List, Tuple

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.constants import LHC_CROSSING_SCHEMES

# ----- Utilities ----- #


def lhc_orbit_variables() -> Tuple[List[str], Dict[str, str]]:
    """
    Get the variable names used for orbit setup in the (HL)LHC. Initial implementation
    credits go to :user:`Joschua Dilly <joschd>`.

    Returns:
        A `tuple` with a `list` of all orbit variables, and a `dict` of additional variables,
        that in the default configurations have the same value as another variable.

    Example:
        .. code-block:: python

            >>> variables, specials = lhc_orbit_variables()
    """
    logger.trace("Returning (HL)LHC orbit variables")
    on_variables = (
        "crab1",
        "crab5",  # exists only in HL-LHC
        "x1",
        "sep1",
        "o1",
        "oh1",
        "ov1",
        "x2",
        "sep2",
        "o2",
        "oe2",
        "a2",
        "oh2",
        "ov2",
        "x5",
        "sep5",
        "o5",
        "oh5",
        "ov5",
        "phi_IR5",
        "x8",
        "sep8",
        "o8",
        "a8",
        "sep8h",
        "x8v",
        "oh8",
        "ov8",
        "alice",
        "sol_alice",
        "lhcb",
        "sol_atlas",
        "sol_cms",
    )
    variables = [f"on_{var}" for var in on_variables] + [f"phi_IR{ir:d}" for ir in (1, 2, 5, 8)]
    special = {
        "on_ssep1": "on_sep1",
        "on_xx1": "on_x1",
        "on_ssep5": "on_sep5",
        "on_xx5": "on_x5",
    }
    return variables, special


def setup_lhc_orbit(madx: Madx, scheme: str = "flat", **kwargs) -> Dict[str, float]:
    """
    Automated orbit setup for (HL)LHC runs, for some default schemes. It is assumed that at
    least sequence and optics files have been called. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        scheme (str): the default scheme to apply, as defined in the ``LHC_CROSSING_SCHEMES``
            constant. Accepted values are keys of `LHC_CROSSING_SCHEMES`. Defaults to *flat*
            (every orbit variable to 0).
        **kwargs: Any standard crossing scheme variables (``on_x1``, ``phi_IR1``, etc). Values
            given here override the values in the default scheme configurations.

    Returns:
        A `dict` of all orbit variables set, and their values as set in the ``MAD-X`` globals.

    Example:
        .. code-block:: python

            >>> orbit_setup = setup_lhc_orbit(madx, scheme="lhc_top")
    """
    if scheme not in LHC_CROSSING_SCHEMES.keys():
        logger.error(f"Invalid scheme parameter, should be one of {LHC_CROSSING_SCHEMES.keys()}")
        raise ValueError("Invalid scheme parameter given")

    logger.debug("Getting orbit variables")
    variables, special = lhc_orbit_variables()

    scheme_dict = LHC_CROSSING_SCHEMES[scheme]
    final_scheme = {}

    for orbit_variable in variables:
        variable_value = kwargs.get(orbit_variable, scheme_dict.get(orbit_variable, 0))
        logger.trace(f"Setting orbit variable '{orbit_variable}' to {variable_value}")
        # Sets value in MAD-X globals & returned dict, taken from scheme dict or kwargs if provided
        madx.globals[orbit_variable] = final_scheme[orbit_variable] = variable_value

    for special_variable, copy_from in special.items():
        special_variable_value = kwargs.get(special_variable, madx.globals[copy_from])
        logger.trace(f"Setting special orbit variable '{special_variable}' to {special_variable_value}")
        # Sets value in MAD-X globals & returned dict, taken from a given global or kwargs if provided
        madx.globals[special_variable] = final_scheme[special_variable] = special_variable_value

    return final_scheme


def get_current_orbit_setup(madx: Madx) -> Dict[str, float]:
    """
    Get the current values for the (HL)LHC orbit variables. Initial implementation credits go to
    :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A `dict` of all orbit variables set, and their values as set in the ``MAD-X`` globals.

    Example:
        .. code-block:: python

            >>> orbit_setup = get_current_orbit_setup(madx)
    """
    logger.debug("Extracting orbit variables from global table")
    variables, specials = lhc_orbit_variables()
    return {orbit_variable: madx.globals[orbit_variable] for orbit_variable in variables + list(specials.keys())}


def correct_lhc_orbit(
    madx: Madx,
    sequence: str,
    orbit_tolerance: float = 1e-14,
    iterations: int = 3,
    mode: str = "micado",
    **kwargs,
) -> None:
    """
    Routine for orbit correction using ``MCB.*`` elements in the LHC. This uses the
    ``CORRECT`` command in ``MAD-X`` behind the scenes, refer to the
    `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_ for
    usage information.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        sequence (str): which sequence to use the routine on.
        orbit_tolerance (float): the tolerance for the correction. Defaults to 1e-14.
        iterations (int): the number of iterations of the correction to perform.
            Defaults to 3.
        mode (str): the method to use for the correction. Defaults to ``micado`` as in
            the `CORRECT` command.
        **kwargs: Any keyword argument that can be given to the ``MAD-X`` ``CORRECT``
            command, such as ``mode``, ``ncorr``, etc.

    Example:
        .. code-block:: python

            >>> correct_lhc_orbit(madx, sequence="lhcb1", plane="y")
    """
    logger.debug("Starting orbit correction")
    for default_kicker in ("kicker", "hkicker", "vkicker", "virtualcorrector"):
        logger.trace(f"Disabling default corrector class '{default_kicker}'")
        madx.command.usekick(sequence=sequence, status="off", class_=default_kicker)

    logger.debug("Selecting '^MCB.*' correctors")
    madx.command.usekick(sequence=sequence, status="on", pattern="^MCB.*")
    madx.command.usemonitor(sequence=sequence, status="on", class_="monitor")

    for _ in range(iterations):
        logger.trace("Doing orbit correction for Y then X plane")
        madx.twiss(chrom=True)
        madx.command.correct(sequence=sequence, plane="y", flag="ring", error=orbit_tolerance, mode=mode, **kwargs)
        madx.command.correct(sequence=sequence, plane="x", flag="ring", error=orbit_tolerance, mode=mode, **kwargs)
