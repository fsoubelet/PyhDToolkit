"""
Module optics.beam
------------------

Created on 2020.11.11
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 module implementing various functionality for simple beam parameter calculations.
"""
import numpy as np

from scipy import constants


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
