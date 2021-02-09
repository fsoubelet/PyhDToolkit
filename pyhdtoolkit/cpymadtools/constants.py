"""
Module cpymadtools.constants
----------------------------

Created on 2020.02.02
:author: Felix Soubelet (felix.soubelet@cern.ch)

Specific constants to be used in cpymadtools functions, to help with consistency.
"""
DEFAULT_TWISS_COLUMNS = [
    "name",
    "s",
    "x",
    "y",
    "px",
    "py",
    "betx",
    "bety",
    "alfx",
    "alfy",
    "dx",
    "dy",
    "mux",
    "muy",
    "r11",
    "r12",
    "r21",
    "r22",
    "beta11",
    "beta12",
    "beta21",
    "beta22",
]

LHC_CROSSING_SCHEMES = {
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

# All values are defined as multiples of 0.3/Energy
CORRECTOR_LIMITS = {
    "HLLHC": dict(
        # MQSX1=mvars['kmax_MQSXF'],
        MQSX1=0.600 / 0.050,  # 0.6 T.m @ 50 mm in IR1&IR5
        MQSX2=1.360 / 0.017,  # 1.36 T @ 17 mm in IR2&IR8
        # MCSX1=mvars['kmax_MCSXF'],
        MCSX1=0.050 * 2 / (0.050 ** 2),  # 0.050 Tm @ 50 mm in IR1&IR5
        MCSX2=0.028 * 2 / (0.017 ** 2),  # 0.028 T @ 17 mm in IR2&IR8
        # MCSSX1=mvars['kmax_MCSSXF'],
        MCSSX1=0.050 * 2 / (0.050 ** 2),  # 0.050 Tm @ 50 mm in IR1&IR5
        MCSSX2=0.11 * 2 / (0.017 ** 2),  # 0.11 T @ 17 mm in IR2&IR8
        # MCOX1=mvars['kmax_MCOXF'],
        MCOX1=0.030 * 6 / (0.050 ** 3),  # 0.030 Tm @ 50 mm in IR1&IR5
        MCOX2=0.045 * 6 / (0.017 ** 3),  # 0.045 T @ 17 mm in IR2&IR8
        # MCOSX1=mvars['kmax_MCOSXF'],
        MCOSX1=0.030 * 6 / (0.050 ** 3),  # 0.030 Tm @ 50 mm in IR1&IR5
        MCOSX2=0.048 * 6 / (0.017 ** 3),  # 0.048 T @ 17 mm in IR2&IR8
        # MCDX1=mvars['kmax_MCDXF'],
        MCDX1=0.030 * 24 / (0.050 ** 4),  # 0.030 Tm @ 50 mm in IR1&IR5
        # MCDSX1=mvars['kmax_MCDSXF'],
        MCDSX1=0.030 * 24 / (0.050 ** 4),  # 0.030 Tm @ 50 mm in IR1&IR5
        # MCTX1=mvars['kmax_MCTXF'],
        MCTX1=0.07 * 120 / (0.050 ** 5),  # 0.070 Tm @ 50 mm in IR1&IR5
        MCTX2=0.01 * 120 / (0.017 ** 5),  # 0.010 Tm @ 17 mm in IR1&IR5
        # MCTSX1=mvars['kmax_MCTSXF'],
        MCTSX1=0.07 * 120 / (0.050 ** 5),  # 0.070 Tm @ 50 mm in IR1&IR5
        MQT=120,  # 120 T/m
        MQS=120,  # 120 T/m
        MS=1.280 * 2 / (0.017 ** 2),  # 1.28 T @ 17 mm
        MSS=1.280 * 2 / (0.017 ** 2),  # 1.28 T @ 17 mm
        MCS=0.471 * 2 / (0.017 ** 2),  # 0.471 T @ 17 mm
        MCO=0.040 * 6 / (0.017 ** 3),  # 0.04 T @ 17 mm
        MCD=0.100 * 24 / (0.017 ** 4),  # 0.1 T @ 17 mm
        MO=0.29 * 6 / (0.017 ** 3),  # 0.29 T @ 17 mm
    )
}

FD_FAMILIES = {"MO", "MS", "MQT"}  # Magnets that have F and D families
TWO_FAMILIES = {"MS"}  # Magnets that have 1 and 2 families
SPECIAL_FAMILIES = {"MQS"}  # Magnets in every second arc
