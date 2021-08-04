"""
Module models.beam
------------------

Created on 2021.08.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with `pydantic` models to validate and store data structures used in the `beam` module.
"""
from typing import Optional

from pydantic import BaseModel


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
