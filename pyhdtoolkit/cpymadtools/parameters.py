"""
Module cpymadtools.parameters
-----------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to compute different beam and machine parameters.
"""

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.models.madx import MADXBeam

# ----- Utilities ----- #


def query_beam_attributes(madx: Madx) -> MADXBeam:
    """
    Returns all `BEAM` attributes from the `MAD-X` process based on the currently defined beam. If no beam
    has been defined at function call, then `MAD-X` will return all the default values. See the `MAD-X`
    manual for details.

    Args:
        madx (cpymad.madx.Madx): an instanciated cpymad Madx object.

    Returns:
        A validated `MADXBeam` object.
    """
    logger.info("Retrieving BEAM attributes from the MAD-X process")
    return MADXBeam(**dict(madx.beam))
