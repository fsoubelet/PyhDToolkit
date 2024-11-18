"""
.. _models-madx:

MAD-X Models
------------

Module with ``pydantic`` models to validate and store
data obtained by interacting with the ``MAD-X`` process
through `cpymad`.
"""

from enum import Enum

from pydantic import BaseModel, PositiveFloat, PositiveInt


class ParticleEnum(str, Enum):
    """
    .. versionadded:: 0.12.0

    Validator Enum defining the accepted particle
    names in ``MAD-X`` beams.
    """

    positron = "positron"
    electron = "electron"
    proton = "proton"
    antiproton = "antiproton"
    posmuon = "posmuon"  # positive muons
    negmuon = "negmuon"  # negative muons
    ions = "ions"


class MADXBeam(BaseModel):
    """
    .. versionadded:: 0.12.0

    Class to encompass and validate ``BEAM`` attributes
    from the ``MAD-X`` process.
    """

    particle: ParticleEnum  # The name of particles in the beam
    mass: PositiveFloat  # The rest mass of the particles in the beam in [GeV]
    charge: float  # The electrical charge of the particles in the beam in units of qp, the proton charge
    energy: PositiveFloat  # Total energy per particle in [GeV]
    pc: float  # Particle momentum times the speed of light, in [GeV]
    gamma: float  # Relativistic factor in [1]
    beta: float  # Relativistic beta in [1]
    brho: float  # Magnetic rigidity of the particles in [T.m]
    ex: float  # Horizontal emittance in [m]
    ey: float  # Vertical emittance in [m]
    et: float  # Longitudinal emittance in [m]
    exn: float  # Normalized horizontal emittance in [m] (beta * gamma * ex)
    eyn: float  # Normalized vertical emittance in [m]  *beta * gamma * ey)
    sigt: float  # The bunch length c σt in [m]  # noqa: RUF003
    sige: float  # The relative energy spread σE /E in [1].  # noqa: RUF003
    kbunch: PositiveInt  # The number of particle bunches in the machine in [1]
    npart: PositiveInt  # The number of particles per bunch in [1]
    bcurrent: float  # The bunch current, in [A]
    bunched: bool  # A logical flag. If set, the beam is treated as bunched whenever this makes sense
    radiate: bool  # A logical flag. If set, synchrotron radiation is considered in all dipole magnets
    bv: int  # integer specifying the direction of the particle movement in the beam line; either +1 or -1
