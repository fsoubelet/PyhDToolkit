"""
Module cpymadtools.helpers
--------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for performing different common operations on a cpymad.madx.Madx object.
"""

import numpy as np

from loguru import logger

try:
    from cpymad.madx import Madx
except ModuleNotFoundError:
    Madx = None


class LatticeMatcher:
    """
    A class with functions to perform MAD-X matchings.
    """

    @staticmethod
    def perform_tune_matching(
        cpymad_instance: Madx, sequence_name: str, q1_target: float, q2_target: float
    ) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will run an additional
        matching command to reach the provided values for tunes.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            sequence_name: name of the sequence you want to activate for the tune matching.
            q1_target: horizontal tune to match to.
            q2_target: vertical tune to match to.

        Returns:
            Nothing.
        """
        logger.debug(f"Starting matching sequence for target tunes {q1_target} and {q2_target}")
        cpymad_instance.input(
            f"""
!MATCHING SEQUENCE
match, sequence={sequence_name};
  vary, name=kqf, step=0.00001;
  vary, name=kqd, step=0.00001;
  global, sequence=CAS3, Q1={q1_target};
  global, sequence=CAS3, Q2={q2_target};
  Lmdif, calls=1000, tolerance=1.0e-21;
endmatch;
twiss;
"""
        )

    @staticmethod
    def perform_chroma_matching(
        cpymad_instance: Madx, sequence_name: str, dq1_target: float, dq2_target: float
    ) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will run an additional
        matching command to reach the provided values for chromaticities.

        Args:
            cpymad_instance: an instanciated `cpymad.madx.Madx` object.
            sequence_name: name of the sequence you want to activate for the tune matching.
            dq1_target: horizontal chromaticity to match to.
            dq2_target: vertical chromaticity to match to.

        Returns:
            Nothing.
        """
        logger.debug(
            f"Starting matching sequence for target chromaticities {dq1_target} and {dq2_target}"
        )
        cpymad_instance.input(
            f"""
!MATCHING SEQUENCE
match, sequence={sequence_name};
  vary, name=ksf, step=0.00001;
  vary, name=ksd, step=0.00001;
  global, sequence=CAS3, dq1={dq1_target};
  global, sequence=CAS3, dq2={dq2_target};
  Lmdif, calls=1000, tolerance=1.0e-21;
endmatch;
twiss;
"""
        )


class Parameters:
    """
    A class to compute different beam and machine parameters.
    """

    @staticmethod
    def beam_parameters(
        pc_GeV: float,
        en_x_m: float = 5e-6,
        en_y_m: float = 5e-6,
        deltap_p: float = 1e-3,
        verbose: bool = False,
    ):
        """Calculate beam parameters from provided values.

        Args:
            pc_GeV: particle momentum.
            en_x_m: horizontal emittance, in meters.
            en_y_m: vertical emittance, in meters.
            deltap_p: momentum deviation.
            verbose: bollean to print or not.

        Returns:
            A dictionnary with the calculated values.
        """
        E_0_GeV = 0.9382720813
        E_tot_GeV = np.sqrt(pc_GeV ** 2 + E_0_GeV ** 2)
        gamma_r = E_tot_GeV / E_0_GeV
        beta_r = pc_GeV / np.sqrt(pc_GeV ** 2 + E_0_GeV ** 2)

        parameters: dict = {
            "pc_GeV": pc_GeV,  # Particle momentum [GeV]
            "B_rho_Tm": 3.3356 * pc_GeV,  # Beam rigidity [T/m]
            "E_0_GeV": E_0_GeV,  # Rest mass energy [GeV]
            "E_tot_GeV": E_tot_GeV,  # Total beam energy [GeV]
            "E_kin_GeV": E_tot_GeV - E_0_GeV,  # Kinectic beam energy [GeV]
            "gamma_r": gamma_r,  # Relativistic gamma
            "beta_r": beta_r,  # Relativistic beta
            "en_x_m": en_x_m,  # Horizontal emittance [m]
            "en_y_m": en_y_m,  # Vertical emittance [m]
            "eg_x_m": en_x_m / gamma_r / beta_r,  # Horizontal geometrical emittance
            "eg_y_m": en_y_m / gamma_r / beta_r,  # Vertical geometrical emittance
            "deltap_p": deltap_p,  # Momentum deviation
        }

        if verbose:
            logger.debug("Outputing computed values")
            print(
                f"""Particle type: proton
            Beam momentum = {parameters["pc_GeV"]:2.3f} GeV/c
            Normalized x-emittance = {parameters["en_x_m"] * 1e6:2.3f} mm mrad
            Normalized y-emittance = {parameters["en_y_m"] * 1e6:2.3f} mm mrad
            Momentum deviation deltap/p = {parameters["deltap_p"]}
            -> Beam total energy = {parameters["E_tot_GeV"]:2.3f} GeV
            -> Beam kinetic energy = {parameters["E_kin_GeV"]:2.3f} GeV
            -> Beam rigidity = {parameters["B_rho_Tm"]:2.3f} Tm
            -> Relativistic beta = {parameters["beta_r"]:2.5f}
            -> Relativistic gamma = {parameters["gamma_r"]:2.3f}
            -> Geometrical x emittance = {parameters["eg_x_m"] * 1e6:2.3f} mm mrad
            -> Geometrical y emittance = {parameters["eg_y_m"] * 1e6:2.3f} mm mrad
            """
            )
        return parameters
