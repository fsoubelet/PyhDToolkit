"""
Module optics.beam
------------------

Created on 2020.11.11
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 module implementing various functionality for simple beam parameter calculations.
"""
import numpy as np

from scipy import constants

from pyhdtoolkit.models.beam import BeamParameters


def compute_beam_parameters(pc_gev: float, en_x_m: float, en_y_m: float, deltap_p: float) -> BeamParameters:
    """
    Calculate beam parameters from provided values, for proton particles.

    Args:
        pc_gev (float): particle momentum.
        en_x_m (float): horizontal emittance, in meters.
        en_y_m (float): vertical emittance, in meters.
        deltap_p (float): momentum deviation.

    Returns:
        A `BeamParameters` object with the calculated values.
    """
    e0_gev = 0.9382720813
    e_tot_gev = np.sqrt(pc_gev ** 2 + e0_gev ** 2)
    gamma_r = e_tot_gev / e0_gev
    beta_r = pc_gev / np.sqrt(pc_gev ** 2 + e0_gev ** 2)

    return BeamParameters(
        pc_GeV=pc_gev,
        B_rho_Tm=3.3356 * pc_gev,
        E_0_GeV=e0_gev,
        E_tot_GeV=e_tot_gev,
        E_kin_GeV=e_tot_gev - e0_gev,
        gamma_r=gamma_r,
        beta_r=beta_r,
        en_x_m=en_x_m,
        en_y_m=en_y_m,
        eg_x_m=en_x_m / gamma_r / beta_r,
        eg_y_m=en_y_m / gamma_r / beta_r,
        deltap_p=deltap_p,
    )


class Beam:
    """
    Class to encompass functionality.
    """

    def __init__(
        self,
        energy: float,
        emittance: float,
        m0: float = constants.physical_constants["proton mass energy equivalent in MeV"][0],
    ) -> None:
        """
        Args:
            energy (float): energy of the particles in your beam, in [GeV].
            emittance (float): beam emittance, in [m].
            m0 (float): rest mass of the beam's particles in MeV. Defaults to that of a proton.
        """
        self.energy = energy
        self.emittance = emittance
        self.rest_mass = m0

    @property
    def gamma_rel(self) -> float:
        """Relativistic gamma."""
        return (1e3 * self.energy + self.rest_mass) / self.rest_mass

    @property
    def beta_rel(self) -> float:
        """Relativistic beta."""
        return np.sqrt(1 + 1 / (self.gamma_rel ** 2))

    @property
    def brho(self) -> float:
        """Beam rigidity [T/m]."""
        return (1 / 0.3) * self.beta_rel * self.energy / constants.c

    @property
    def normalized_emittance(self) -> float:
        """
        Normalized emittance [m].
        """
        return self.emittance * self.beta_rel * self.gamma_rel

    @property
    def rms_emittance(self) -> float:
        """
        Rms emittance [m].
        """
        return self.emittance / (self.beta_rel * self.gamma_rel)

    def revolution_frequency(self, circumference: float = 26658.8832, speed: float = constants.c) -> float:
        """
        Revolution frequency.

        Args:
            circumference (float): the machine circumference in [m]. Defaults to that of the LHC.
            speed (float): the particles' speed in the machine, in [m/s]. Defaults to c.
        """
        return self.beta_rel * speed / circumference

    def eta(self, alpha_p: float) -> float:
        """
        Slip factor parameter eta: eta = 0 at transition energy (eta < 0 above transition).

        Args:
            alpha_p (float): momentum compaction factor.
        """
        return (1 / (self.gamma_rel ** 2)) - alpha_p

    @staticmethod
    def gamma_transition(alpha_p: float) -> float:
        """
        Relativistic gamma corresponding to the transition energy.

        Args:
            alpha_p (float): momentum compaction factor.
        """
        return np.sqrt(1 / alpha_p)
