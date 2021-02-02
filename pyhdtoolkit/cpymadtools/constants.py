"""
Module cpymadtools.constants
----------------------------

Created on 2020.02.02
:author: Felix Soubelet (felix.soubelet@cern.ch)

Specific constants to be used in cpymadtools functions, to help with consistency.
"""
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
