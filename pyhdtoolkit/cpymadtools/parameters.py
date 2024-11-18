"""
.. _cpymadtools-parameters:

Beam Parameters
---------------

Module with functions to fetch or compute different beam and
machine parameters through a `~cpymad.madx.Madx` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from pyhdtoolkit.models.madx import MADXBeam

if TYPE_CHECKING:
    from cpymad.madx import Madx

# ----- Utilities ----- #


def query_beam_attributes(madx: Madx, /) -> MADXBeam:
    """
    .. versionadded:: 0.12.0

    Returns all ``BEAM`` attributes from the ``MAD-X`` process based on
    the currently defined beam. If no beam has been defined at function call,
    then ``MAD-X`` will return all the default values. See the `MAD-X manual
    <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_ for details.

    Parameters
    ----------
    madx : cpymad.madx.Madx
        An instanciated `~cpymad.madx.Madx` object. Positional only.

    Returns
    -------
    MADXBeam
        A validated `~.models.madx.MADXBeam` object.

    Example
    -------
        .. code-block:: python

            beam_parameters = query_beam_attributes(madx)
    """
    logger.debug("Retrieving BEAM attributes from the MAD-X process")
    return MADXBeam(**dict(madx.beam))
