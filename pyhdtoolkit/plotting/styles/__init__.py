"""
.. _plotting-styles:

Plotting Styles
---------------

The **style** submodules provide styles to be used with `~matplotlib`, mostly tailored for my use, and for good results with the plotters in `~pyhdtoolkit.plotting`.
Feel free to use them anyway, as they might be useful to you.
This init file provides a ``BASELINE`` style with settings to be used everywhere.
"""
from typing import Dict, Union

from . import paper, thesis

PlotSetting = Union[float, bool, str, tuple]

# TODO: adapt and simplify from this
BASELINE: Dict[str, PlotSetting] = {  # ------ Patches ------ #
    "patch.linewidth": 1.5,  # Width of patches edge lines
    # ------ Fonts ------ #
    "font.family": "sans-serif",  # Font family
    "font.style": "normal",  # Style to apply to text font
    "font.weight": "bold",  # Bold font
    "font.size": 25,  # Default font size of elements
    "font.sans-serif": "Helvetica",  # Sans-Serif font to use
    # ----- Mathtext ----- #
    "mathtext.default": "regular",  # default font for math
    # ------ Text ------ #
    "text.usetex": True,  # Use LaTeX for text handling (Set to False if you don't have a local installation)
    "text.latex.preamble": r"\usepackage{amsmath, amssymb}",  # Be careful with the preamble
    # ------ Axes ------ #
    "axes.linewidth": 2,  # Linewidth of axes edges
    "axes.grid": True,  # Do display grid
    "axes.titlesize": 30,  # Fontsize of the axes title
    "axes.labelsize": 30,  # Fontsize of the x and y axis labels
    "axes.labelweight": "bold",  # Bold labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches 1e3
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    # ------ Date Formats ------ #
    "date.autoformatter.year": "%Y",  # AutoDateFormatter setting for years display
    "date.autoformatter.month": "%Y-%m",  # AutoDateFormatter setting for months display
    "date.autoformatter.day": "%Y-%m-%d",  # AutoDateFormatter setting for days display
    "date.autoformatter.hour": "%m-%d %H",  # AutoDateFormatter setting for seconds display
    "date.autoformatter.minute": "%d %H:%M",  # AutoDateFormatter setting for minutes display
    "date.autoformatter.second": "%H:%M:%S",  # AutoDateFormatter setting for seconds display
    "date.autoformatter.microsecond": "%M:%S.%f",  # AutoDateFormatter setting for microseconds
    # ------ Horizontal Ticks ------ #
    "xtick.major.size": 8,  # Size (length) of the major xtick locators
    "xtick.minor.size": 5,  # Size (length) of the minor xtick locators
    "xtick.major.width": 1.5,  # Width of the major xtick locators
    "xtick.minor.width": 0.6,  # Width of the minor xtick locators
    "xtick.labelsize": 25,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    "xtick.minor.visible": True,  # Show minor xtick locators
    # ------ Vertical Ticks ------ #
    "ytick.major.size": 8,  # Size (length) of the major ytick locators
    "ytick.minor.size": 5,  # Size (length) of the minor ytick locators
    "ytick.major.width": 1.5,  # Width of the major ytick locators
    "ytick.minor.width": 0.6,  # Width of the minor ytick locators
    "ytick.labelsize": 25,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    "ytick.minor.visible": True,  # Show minor ytick locators
    # ----- Grid ----- #
    "grid.linestyle": "--",  # Which linestyle for grid lines
    "grid.linewidth": 1.3,  # Width of the grid lines
    # ------- Legend ------ #
    "legend.loc": "best",  # Default legend location
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.framealpha": 0.9,  # Legend patch transparency factor
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 22,  # Legend text font size
    "legend.title_fontsize": 23,  # Legend title text font size
    # ------ Figure ------ #
    "figure.titlesize": 35,  # Size of the figure title
    "figure.figsize": (16, 10),  # Default size of the figures
    "figure.dpi": 300,  # Figure dots per inch
    "figure.subplot.left": 0.15,  # Left side of the subplots of the figure
    "figure.subplot.right": 0.90,  # Right side of the subplots of the figure
    "figure.subplot.bottom": 0.15,  # Bottom side of the subplots of the figure
    "figure.subplot.top": 0.90,  # Top side of the subplots of the figure
    "figure.autolayout": True,  # Adjust subplot params to fit the figure (tight_layout)
    # ------ Saving ------ #
    "savefig.dpi": 1000,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
    "savefig.bbox": "tight",  # Careful: incompatible with pipe-based animation backends
}

# This is meant for use to guarantee single-subplot figures all align on
# their axes and labels, for consistencyin my articles / thesis.
_FIGURE_CONSTRAINTS: Dict[str, PlotSetting] = {
    "figure.constrained_layout.use": False,
    "figure.subplot.left": 0.09,
    "figure.subplot.bottom": 0.1,
    "figure.subplot.right": 0.95,
    "figure.subplot.top": 0.85,
}
