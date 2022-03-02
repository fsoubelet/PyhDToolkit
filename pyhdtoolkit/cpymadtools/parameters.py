"""
.. _cpymadtools-parameters:

Parameters
----------

Module with functions to fetch or compute different beam and machine parameters
through a `~cpymad.madx.Madx` object.
"""

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.models.madx import MADXBeam

# ----- Utilities ----- #


def query_beam_attributes(madx: Madx) -> MADXBeam:
    """
    Returns all ``BEAM`` attributes from the ``MAD-X`` process based on the currently defined
    beam. If no beam has been defined at function call, then ``MAD-X`` will return all the default
    values. See the `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_
    for details.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.

    Returns:
        A validated `~.models.madx.MADXBeam` object.
    """
    logger.debug("Retrieving BEAM attributes from the MAD-X process")
    return MADXBeam(**dict(madx.beam))
