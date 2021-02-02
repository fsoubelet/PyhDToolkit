"""
Module cpymadtools.helpers
--------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for performing different common operations on a cpymad.madx.Madx object.
"""
from typing import Dict, Sequence, Tuple

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
    def get_tune_and_chroma_knobs(accelerator: str, beam: int = 1) -> Tuple[str, str, str, str]:
        """
        CREDITS GO TO JOSCHUA DILLY.
        Get names of knobs needed to match tunes and chromaticities as a tuple of strings.

        Args:
            accelerator (str): Accelerator either 'LHC' (dQ[xy], dQp[xy] knobs) or 'HLLHC'
                (kqt[fd], ks[fd] knobs).
            beam (int): Beam to use, for the knob names.

        Returns:
            Tuple of strings with knobs for `(qx, qy, dqx, dqy)`.
        """
        beam = 2 if beam == 4 else beam

        if accelerator.upper() not in ("LHC", "HLLHC"):
            logger.error("Invalid accelerator name, only 'LHC' and 'HLLHC' implemented")
            raise NotImplementedError(f"Accelerator '{accelerator}' not implemented.")

        return {
            "LHC": (f"dQx.b{beam}", f"dQy.b{beam}", f"dQpx.b{beam}", f"dQpy.b{beam}"),
            "HLLHC": (f"kqtf.b{beam}", f"kqtd.b{beam}", f"ksf.b{beam}", f"ksd.b{beam}"),
        }[accelerator.upper()]

    @staticmethod
    def perform_tune_and_chroma_matching(
        cpymad_instance: Madx,
        accelerator: str = None,
        sequence_name: str = None,
        q1_target: float = None,
        q2_target: float = None,
        dq1_target: float = None,
        dq2_target: float = None,
        varied_knobs: Sequence[str] = None,  # ["kqf", "kqd", "ksf", "ksd"],
        step: float = 1e-7,
        calls: int = 100,
        tolerance: float = 1e-21,
    ) -> None:
        """
        Provided with an active `cpymad` class after having ran a script, will run an additional
        matching command to reach the provided values for tunes and chromaticities.

        Tune matching is always performed. If chromaticity target values are given, then a matching is done
        for them, followed by an additionnal matching for both tunes and chromaticities.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            accelerator (str): name of the accelerator, used to determmine knobs if 'variables' not given.
                Automatic determination will only work for LHC and HLLHC.
            sequence_name (str): name of the sequence you want to activate for the tune matching.
            q1_target (float): horizontal tune to match to.
            q2_target (float): vertical tune to match to.
            dq1_target (float): horizontal chromaticity to match to.
            dq2_target (float): vertical chromaticity to match to.
            varied_knobs (Sequence[str]): the variables names to 'vary' in the MADX routine. An input
                could be ["kqf", "ksd", "kqf", "kqd"] as they are common names used for quadrupole and
                sextupole strengths (foc / defoc) in most examples.
            step (float): step size to use when varying knobs.
            calls (int): max number of varying calls to perform.
            tolerance (float): tolerance for successfull matching.
        """
        if accelerator and not varied_knobs:
            varied_knobs = LatticeMatcher.get_tune_and_chroma_knobs(
                accelerator=accelerator, beam=int(sequence_name[-1])
            )

        def match(*args, **kwargs):
            logger.debug("Executing matching commands")
            cpymad_instance.command.match(chrom=True)
            cpymad_instance.command.global_(sequence=sequence_name, **kwargs)
            for variable_name in args:
                cpymad_instance.command.vary(name=variable_name, step=step)
            cpymad_instance.command.lmdif(calls=calls, tolerance=tolerance)
            cpymad_instance.command.endmatch()

        logger.info(f"Matching tunes to Qx = {q1_target}, Qy = {q2_target} for sequence '{sequence_name}'")
        match(*varied_knobs[:2], q1=dq1_target, q2=dq2_target)  # first two in varied_knobs are tune knobs

        if (dq1_target is not None) and (dq2_target is not None):
            logger.info(
                f"Matching chromaticities to dqx = {dq1_target}, dqy = {dq2_target} for sequence "
                f"'{sequence_name}'"
            )
            match(*varied_knobs[2:], dq1=dq1_target, dq2=dq2_target)  # last two are chroma knobs
            logger.info(
                f"Doing additional combined matching to Qx = {q1_target}, Qy = {q2_target}, "
                f"dqx = {dq1_target}, dqy = {dq2_target} for sequence '{sequence_name}'"
            )
            match(*varied_knobs, q1=q1_target, q2=q2_target, dq1=dq1_target, dq2=dq2_target)

    @staticmethod
    def perform_closest_tune_approach(
        cpymad_instance: Madx,
        accel: str,
        sequence: str,
        qx: float,
        qy: float,
        dqx: float,
        dqy: float,
        step: float = 1e-7,
        calls: float = 100,
        tolerance: float = 1e-21,
    ):
        """ Tries to match the tunes to their mid-fractional tunes.
        The difference between this mid-tune and the actual matched tune is the
        closest tune approach. This distorts the optics.
        Better save and restore tunes before and after matching (see
        :fun:`get_tune_and_dispersion_knob_values` and :fun:`re.
        """
        mid_fraction = 0.5 * (fractional_tune(qx) + fractional_tune(qy))
        qxmid, qymid = int(qx) + mid_fraction, int(qy) + mid_fraction
        LOG.info("Performing closest tune approach:")
        LOG.info(f"  q1={qxmid}, q2={qymid}.")

        cpymad_instance.command.match(chrom=True)
        cpymad_instance.command.global_(sequence=sequence, q1=qxmid, q2=qymid, dq1=dqx, dq2=dqy)
        for name in get_tune_and_dispersion_knobs(accel, beam=int(sequence[-1])):
            cpymad_instance.command.vary(name=name, step=step)
        cpymad_instance.command.lmdif(calls=calls, tolerance=tolerance)
        cpymad_instance.command.endmatch()


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
