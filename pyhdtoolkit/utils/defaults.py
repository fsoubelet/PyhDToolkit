"""
Module utils.defaults
---------------------

Created on 2019.11.12
:author: Felix Soubelet (felix.soubelet@cern.ch)

Provides defaults to import for different settings.
"""
import sys

from pathlib import Path
from typing import Dict, NewType, Union

import matplotlib
import matplotlib.pyplot as plt

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
    # ------ Patches ------ #
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
    "text.latex.preamble": r"\usepackage{amsmath, amssymb}",  # \boldmath",  # Be careful with the preamble
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


def config_logger(level: str = "INFO", **kwargs) -> None:
    """
    Resets the logger object from loguru, with `sys.stdout` as a sink and the aforedefined format.
    This comes down to personnal preference.
    Any additional keyword argument used is transmitted to the `logger.add` call.
    """
    logger.remove()
    logger.add(sys.stdout, format=LOGURU_FORMAT, level=level.upper(), **kwargs)


def install_mpl_style() -> None:
    """
    Will create a `phd.mplstyle` file in the appropriate directories from the `PLOT_PARAMS` defined in this
    module. This enables one to use the style without importing `PLOT_PARAMS` and updating the rcParams,
    but instead simply using `plt.style.use("phd")`.
    Sometimes, matplotlib will not look for the file in its global config directory, but in the activated
    environment's site-packages data. The file is installed in both places.
    """
    logger.info("Installing matplotlib style")
    style_content: str = "\n".join(f"{option} : {setting}" for option, setting in PLOT_PARAMS.items())
    mpl_config_stylelib = Path(matplotlib.get_configdir()) / "stylelib"
    mpl_env_stylelib = Path(plt.style.core.BASE_LIBRARY_PATH)

    logger.debug("Ensuring matplotlib 'stylelib' directory exists")
    mpl_config_stylelib.mkdir(parents=True, exist_ok=True)
    mpl_env_stylelib.mkdir(parents=True, exist_ok=True)
    config_style_file = mpl_config_stylelib / "phd.mplstyle"
    env_style_file = mpl_env_stylelib / "phd.mplstyle"

    logger.debug(f"Creating style file at '{config_style_file.absolute()}'")
    config_style_file.write_text(style_content.replace("(", "").replace(")", ""))
    logger.debug(f"Creating style file at '{env_style_file.absolute()}'")
    env_style_file.write_text(style_content.replace("(", "").replace(")", ""))
    logger.success("You can now use it with 'plt.style.use(\"phd\")'")
