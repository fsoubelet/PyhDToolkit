"""
Module plotting.settings
------------------------

Created on 2019.12.08
:author: Felix Soubelet (felix.soubelet@cern.ch)

Some settings for better matplotlib.pyplot plots.
Work in progress.
"""
from typing import Dict, Union

# Set those with matplotlib.pyplot.rcParams.update(PLOT_PARAMS).
# Will ALWAYS be overwritten by later on definition
PLOT_PARAMS: Dict[str, Union[float, bool, str, tuple]] = {
    # ------ Axes ------ #
    "axes.linewidth": 0.8,  # Linewidth of axes edges
    "axes.grid": False,  # Do not display grid
    "axes.labelsize": 25,  # Fontsize of the x and y axis labels
    "axes.titlesize": 27,  # Fontsize of the axes title
    # ------ Date Forrmats ------ #
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
    "figure.figsize": (18, 11),  # Size of the figure
    "figure.max_open_warning": 10,  # Max number of figures to open before warning
    "figure.titlesize": 30,  # Size of the figure title
    # ------ Fonts ------ #
    "font.family": "sans-serif",  # Font family
    # "font.sans-serif": "Helvetica",  # Sans-Serif font to use
    "font.style": "normal",  # Style to apply to text font
    # ------- Legend ------ #
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 22,  # Legend text font size
    "legend.loc": "best",  # Default legend location
    # ------ Lines ------ #
    "lines.linewidth": 1,  # Line width, in points
    "lines.markersize": 5,  # Marker size, in points
    "lines.antialiased": True,  # Apply anti-aliasing to lines display
    # ------ Patches ------ #
    "patch.linewidth": 1,  # Width of patches edge lines
    "patch.antialiased": True,  # Apply anti-aliasing to patches display
    # ------ Paths ------ #
    "path.simplify": True,  # Reduce file size by removing "invisible" points
    # ------ Saving ------ #
    "savefig.dpi": 300,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
    "savefig.bbox": "tight",  # Careful: incompatible with pipe-based animation backends
    # ------ Text ------ #
    "text.antialiased": True,  # Apply anti-aliasing to text elements
    "text.color": "black",  # Default text color
    "text.usetex": False,  # Do not use LaTeX for text handling (I don't have a local installation)
    # ------ Ticks ------ #
    "xtick.labelsize": 20,  # Fontsize of the x axis tick labels
    "ytick.labelsize": 20,  # Fontsize of the y axis tick labels
}
