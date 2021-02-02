"""
Module cpymadtools.helpers
--------------------------

Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for performing different common operations on a cpymad.madx.Madx object.
"""
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import tfs

from loguru import logger

from pyhdtoolkit.cpymadtools.constants import LHC_CROSSING_SCHEMES

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
        CREDITS GO TO JOSCHUA DILLY (@JoschD).
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
        sequence: str = None,
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
            sequence (str): name of the sequence you want to activate for the tune matching.
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
                accelerator=accelerator, beam=int(sequence[-1])
            )

        def match(*args, **kwargs):
            logger.debug("Executing matching commands")
            cpymad_instance.command.match(chrom=True)
            cpymad_instance.command.global_(sequence=sequence, **kwargs)
            for variable_name in args:
                cpymad_instance.command.vary(name=variable_name, step=step)
            cpymad_instance.command.lmdif(calls=calls, tolerance=tolerance)
            cpymad_instance.command.endmatch()
            logger.trace("Performing routine TWISS")
            cpymad_instance.twiss()  # prevents errors if the user forget to do so before querying tables

        logger.info(f"Matching tunes to Qx = {q1_target}, Qy = {q2_target} for sequence '{sequence}'")
        match(*varied_knobs[:2], q1=dq1_target, q2=dq2_target)  # first two in varied_knobs are tune knobs

        if (dq1_target is not None) and (dq2_target is not None):
            logger.info(
                f"Matching chromaticities to dqx = {dq1_target}, dqy = {dq2_target} for sequence "
                f"'{sequence}'"
            )
            match(*varied_knobs[2:], dq1=dq1_target, dq2=dq2_target)  # last two are chroma knobs
            logger.info(
                f"Doing additional combined matching to Qx = {q1_target}, Qy = {q2_target}, "
                f"dqx = {dq1_target}, dqy = {dq2_target} for sequence '{sequence}'"
            )
            match(*varied_knobs, q1=q1_target, q2=q2_target, dq1=dq1_target, dq2=dq2_target)

    @staticmethod
    def get_closest_tune_approach(
        cpymad_instance: Madx,
        accelerator: str = None,
        sequence: str = None,
        varied_knobs: Sequence[str] = None,  # ["kqf", "kqd", "ksf", "ksd"],
        step: float = 1e-7,
        calls: float = 100,
        tolerance: float = 1e-21,
    ) -> float:
        """
        Provided with an active `cpymad` class after having ran a script, tries to match the tunes to
        their mid-fractional tunes. The difference between this mid-tune and the actual matched tune is the
        closest tune approach.

        NOTA BENE: This assumes your lattice has previously been matched to desired tunes and
        chromaticities, as it will determine the appropriate targets from the Madx instance's internal tables.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            accelerator (str): name of the accelerator, used to determmine knobs if 'variables' not given.
                Automatic determination will only work for LHC and HLLHC.
            sequence (str): name of the sequence you want to activate for the tune matching.
            varied_knobs (Sequence[str]): the variables names to 'vary' in the MADX routine. An input
                could be ["kqf", "ksd", "kqf", "kqd"] as they are common names used for quadrupole and
                sextupole strengths (foc / defoc) in most examples.
            step (float): step size to use when varying knobs.
            calls (int): max number of varying calls to perform.
            tolerance (float): tolerance for successfull matching.

        Returns:
            The closest tune approach, in absolute value.
        """
        if accelerator and not varied_knobs:
            varied_knobs = LatticeMatcher.get_tune_and_chroma_knobs(
                accelerator=accelerator, beam=int(sequence[-1])
            )

        logger.info("Saving knob values to restore after closest tune approach")
        saved_knobs: Dict[str, float] = {knob: cpymad_instance.globals[knob] for knob in varied_knobs}

        logger.debug("Retrieving tunes and chromaticities from internal tables")
        q1, q2 = cpymad_instance.table.summ.q1[0], cpymad_instance.table.summ.q2[0]
        dq1, dq2 = cpymad_instance.table.summ.dq1[0], cpymad_instance.table.summ.dq2[0]

        logger.debug("Determining target tunes for closest approach")
        half_fractional_tune_split = (_fractional_tune(q1) + _fractional_tune(q2)) / 2
        qx_mid = int(q1) + half_fractional_tune_split
        qy_mid = int(q2) + half_fractional_tune_split

        logger.info("Performing closest tune approach routine, this matching should fail at deltaq = dqmin")
        LatticeMatcher.perform_tune_and_chroma_matching(
            cpymad_instance,
            accelerator,
            sequence,
            qx_mid,
            qy_mid,
            dq1,
            dq2,
            varied_knobs,
            step,
            calls,
            tolerance,
        )

        dqmin = abs(cpymad_instance.table.summ.q1[0] - cpymad_instance.table.summ.q2[0])

        logger.info("Restoring saved knobs")
        for knob, knob_value in saved_knobs.items():
            cpymad_instance.globals[knob] = knob_value
        cpymad_instance.twiss()

        return dqmin


