"""
.. _cpymadtools-constants:

Useful Constants
----------------

Specific constants to be used in `~.cpymadtools` functions,
to help with consistency.
"""

_MAX_SECTOR_VALUE: int = 8

# fmt: off
DEFAULT_TWISS_COLUMNS: list[str] = ["name", "s", "x", "y", "l", "px", "py", "betx", "bety", "alfx", "alfy",
                                    "dx", "dy", "mux", "muy", "r11", "r12", "r21", "r22", "beta11", "beta12",
                                    "beta21", "beta22"]
MONITOR_TWISS_COLUMNS: list[str] = ["name", "s", "betx", "bety", "alfx", "alfy", "mux", "muy", "dx", "dy",
                                    "dpx", "dpy", "x", "y", "ddx", "ddy", "k1l", "k1sl", "k2l", "k3l", "k4l",
                                    "wx", "wy", "phix", "phiy", "dmux", "dmuy", "keyword", "dbx", "dby",
                                    "r11", "r12", "r21", "r22"]
# fmt: on

# Needs to be formatted
LHC_IR_BPM_REGEX = r"BPM\S?\S?\.[0-{max_index}][LR][1258]\.*"

# MQX + maybe F (1/3 in HLLHC) + A (1/3) or B (2) + . + maybe A or B (2) + triplet number (1/2/3) + side (R/L) + IP number (1/2/5/8)
LHC_TRIPLETS_REGEX = "^MQXF?[AB].[AB]?[123][RL][1258]"

# This might not be accurate anymore
LHC_CROSSING_SCHEMES: dict[str, dict[str, float]] = {
    "flat": {},
    "lhc_inj": {
        "on_x1": -170,
        "on_sep1": -2,
        "on_x2": 170,
        "on_sep2": 3.5,
        "on_x5": 170,
        "on_sep5": 2,
        "on_x8": -170,
        "on_sep8": -3.5,
        "phi_IR1": 90,
        "phi_IR5": 0,
    },
    "lhc_top": {
        "on_x1": -160,
        "on_sep1": -0.55,
        "on_x2": 200,
        "on_sep2": 1.4,
        "on_x5": 160,
        "on_sep5": 0.55,
        "on_oh5": -1.8,
        "on_x8": -250,
        "on_sep8": -1,
        "phi_IR1": 90,
        "phi_IR5": 0,
    },
    "hllhc_inj": {
        "on_x1": 295,
        "on_sep1": -2,
        "on_x2": 170,
        "on_sep2": 3.5,
        "on_x5": 295,
        "on_sep5": 2,
        "on_x8": -170,
        "on_sep8": -3.5,
        # phis should be set by optics
    },
    "hllhc_top": {
        "on_x1": 250,
        "on_sep1": -0.75,  # 0.55
        "on_x2": 170,
        "on_sep2": 1,  # 1.4
        "on_x5": 250,
        "on_sep5": 0.75,  # 0.55 #'on_oh5': -1.8,
        "on_x8": -200,  # -250
        "on_sep8": -1,
        "on_crab1": -190,
        "on_crab5": -190,
        # phis should be set by optics
    },
}

# ----- LHC IP bump flags ----- #
LHC_CROSSING_ANGLE_FLAGS: list[str] = [f"on_x{ip}" for ip in [1, 2, 5, 8]] + [
    "on_x1h",
    "on_x5v",
    "on_s_x1h",
    "on_s_x5v",
]
LHC_PARALLEL_SEPARATION_FLAGS: list[str] = [f"on_sep{ip}" for ip in [1, 2, 5, 8]] + [
    "on_sep1v",
    "on_sep5h",
    "on_s_sep1v",
    "on_s_sep5h",
]
# Offset is in the plane of the crossing angle
LHC_IP_OFFSET_FLAGS: list[str] = (
    [f"on_o{ip}" for ip in [1, 2, 5, 8]]
    + ["on_o1h"]
    + [f"on_oh{ip}" for ip in [1, 5]]
    + [f"on_ov{ip}" for ip in [1, 2, 5]]
)
# Angle is in the same plane as the separation
LHC_ANGLE_FLAGS: list[str] = [f"on_a{ip}" for ip in [1, 2, 5, 8]] + ["on_a1v"]
# Magnetic fields or solenoids powering status
LHC_EXPERIMENT_STATE_FLAGS: list[str] = ["on_alice", "on_lhcb", "on_sol_atlas", "on_sol_cms", "on_sol_alice"]
LHC_IP2_SPECIAL_FLAG: list[str] = ["on_oe2"]  # TODO: ask Tobias or Stephane F.

# ----- LHC Triplet Correctors Knobs ----- #
LHC_KQSX_KNOBS: list[str] = [f"kqsx3.{side}{ip}" for side in ("r", "l") for ip in (1, 2, 5, 8)]  # skew quad
LHC_KCSX_KNOBS: list[str] = [f"kcsx3.{side}{ip}" for side in ("r", "l") for ip in (1, 2, 5, 8)]  # sextupole
LHC_KCSSX_KNOBS: list[str] = [f"kcssx3.{side}{ip}" for side in ("r", "l") for ip in (1, 2, 5, 8)]  # skew sext
LHC_KCOX_KNOBS: list[str] = [f"kcox3.{side}{ip}" for side in ("r", "l") for ip in (1, 2, 5, 8)]  # octupole
LHC_KCOSX_KNOBS: list[str] = [f"kcosx3.{side}{ip}" for side in ("r", "l") for ip in (1, 2, 5, 8)]  # skew oct
LHC_KCTX_KNOBS: list[str] = [f"kctx3.{side}{ip}" for side in ("r", "l") for ip in (1, 2, 5, 8)]  # decapole

