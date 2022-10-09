"""
.. _plotting-styles-thesis:

Thesis Styles
-------------

This module contains different styles to be used with `~matplotlib`.
The styles are tailored to be included in my thesis paper, and insert themselves seamlessly with the rest of the paper.
All plots are included as either a simple or double figure, with ``[width=0.9\linewidth]``.
The text body has a fontsize of 12 points, and the figures should integrate to have roughly the same text size.

The following are available:

- ``SMALL``:
- ``MEDIUM``:
- ``LARGE``:
"""
from typing import Dict, Union

PlotSetting = Union[float, bool, str, tuple]


SMALL: Dict[str, PlotSetting] = {}

# TODO: adapt from these sphinx params
MEDIUM: Dict[str, PlotSetting] = {
    "figure.autolayout": True,
    "figure.titlesize": 28,
    "axes.titlesize": 28,
    "legend.fontsize": 24,
    "axes.labelsize": 23,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
}

LARGE: Dict[str, PlotSetting] = {}