class OrbitSetup:
    @staticmethod
    def lhc_orbit_variables() -> Tuple[List[str], Dict[str, str]]:
        """
        CREDITS GO TO JOSCHUA DILLY (@JoschD).
        Get the variable names used for orbit setup in the (HL)LHC.

        Returns:
            A tuple with a list of all orbit variables, and a dict of additional variables, that in the
            default configurations have the same value as another variable.
        """
        logger.trace("Returning (HL)LHC orbit variables")
        on_variables = (
            "crab1",
            "crab5",  # exists only in HL-LHC
            "x1",
            "sep1",
            "o1",
            "oh1",
            "ov1",
            "x2",
            "sep2",
            "o2",
            "oe2",
            "a2",
            "oh2",
            "ov2",
            "x5",
            "sep5",
            "o5",
            "oh5",
            "ov5",
            "phi_IR5",
            "x8",
            "sep8",
            "o8",
            "a8",
            "sep8h",
            "x8v",
            "oh8",
            "ov8",
            "alice",
            "sol_alice",
            "lhcb",
            "sol_atlas",
            "sol_cms",
        )
        variables = [f"on_{var}" for var in on_variables] + [f"phi_IR{ir:d}" for ir in (1, 2, 5, 8)]
        special = {
            "on_ssep1": "on_sep1",
            "on_xx1": "on_x1",
            "on_ssep5": "on_sep5",
            "on_xx5": "on_x5",
        }
        return variables, special

    @staticmethod
    def lhc_orbit_setup(cpymad_instance: Madx, scheme: str = "flat", **kwargs) -> Dict[str, float]:
        """
        CREDITS GO TO JOSCHUA DILLY (@JoschD).
        Automated orbit setup for (hl)lhc runs, for some default schemes.
        Assumed that at least sequence and optics files have been called.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            scheme (str): the default scheme to apply, as defined in `LHC_CROSSING_SCHEMES`. Accepted values
                are keys of `LHC_CROSSING_SCHEMES`. Defaults to 'flat' (every orbit variable to 0).

        Keyword Args:
            All standard crossing scheme variables (on_x1, phi_IR1, etc). Values given here override the
            values in the default scheme configurations.

        Returns:
            A dictionary of all orbit variables set, and their values as set in the MAD-X globals.
        """
        if scheme not in LHC_CROSSING_SCHEMES.keys():
            logger.error(f"Invalid scheme parameter, should be one of {LHC_CROSSING_SCHEMES.keys()}")
            raise ValueError("Invalid scheme parameter given")

        logger.debug("Getting orbit variables")
        variables, special = OrbitSetup.lhc_orbit_variables()

        scheme_dict = LHC_CROSSING_SCHEMES[scheme]
        final_scheme = {}

        for orbit_variable in variables:
            logger.trace(f"Setting orbit variable '{orbit_variable}'")
            # Sets value in MAD-X globals & returned dict, taken from scheme dict or kwargs if provided
            cpymad_instance.globals[orbit_variable] = final_scheme[var] = kwargs.get(
                orbit_variable, default=scheme_dict.get(var, 0)
            )

        for special_variable, copy_from in special.items():
            logger.trace(f"Setting special orbit variable '{special_variable}'")
            # Sets value in MAD-X globals & returned dict, taken from a given global or kwargs if provided
            cpymad_instance.globals[special_variable] = final_scheme[special_variable] = kwargs.get(
                special_variable, cpymad_instance.globals[copy_from]
            )

        return final_scheme

    @staticmethod
    def get_current_orbit_setup(cpymad_instance: Madx) -> Dict[str, float]:
        """
        CREDITS GO TO JOSCHUA DILLY (@JoschD).
        Get the current values for the orbit variales.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.

        Returns:
            A dictionary of all orbit variables set, and their values as set in the MAD-X globals.
        """
        logger.debug("Extracting orbit variables from global table")
        variables, specials = OrbitSetup.lhc_orbit_variables()
        return {
            orbit_variable: cpymad_instance.globals[orbit_variable]
            for orbit_variable in variables + list(specials.keys())
        }


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


