"""
Module models.beam
------------------

Created on 2021.08.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with `pydantic` models to validate and store data structures used in the `beam` module.
"""
from typing import Optional

from pydantic import BaseModel, PositiveInt


class MADXBeam(BaseModel):
    """
    This is a class to encompass and manipulate
    """

    particle: str
    mass: float
    charge: float
    energy: float  # Total energy per particle in [GeV]
    pc: float  # Particle momentum times the speed of light, in [GeV]
    gamma: float  # Relativistic factor in [1]
    beta: float  # Relativistic beta in [1]
    brho: float  # Magnetic rigidity of the particles in [T.m]
    ex: float  # Horizontal emittance in [m]
    ey: float  # Vertical emittance in [m]
    et: float  # Longitudinal emittance in [m]
    exn: float  # Normalized horizontal emittance in [m] (beta * gamma * ex)
    eyn: float  # Normalized vertical emittance in [m]  *beta * gamma * ey)
    sigt: float  # The bunch length c σt in [m]
    sige: float  # The relative energy spread σE /E in [1].
    kbunch: PositiveInt  # The number of particle bunches in the machine in [1]
    npart: PositiveInt  # The number of particles per bunch in [1]
    bcurrent: float  # The bunch current, in [A]
    bunched: bool  # A logical flag. If set, the beam is treated as bunched whenever this makes sense
    radiate: bool  # A logical flag. If set, synchrotron radiation is considered in all dipole magnets
    bv: int  # integer specifying the direction of the particle movement in the beam line; either +1 or -1


class BeamParameters(BaseModel):
    """
    Class to encompass, validate and manipulate properties of a particle beam.
    """

    pc_GeV: Optional[float]  # Beam momentum [GeV]
    B_rho_Tm: Optional[float]  # Beam rigidity [T/m]
    E_0_GeV: Optional[float]  # Particle rest mass energy [GeV]
    charge: Optional[float]  # Particle charge in [e]
    E_tot_GeV: Optional[float]  # Total beam energy [GeV]
    E_kin_GeV: Optional[float]  # Kinectic beam energy [GeV]
    gamma_r: Optional[float]  # Relativistic gamma
    beta_r: Optional[float]  # Relativistic beta
    en_x_m: Optional[float]  # Horizontal normalized emittance [m]
    en_y_m: Optional[float]  # Vertical normalized emittance [m]
    eg_x_m: Optional[float]  # Horizontal geometrical emittance
    eg_y_m: Optional[float]  # Vertical geometrical emittance
    deltap_p: Optional[float]  # Momentum deviation