# ----- LHC Arc Correctors Knobs ----- #
LHC_KQTF_KNOBS: list[str] = [  # tune trims, focusing and defocusing families, for each beam
    f"kqt{family}.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}.b{beam}"
    for beam in [1, 2]
    for family in ["f", "d"]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]
# fmt: off
# skew quadrupoles in arc short straight sections
LHC_KQS_KNOBS: list[str] = [f"kqs.r{ip}b1" for ip in [1, 3, 5, 7]] + \
    [f"kqs.l{ip}b1" for ip in [2, 4, 6, 8]] + \
    [f"kqs.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b1" for sector in [2, 4, 6, 8]] + \
    [f"kqs.r{ip}b2" for ip in [2, 4, 6, 8]] + \
    [f"kqs.l" f"{ip}b2" for ip in [3, 5, 7, 1]] + \
    [f"kqs.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b2" for sector in [1, 3, 5, 7]]
# fmt: on
LHC_KSF_KNOBS: list[str] = [  # sextupole correctors
    f"ks{family}{beam_id}.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b{beam}"
    for beam in [1, 2]
    for beam_id in [1, 2]
    for family in ["f", "d"]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]
LHC_KSS_KNOBS: list[str] = [  # skew sextupole correctors
    f"kss.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b{beam}"
    for beam in [1, 2]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]
LHC_KCS_KNOBS: list[str] = [  # spool piece (skew) sextupoles
    f"kcs.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b{beam}"
    for beam in [1, 2]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]
LHC_KCO_KNOBS: list[str] = [  # spool piece (skew) octupoles
    f"kco.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b{beam}"
    for beam in [1, 2]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]
LHC_KCD_KNOBS: list[str] = [  # spool piece (skew) decapoles
    f"kcd.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b{beam}"
    for beam in [1, 2]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]
LHC_KO_KNOBS: list[str] = [  # octupoles in arc short straight sections
    f"ko{family}.a{sector}{sector+1 if sector < _MAX_SECTOR_VALUE else 1}b{beam}"
    for beam in [1, 2]
    for family in ["f", "d"]
    for sector in [1, 2, 3, 4, 5, 6, 7, 8]
]

HLLHC_CORRECTOR_LIMITS: dict[str, float] = {  # All values are defined as multiples of 0.3/Energy
    "MQSX1": 0.600 / 0.050,  # 0.6 T.m @ 50 mm in IR1&IR5
    "MQSX2": 1.360 / 0.017,  # 1.36 T @ 17 mm in IR2&IR8
    # ------------- #
    "MCSX1": 0.050 * 2 / (0.050**2),  # 0.050 Tm @ 50 mm in IR1&IR5
    "MCSX2": 0.028 * 2 / (0.017**2),  # 0.028 T @ 17 mm in IR2&IR8
    # ------------- #
    "MCSSX1": 0.050 * 2 / (0.050**2),  # 0.050 Tm @ 50 mm in IR1&IR5
    "MCSSX2": 0.11 * 2 / (0.017**2),  # 0.11 T @ 17 mm in IR2&IR8
    # ------------- #
    "MCOX1": 0.030 * 6 / (0.050**3),  # 0.030 Tm @ 50 mm in IR1&IR5
    "MCOX2": 0.045 * 6 / (0.017**3),  # 0.045 T @ 17 mm in IR2&IR8
    # ------------- #
    "MCOSX1": 0.030 * 6 / (0.050**3),  # 0.030 Tm @ 50 mm in IR1&IR5
    "MCOSX2": 0.048 * 6 / (0.017**3),  # 0.048 T @ 17 mm in IR2&IR8
    # ------------- #
    "MCDX1": 0.030 * 24 / (0.050**4),  # 0.030 Tm @ 50 mm in IR1&IR5
    # ------------- #
    "MCDSX1": 0.030 * 24 / (0.050**4),  # 0.030 Tm @ 50 mm in IR1&IR5
    # ------------- #
    "MCTX1": 0.07 * 120 / (0.050**5),  # 0.070 Tm @ 50 mm in IR1&IR5
    "MCTX2": 0.01 * 120 / (0.017**5),  # 0.010 Tm @ 17 mm in IR1&IR5
    # ------------- #
    "MCTSX1": 0.07 * 120 / (0.050**5),  # 0.070 Tm @ 50 mm in IR1&IR5
    "MQT": 120,  # 120 T/m
    "MQS": 120,  # 120 T/m
    "MS": 1.280 * 2 / (0.017**2),  # 1.28 T @ 17 mm
    "MSS": 1.280 * 2 / (0.017**2),  # 1.28 T @ 17 mm
    "MCS": 0.471 * 2 / (0.017**2),  # 0.471 T @ 17 mm
    "MCO": 0.040 * 6 / (0.017**3),  # 0.04 T @ 17 mm
    "MCD": 0.100 * 24 / (0.017**4),  # 0.1 T @ 17 mm
    "MO": 0.29 * 6 / (0.017**3),  # 0.29 T @ 17 mm
}

FD_FAMILIES: set[str] = {"MO", "MS", "MQT"}  # Magnets that have F and D families
TWO_FAMILIES: set[str] = {"MS"}  # Magnets that have 1 and 2 families
SPECIAL_FAMILIES: set[str] = {"MQS"}  # Magnets in every second arc
