"""
Module cpymadtools.helpers
--------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for performing different common operations on a cpymad.madx.Madx object.
"""
from typing import Dict, List

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
        cpymad_instance: Madx,
        sequence_name: str,
        q1_target: float,
        q2_target: float,
        variables: List[str] = ["kqf", "kqd"],
    ) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will run an additional
        matching command to reach the provided values for tunes.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            sequence_name (str): name of the sequence you want to activate for the tune matching.
            q1_target (float): horizontal tune to match to.
            q2_target (float): vertical tune to match to.
            variables (List[str]): the variables names to 'vary' in the MADX routine. Defaults to
                ["kqf", "ksd"] as it is a common name for quadrupole strengths (foc / defoc).
        """
        matching_routine: str = _create_tune_matching_routine(
            sequence_name, q1_target, q2_target, variables
        )
        logger.debug("Sending matching routine to cpymad")
        cpymad_instance.input(matching_routine)

    @staticmethod
    def perform_chroma_matching(
        cpymad_instance: Madx,
        sequence_name: str,
        dq1_target: float,
        dq2_target: float,
        variables: List[str] = ["ksf", "ksd"],
    ) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will run an additional
        matching command to reach the provided values for chromaticities.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            sequence_name (str): name of the sequence you want to activate for the tune matching.
            dq1_target (float): horizontal tune to match to.
            dq2_target (float): vertical tune to match to.
            variables (List[str]): the variables names to 'vary' in the MADX routine. Defaults to
                ["ksf", "ksd"] as it is a common name for sextupole strengths (foc / defoc).
        """
        matching_routine: str = _create_chromaticity_matching_routine(
            sequence_name, dq1_target, dq2_target, variables
        )
        logger.debug("Sending matching routine to cpymad")
        cpymad_instance.input(matching_routine)


class Parameters:
    """
    A class to compute different beam and machine parameters.
    """

    @staticmethod
    def beam_parameters(
        pc_gev: float, en_x_m: float, en_y_m: float, deltap_p: float, verbose: bool = False,
    ) -> Dict[str, float]:
        """Calculate beam parameters from provided values.

        Args:
            pc_gev (float): particle momentum.
            en_x_m (float): horizontal emittance, in meters.
            en_y_m (float): vertical emittance, in meters.
            deltap_p (float): momentum deviation.
            verbose (bool): bolean, whether to print out a summary of parameters or not.

        Returns:
            A dictionnary with the calculated values.
        """
        e0_gev = 0.9382720813
        e_tot_gev = np.sqrt(pc_gev ** 2 + e0_gev ** 2)
        gamma_r = e_tot_gev / e0_gev
        beta_r = pc_gev / np.sqrt(pc_gev ** 2 + e0_gev ** 2)

        parameters: Dict[str, float] = {
            "pc_GeV": pc_gev,  # Particle momentum [GeV]
            "B_rho_Tm": 3.3356 * pc_gev,  # Beam rigidity [T/m]
            "E_0_GeV": e0_gev,  # Rest mass energy [GeV]
            "E_tot_GeV": e_tot_gev,  # Total beam energy [GeV]
            "E_kin_GeV": e_tot_gev - e0_gev,  # Kinectic beam energy [GeV]
            "gamma_r": gamma_r,  # Relativistic gamma
            "beta_r": beta_r,  # Relativistic beta
            "en_x_m": en_x_m,  # Horizontal emittance [m]
            "en_y_m": en_y_m,  # Vertical emittance [m]
            "eg_x_m": en_x_m / gamma_r / beta_r,  # Horizontal geometrical emittance
            "eg_y_m": en_y_m / gamma_r / beta_r,  # Vertical geometrical emittance
            "deltap_p": deltap_p,  # Momentum deviation
        }

        if verbose:
            logger.trace("Outputing computed parameter values")
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


def _create_tune_matching_routine(
    sequence_name: str, q1_target: float, q2_target: float, variables: List[str] = ["kqf", "kqd"],
) -> str:
    """
    Create the string for a tune matching routine with provided parameters.

    Args:
        sequence_name (str): name of the sequence you want to activate for the tune matching.
        q1_target (float): horizontal tune to match to.
        q2_target (float): vertical tune to match to.
        variables (List[str]): the variables names to 'vary' in the MADX routine. Defaults to
            ["kqf", "kqd"] as it is a common name for quadrupole strengths (foc / defoc).

    Returns:
        The string to input in MADX to perform the matching.
    """
    logger.debug(
        f"Creating tune matching routine with for sequence '{sequence_name}' with target "
        f"tunes {q1_target} and {q2_target} "
    )
    matching_routine_string: str = f"""
!MATCHING SEQUENCE
match, sequence={sequence_name};"""

    for variable in variables:
        matching_routine_string += f"\n  vary, name={variable}, step=0.00001;"

    matching_routine_string += f"""
  global, sequence={sequence_name}, Q1={q1_target};
  global, sequence={sequence_name}, Q2={q2_target};
  Lmdif, calls=1000, tolerance=1.0e-21;
endmatch;
twiss;
"""
    return matching_routine_string


def _create_chromaticity_matching_routine(
    sequence_name: str, dq1_target: float, dq2_target: float, variables: List[str] = ["ksf", "ksd"],
) -> str:
    """
    Create the string for a chromaticity matching routine with provided parameters.

    Args:
        sequence_name (str): name of the sequence you want to activate for the tune matching.
        dq1_target (float): horizontal chromaticity to match to.
        dq2_target (float): vertical chromaticity to match to.
        variables (List[str]): the variables names to 'vary' in the MADX routine. Defaults to
            ["ksf", "ksd"] as it is a common name for sextupole strengths (foc / defoc).

    Returns:
        The string to input in MADX to perform the matching.
    """
    logger.debug(
        f"Creating chromaticity matching routine with for sequence '{sequence_name}' with target "
        f"chromaticities {dq1_target} and {dq2_target} "
    )
    matching_routine_string: str = f"""
!MATCHING SEQUENCE
match, sequence={sequence_name};"""

    for variable in variables:
        matching_routine_string += f"\n  vary, name={variable}, step=0.00001;"

    matching_routine_string += f"""
  global, sequence={sequence_name}, dq1={dq1_target};
  global, sequence={sequence_name}, dq2={dq2_target};
  Lmdif, calls=1000, tolerance=1.0e-21;
endmatch;
twiss;
"""
    return matching_routine_string
