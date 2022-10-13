"""
.. _optics-beam:

Beam Optics
-----------

Module implementing various functionality for simple beam parameter calculations.
"""
import numpy as np

from scipy import constants

from pyhdtoolkit.models.beam import BeamParameters


def compute_beam_parameters(pc_gev: float, en_x_m: float, en_y_m: float, deltap_p: float) -> BeamParameters:
    """
    .. versionadded:: 0.12.0

    Calculates beam parameters from provided values, for *proton* particles. One can find
    an example use of this function in the :ref:`beam enveloppe <demo-beam-enveloppe>`
    example gallery.

    Args:
        pc_gev (float): particle momentum, in [GeV].
        en_x_m (float): horizontal emittance, in [m].
        en_y_m (float): vertical emittance, in [m].
        deltap_p (float): momentum deviation.

    Returns:
        A `~.optics.beam.BeamParameters` object with the calculated values.

    Example:
        .. code-block:: python

            >>> params = compute_beam_parameters(1.9, 5e-6, 5e-6, 2e-3)
            >>> print(params)
            Beam Parameters for particle of charge 1
            Beam momentum = 1.900 GeV/c
            Normalized x-emittance = 5.000 mm mrad
            Normalized y-emittance = 5.000 mm mrad
            Momentum deviation deltap/p = 0.002
            -> Beam total energy = 2.119 GeV
            -> Beam kinetic energy = 1.181 GeV
            -> Beam rigidity = 6.333 Tm
            -> Relativistic beta = 0.89663
            -> Relativistic gamma = 2.258
            -> Geometrical x emittance = 2.469 mm mrad
            -> Geometrical y emittance = 2.469 mm mrad
    """
    e0_gev = 0.9382720813
    e_tot_gev = np.sqrt(pc_gev**2 + e0_gev**2)
    gamma_r = e_tot_gev / e0_gev
    beta_r = pc_gev / np.sqrt(pc_gev**2 + e0_gev**2)

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
    .. versionadded:: 0.6.0

    Class to represent most useful particle beam attributes for ``MAD-X`` simulations.
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
            m0 (float): rest mass of the beam's particles in [MeV]. Defaults to that of a proton.
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
        return np.sqrt(1 + 1 / (self.gamma_rel**2))

    @property
    def brho(self) -> float:
        """Beam rigidity [T/m]."""
        return (1 / 0.3) * self.beta_rel * self.energy / constants.c

    @property
    def normalized_emittance(self) -> float:
        """Normalized emittance [m]."""
        return self.emittance * self.beta_rel * self.gamma_rel

    @property
    def rms_emittance(self) -> float:
        """Rms emittance [m]."""
        return self.emittance / (self.beta_rel * self.gamma_rel)

    def revolution_frequency(self, circumference: float = 26658.8832, speed: float = constants.c) -> float:
        """
        Returns the revolution frequency of the beam's particles around the accelerator.

        Args:
            circumference (float): the machine circumference in [m]. Defaults to that of the LHC.
            speed (float): the particles' speed in the machine, in [m/s]. Defaults to c.

        Returns:
            The revolution frequency, in [turns/s].
        """
        return self.beta_rel * speed / circumference

    def eta(self, alpha_p: float) -> float:
        """
        Returns the slip factor parameter :math:`\\eta`.

        .. note::
            :math:`\\eta = 0` at transition energy (:math:`\\eta < 0` above transition).

        Args:
            alpha_p (float): momentum compaction factor.

        Returns:
            The slip factor.
        """
        return (1 / (self.gamma_rel**2)) - alpha_p

    @staticmethod
    def gamma_transition(alpha_p: float) -> float:
        """
        Returns the relativistic :math:`\\gamma` corresponding to the transition energy.

        Args:
            alpha_p (float): momentum compaction factor.

        Returns:
            The relativistic :math:`\\gamma` value at the transition energy.
        """
        return np.sqrt(1 / alpha_p)
