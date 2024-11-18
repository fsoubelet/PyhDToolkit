"""
.. _plotting-styles-paper:

Paper Styles
-------------

This module contains different styles to be used with `~matplotlib`,
tailored for figures to be included in my journal papers. The end
results should insert themselves seamlessly with the rest of the paper.
All plots are included as either a single or double column figure in these
papers.

The following are available:

- ``SINGLE_COLUMN``: For plots to be included in a single column figure environment.
- ``DOUBLE_COLUMN``: For plots to be included in a full width (double column) figure environment.
"""

PlotSetting = float | bool | str | tuple


SINGLE_COLUMN: dict[str, PlotSetting] = {
    # ------ Lines ------ #
    "lines.linewidth": 1.3,  # Width of plot lines
    "lines.markersize": 5,  # Marker size, in points
    # ------ Patches ------ #
    "patch.linewidth": 1.2,  # Width of patches edge lines
    # ------ Fonts ------ #
    "font.size": 16,  # Default font size of elements
    # ----- Mathtext ----- #
    "mathtext.default": "regular",  # Default font for math
    # ------ Text ------ #
    "text.usetex": False,  # Don't use LaTeX for text handling
    # ------ Axes ------ #
    "axes.linewidth": 1,  # Linewidth of axes edges
    "axes.titlesize": 20,  # Fontsize of the axes title
    "axes.labelsize": 20,  # Fontsize of the x and y axis labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches ±1e3
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    # ------ Horizontal Ticks ------ #
    "xtick.major.size": 4,  # Size (length) of the major xtick locators
    "xtick.major.width": 1,  # Width of the major xtick locators
    "xtick.labelsize": 18,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    # ------ Vertical Ticks ------ #
    "ytick.major.size": 4,  # Size (length) of the major ytick locators
    "ytick.major.width": 1,  # Width of the major ytick locators
    "ytick.labelsize": 18,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    # ----- Grids ----- #
    "grid.linestyle": "--",  # Dashed grids (when explicitely asked for)
    # ------- Legend ------ #
    "legend.loc": "best",  # Default legend location
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.framealpha": 0.85,  # Legend patch transparency factor
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 20,  # Legend text font size
    # ------ Figure ------ #
    "figure.figsize": (11, 7),  # Size of the figure
    "figure.titlesize": 20,  # Size of the figure title
    "figure.subplot.left": 0.13,  # Left side limit of the subplots of the figure
    "figure.subplot.top": 0.9,  # Top side limit of the subplots of the figure
    "figure.subplot.bottom": 0.1,  # Bottom side limit of the subplots of the figure
    # ------ Saving ------ #
    "savefig.dpi": 400,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
}

DOUBLE_COLUMN: dict[str, PlotSetting] = {
    # ------ Lines ------ #
    "lines.linewidth": 1.7,  # Width of plot lines
    "lines.markersize": 3,
    # ------ Patches ------ #
    "patch.linewidth": 1.2,  # Width of patches edge lines
    # ------ Fonts ------ #
    "font.size": 18,  # Default font size of elements
    # ----- Mathtext ----- #
    "mathtext.default": "regular",  # Default font for math
    # ------ Text ------ #
    "text.usetex": False,  # Don't use LaTeX for text handling
    # ------ Axes ------ #
    "axes.linewidth": 1.1,  # Linewidth of axes edges
    "axes.titlesize": 20,  # Fontsize of the axes title
    "axes.labelsize": 26,  # Fontsize of the x and y axis labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches ±1e3
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    # ------ Horizontal Ticks ------ #
    "xtick.major.size": 7,  # Size (length) of the major xtick locators
    "xtick.major.width": 1.6,  # Width of the major xtick locators
    "xtick.labelsize": 25,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    # ------ Vertical Ticks ------ #
    "ytick.major.size": 7,  # Size (length) of the major ytick locators
    "ytick.major.width": 1.6,  # Width of the major ytick locators
    "ytick.labelsize": 25,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    # ----- Grids ----- #
    "grid.linestyle": "--",  # Dashed grids (when explicitely asked for)
    # ------- Legend ------ #
    "legend.loc": "best",  # Default legend location
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.framealpha": 0.85,  # Legend patch transparency factor
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 21,  # Legend text font size
    # ------ Figure ------ #
    "figure.figsize": (18, 11),  # Size of the figure
    "figure.titlesize": 20,  # Size of the figure title
    "figure.subplot.left": 0.13,  # Left side of the subplots of the figure
    "figure.subplot.bottom": 0.15,  # Bottom side of the subplots of the figure
    # ------ Saving ------ #
    "savefig.dpi": 500,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
}