class PTCUtils:
    @staticmethod
    def amplitude_detuning_ptc(
        cpymad_instance: Madx, order: int = 2, file: Union[Path, str] = None
    ) -> tfs.TfsDataFrame:
        """
        CREDITS GO TO JOSCHUA DILLY (@JoschD).
        Calculate amplitude detuning via PTC_NORMAL.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            order (int): maximum derivative order (only 0, 1 or 2 implemented in PTC). Defaults to `2`.
            file (Union[Path, str]): path to output file. Default `None`

        Returns:
            A TfsDataframe with results.
        """
        if order >= 3:
            logger.error(f"Maximum amplitude detuning order in PTC is 2, but {order:d} was requested")
            raise NotImplementedError("PTC amplitude detuning is not implemented for order > 2")

        logger.info("Entering PTC to calculate amplitude detuning")
        cpymad_instance.ptc_create_universe()

        # layout I got with mask (jdilly)
        # model=3 (Sixtrack code model: Delta-Matrix-Kick-Matrix)
        # method=4 (integration order), nst=3 (integration steps), exact=True (exact Hamiltonian)
        logger.trace("Creating PTC layout")
        cpymad_instance.ptc_create_layout(model=3, method=4, nst=3, exact=True)

        # alternative layout: model=3, method=6, nst=3
        # resplit=True (adaptive splitting of magnets), thin=0.0005 (splitting of quads),
        # xbend=0.0005 (splitting of dipoles)
        # madx.ptc_create_layout(model=3, method=6, nst=3, resplit=True, thin=0.0005, xbend=0.0005)

        logger.trace("Incorporating MAD-X alignment errors")
        cpymad_instance.ptc_align()  # use madx alignment errors
        # madx.ptc_setswitch(fringe=True)  # include fringe effects

        logger.trace("Selecting tune orders")
        cpymad_instance.select_ptc_normal(q1="0", q2="0")
        for ii in range(1, order + 1):  # These are d^iQ/ddp^i
            cpymad_instance.select_ptc_normal(dq1=f"{ii:d}", dq2=f"{ii:d}")

        # ANH = anharmonicities (ex, ey, deltap), works only with parameters as full strings
        # could be done nicer with permutations ...
        logger.trace("Selecting anharmonicities")
        if order >= 1:
            # madx.select_ptc_normal('anhx=0, 0, 1')  # dQx/ddp
            # madx.select_ptc_normal('anhy=0, 0, 1')  # dQy/ddp
            cpymad_instance.select_ptc_normal("anhx=1, 0, 0")  # dQx/dex
            cpymad_instance.select_ptc_normal("anhy=0, 1, 0")  # dQy/dey
            cpymad_instance.select_ptc_normal("anhx=0, 1, 0")  # dQx/dey
            cpymad_instance.select_ptc_normal("anhy=1, 0, 0")  # dQy/dex

        if order >= 2:
            # madx.select_ptc_normal('anhx=0, 0, 2')  # d^2Qx/ddp^2
            # madx.select_ptc_normal('anhy=0, 0, 2')  # d^2Qy/ddp^2
            cpymad_instance.select_ptc_normal("anhx=2, 0, 0")  # d^2Qx/dex^2
            cpymad_instance.select_ptc_normal("anhx=1, 1, 0")  # d^2Qx/dexdey
            cpymad_instance.select_ptc_normal("anhx=0, 2, 0")  # d^2Qx/dey^2
            cpymad_instance.select_ptc_normal("anhy=0, 2, 0")  # d^2Qy/dey^2
            cpymad_instance.select_ptc_normal("anhy=1, 1, 0")  # d^2Qy/dexdey
            cpymad_instance.select_ptc_normal("anhy=2, 0, 0")  # d^2Qy/dex^2

        # icase = phase-space dimensionality, no = order of map
        logger.debug("Executing PTC Normal")
        cpymad_instance.ptc_normal(closed_orbit=True, normal=True, icase=5, no=5)
        cpymad_instance.ptc_end()

        logger.debug("Extracting results to TfsDataFrame")
        dframe = tfs.TfsDataFrame(cpymad_instance.table.normal_results.dframe())
        dframe.columns = dframe.columns.str.upper()
        dframe.NAME = dframe.NAME.str.upper()
        dframe.index = range(len(dframe.NAME))  # table has a weird index

        if file:
            logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
            tfs.write(file, dframe)

        return dframe

    @staticmethod
    def rdts_ptc(cpymad_instance: Madx, order: int = 4, file: Union[Path, str] = None) -> tfs.TfsDataFrame:
        """
        CREDITS GO TO JOSCHUA DILLY (@JoschD).
        Calculate the RDTs via PTC_TWISS.

        Args:
            cpymad_instance (cpymad.madx.Madx): an instanciated cpymad Madx object.
            order (int): maximum derivative order (only 0, 1 or 2 implemented in PTC). Defaults to `2`.
            file (Union[Path, str]): path to output file. Default `None`

        Returns:
            TfsDataframe with results
        """
        logger.info("Entering PTC to calculate RDTs")
        cpymad_instance.ptc_create_universe()

        logger.trace("Creating PTC layout")
        cpymad_instance.ptc_create_layout(model=3, method=4, nst=3, exact=True)
        # madx.ptc_create_layout(model=3, method=6, nst=1)  # from Michi

        logger.trace("Incorporating MAD-X alignment errors")
        cpymad_instance.ptc_align()  # use madx alignment errors
        # madx.ptc_setswitch(fringe=True)  # include fringe effects

        logger.debug("Executing PTC Twiss")
        cpymad_instance.ptc_twiss(icase=6, no=order, normal=True, trackrdts=True)
        cpymad_instance.ptc_end()

        logger.debug("Extracting results to TfsDataFrame")
        dframe = tfs.TfsDataFrame(madx.table.twissrdt.dframe())
        dframe.columns = dframe.columns.str.upper()
        dframe.NAME = dframe.NAME.str.upper()

        if file:
            logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
            tfs.write(file, dframe)

        return dframe


# ----- Helpers ----- #


def _fractional_tune(tune: float) -> float:
    """
    Return only the fractional part of a tune value.

    Args:
        tune (float): tune value.

    Returns:
        The fractional part.
    """
    return tune - int(tune)  # ok since int truncates to lower integer
