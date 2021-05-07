"""
Module utils.defaults
---------------------

Created on 2019.11.12
:author: Felix Soubelet (felix.soubelet@cern.ch)

Provides defaults to import for different settings.
"""
import sys

from pathlib import Path
from typing import Dict, Union, NewType

from loguru import logger

ANACONDA_INSTALL = Path().home() / "anaconda3"
OMC_PYTHON = ANACONDA_INSTALL / "envs" / "OMC" / "bin" / "python"

WORK_REPOSITORIES = Path.home() / "Repositories" / "Work"
BETABEAT_REPO = WORK_REPOSITORIES / "Beta-Beat.src"
OMC3_REPO = WORK_REPOSITORIES / "omc3"

TBT_CONVERTER_SCRIPT = OMC3_REPO / "omc3" / "tbt_converter.py"

LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

PlotSetting = NewType("PlotSetting", Union[float, bool, str, tuple])

# Set those with matplotlib.pyplot.rcParams.update(PLOT_PARAMS).
# Will ALWAYS be overwritten by later on definition
PLOT_PARAMS: Dict[str, PlotSetting] = {
    # ------ Axes ------ #
    "axes.linewidth": 2,  # Linewidth of axes edges
    "axes.grid": True,  # Do display grid
    "axes.labelsize": 30,  # Fontsize of the x and y axis labels
    "axes.titlesize": 30,  # Fontsize of the axes title
    "axes.labelweight": "bold",  # Bold labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches 1e3
    # "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.unicode_minus": True,  # Use true minus sign instead of hyphen
    # ------ Date Formats ------ #
    "date.autoformatter.year": "%Y",  # AutoDateFormatter setting for years display
    "date.autoformatter.month": "%Y-%m",  # AutoDateFormatter setting for months display
    "date.autoformatter.day": "%Y-%m-%d",  # AutoDateFormatter setting for days display
    "date.autoformatter.hour": "%m-%d %H",  # AutoDateFormatter setting for seconds display
    "date.autoformatter.minute": "%d %H:%M",  # AutoDateFormatter setting for minutes display
    "date.autoformatter.second": "%H:%M:%S",  # AutoDateFormatter setting for seconds display
    "date.autoformatter.microsecond": "%M:%S.%f",  # AutoDateFormatter setting for microseconds
    # ------ General Figure ------ #
    "figure.autolayout": True,  # Adjust subplot params to fit the figure (tight_layout)
    "figure.dpi": 300,  # Figure dots per inch
    "figure.figsize": (16, 10),  # Default size of the figures
    "figure.max_open_warning": 10,  # Max number of figures to open before warning
    "figure.titlesize": 35,  # Size of the figure title
    "figure.subplot.left": 0.15,  # Left side of the subplots of the figure
    "figure.subplot.right": 0.90,  # Right side of the subplots of the figure
    "figure.subplot.bottom": 0.15,  # Bottom side of the subplots of the figure
    "figure.subplot.top": 0.90,  # Top side of the subplots of the figure
    # ------ Fonts ------ #
    "font.size": 25,  # Default font size of elements
    "font.weight": "bold",  # Bold font
    "font.family": "sans-serif",  # Font family
    "font.sans-serif": "Helvetica",  # Sans-Serif font to use
    "font.style": "normal",  # Style to apply to text font
    # ----- Grid ----- #
    "grid.linestyle": "--",  # Which linestyle for grid lines
    "grid.linewidth": 1.3,  # Width of the grid lines
    # ------- Legend ------ #
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.title_fontsize": 23,  # Legend title text font size
    "legend.fontsize": 22,  # Legend text font size
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.loc": "best",  # Default legend location
    # ------ Lines ------ #
    "lines.linewidth": 1.5,  # Line width, in points
    "lines.markersize": 3,  # Marker size, in points
    "lines.antialiased": True,  # Apply anti-aliasing to lines display
    # ----- Mathtext ----- #
    "mathtext.default": "bf",  # default font for math
    # ------ Patches ------ #
    "patch.linewidth": 3,  # Width of patches edge lines
    "patch.antialiased": True,  # Apply anti-aliasing to patches display
    # ------ Paths ------ #
    "path.simplify": True,  # Reduce file size by removing "invisible" points
    # ------ Saving ------ #
    "savefig.dpi": 1000,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
    "savefig.bbox": "tight",  # Careful: incompatible with pipe-based animation backends
    # ------ Text ------ #
    "text.antialiased": True,  # Apply anti-aliasing to text elements
    "text.color": "black",  # Default text color
    "text.usetex": True,  # Use LaTeX for text handling (Set to False if you don't have a local installation)
    "text.latex.preamble": r"\usepackage{amsmath}",  # \boldmath",  # Be careful with the preamble
    # ------ Horizontal Ticks ------ #
    "xtick.labelsize": 25,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    "xtick.major.size": 8,  # Size (length) of the major xtick locators
    "xtick.major.width": 1.5,  # Width of the major xtick locators
    "xtick.minor.visible": True,  # Show minor xtick locators
    "xtick.minor.size": 5,  # Size (length) of the minor xtick locators
    "xtick.minor.width": 0.6,  # Width of the minor xtick locators
    # ------ Vertical Ticks ------ #
    "ytick.labelsize": 25,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    "ytick.major.size": 8,  # Size (length) of the major ytick locators
    "ytick.major.width": 1.5,  # Width of the major ytick locators
    "ytick.minor.visible": True,  # Show minor ytick locators
    "ytick.minor.size": 5,  # Size (length) of the minor ytick locators
    "ytick.minor.width": 0.6,  # Width of the minor ytick locators
}


def config_logger(level: str = "INFO", **kwargs) -> None:
    """
    Resets the logger object from loguru, with `sys.stdout` as a sink and the aforedefined format.
    This comes down to personnal preference.
    Any additional keyword argument used is transmitted to the `logger.add` call.
    """
    logger.remove()
    logger.add(sys.stdout, format=LOGURU_FORMAT, level=level.upper(), **kwargs)
