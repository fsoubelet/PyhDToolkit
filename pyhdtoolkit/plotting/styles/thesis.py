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


SMALL: Dict[str, PlotSetting] = {
    # ------ Lines ------ #
    "lines.linewidth": 1.3,  # Width of plot lines
    "lines.markersize": 3,  # Marker size, in points
    # ------ Patches ------ #
    "patch.linewidth": 1.3,  # Width of patches edge lines
    # ------ Fonts ------ #
    "font.size": 11,  # Default font size of elements
    # ----- Mathtext ----- #
    "mathtext.default": "regular",  # Default font for math
    # ------ Text ------ #
    "text.usetex": False,  # Don't use LaTeX for text handling
    # ------ Axes ------ #
    "axes.linewidth": 1,  # Linewidth of axes edges
    "axes.titlesize": 15,  # Fontsize of the axes title
    "axes.labelsize": 15,  # Fontsize of the x and y axis labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches ±1e3
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    # ------ Horizontal Ticks ------ #
    "xtick.major.size": 4,  # Size (length) of the major xtick locators
    "xtick.major.width": 1,  # Width of the major xtick locators
    "xtick.labelsize": 12,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    # ------ Vertical Ticks ------ #
    "ytick.major.size": 4,  # Size (length) of the major ytick locators
    "ytick.major.width": 1,  # Width of the major ytick locators
    "ytick.labelsize": 12,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    # ------- Legend ------ #
    "legend.loc": "best",  # Default legend location
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.framealpha": 0.85,  # Legend patch transparency factor
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 12,  # Legend text font size
    # ------ Figure ------ #
    "figure.figsize": (5, 3),  # Size of the figure
    "figure.titlesize": 15,  # Size of the figure title
    "figure.subplot.left": 0.15,  # Left side of the subplots of the figure
    "figure.subplot.bottom": 0.17,  # Bottom side of the subplots of the figure
    # ------ Saving ------ #
    "savefig.dpi": 300,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
}

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
