"""
Created on 2019.12.08
:author: Felix Soubelet (felix.soubelet@cern.ch)

Some settings for better matplotlib.pyplot plots.
Work in progress.
"""

import matplotlib.pyplot as plt

LARGE = 22
MEDIUM = 16
SMALL = 12
PLOT_PARAMS = {
    "axes.titlesize": LARGE,
    "legend.fontsize": MEDIUM,
    "figure.figsize": (16, 10),
    "axes.labelsize": MEDIUM,
    "xtick.labelsize": MEDIUM,
    "ytick.labelsize": MEDIUM,
    "figure.titlesize": LARGE,
}

plt.rcParams.update(PLOT_PARAMS)
