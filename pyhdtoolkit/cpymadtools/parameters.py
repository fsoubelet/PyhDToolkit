"""
Module cpymadtools.parameters
-----------------------------

Created on 2020.02.03
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to compute different beam and machine parameters.
"""
from typing import Dict

import numpy as np

from loguru import logger

# ----- Utilities ----- #


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
