"""
Module models.beam
------------------

Created on 2021.08.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with `pydantic` models to validate and store data structures used in the `beam` module.
"""
from math import sqrt
from typing import Optional

from pydantic import BaseModel


class BeamParameters(BaseModel):
    """
    Class to encompass, validate and manipulate properties of a particle beam.
    """

    pc_GeV: Optional[float]  # Beam momentum [GeV]
    E_0_GeV: Optional[float] = 0.9382720813  # Particle rest mass energy [GeV], defaults to that of a proton
    charge: Optional[float] = 1  # Particle charge in [e], defaults to that of a proton
    en_x_m: Optional[float]  # Horizontal normalized emittance [m]
    en_y_m: Optional[float]  # Vertical normalized emittance [m]
    deltap_p: Optional[float]  # Momentum deviation

    @property
    def B_rho_Tm(self) -> float:
        """Beam rigidity [T/m]"""
        return self.pc_GeV / 0.3

    @property
    def E_tot_GeV(self) -> float:
        """Total beam energy [GeV]"""
        return sqrt(self.pc_GeV ** 2 + self.E_0_GeV ** 2)

    @property
    def E_kin_GeV(self) -> float:
        """Total beam energy [GeV]"""
        return self.E_tot_GeV - self.E_0_GeV

    @property
    def gamma_r(self) -> float:
        """Relativistic gamma"""
        return self.E_tot_GeV / self.E_0_GeV

    @property
    def beta_r(self) -> float:
        """Relativistic beta"""
        return self.pc_GeV / sqrt(self.pc_GeV ** 2 + self.E_0_GeV ** 2)

    @property
    def eg_x_m(self) -> float:
        """Horizontal geometrical emittance"""
        return self.en_x_m / self.gamma_r / self.beta_r

    @property
    def eg_y_m(self) -> float:
        """Vertical geometrical emittance"""
        return self.en_y_m / self.gamma_r / self.beta_r

    def __repr__(self) -> str:
        return (
            f"Beam Parameters for particle of charge {self.charge} \n"
            + f"Beam momentum = {self.pc_GeV:2.3f} GeV/c \n"
            + f"Normalized x-emittance = {self.en_x_m * 1e6:2.3f} mm mrad \n"
            + f"Normalized y-emittance = {self.en_y_m * 1e6:2.3f} mm mrad \n"
            + f"Momentum deviation deltap/p = {self.deltap_p} \n"
            + f"  -> Beam total energy = {self.E_tot_GeV:2.3f} GeV \n"
            + f"  -> Beam kinetic energy = {self.E_kin_GeV:2.3f} GeV \n"
            + f"  -> Beam rigidity = {self.B_rho_Tm:2.3f} Tm \n"
            + f"  -> Relativistic beta = {self.beta_r:2.5f} \n"
            + f"  -> Relativistic gamma = {self.gamma_r:2.3f} \n"
            + f"  -> Geometrical x emittance = {self.eg_x_m * 1e6:2.3f} mm mrad \n"
            + f"  -> Geometrical y emittance = {self.eg_y_m * 1e6:2.3f} mm mrad \n"
        )

    def __str__(self) -> str:
        return f""
