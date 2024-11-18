r"""
.. _plotting-styles-thesis:

Thesis Styles
-------------

This module contains different styles to be used with `~matplotlib`,
tailored for figures to be included in my thesis document. The end
results should insert themselves seamlessly with the rest of the paper.
All plots are included in a LaTeX figure environment, included with
``[width=0.99\columnwidth]`` (and potentially subfloats inside). The
text body has a fontsize of 12 points, and the figures should integrate
to have roughly the same text size.

The following are available:

- ``SMALL``: For small simple plots to be included in a multi-figure environment (e.g. a LaTeX figure with 2 subfloats). Two of these should render well when displayed side-by-side in the figure environment (``\subfloat[.9\linewidth]`` then ``\hspace{0.3cm}`` then ``\subfloat[.9\linewidth]``).
- ``MEDIUM``: For simple plots to be included alone in a LaTeX figure environment (e.g single axis line plots, or scatters with a colorbar like in `~pyhdtoolkit.plotting.tune`).
- ``LARGE``: For more complex plots to be included alone in a LaTeX figure environment (e.g. multi-axes figures such as in `~pyhdtoolkit.plotting.lattice`).
"""

PlotSetting = float | bool | str | tuple


SMALL: dict[str, PlotSetting] = {
    # ------ Lines ------ #
    "lines.linewidth": 1.3,  # Width of plot lines
    "lines.markersize": 3,  # Marker size, in points
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
    # ----- Grids ----- #
    "grid.linestyle": "--",  # Dashed grids (when explicitely asked for)
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

MEDIUM: dict[str, PlotSetting] = {
    # ------ Lines ------ #
    "lines.linewidth": 1.3,  # Width of plot lines
    "lines.markersize": 5,  # Marker size, in points
    # ------ Patches ------ #
    "patch.linewidth": 1.2,  # Width of patches edge lines
    # ------ Fonts ------ #
    "font.size": 12,  # Default font size of elements
    # ----- Mathtext ----- #
    "mathtext.default": "regular",  # Default font for math
    # ------ Text ------ #
    "text.usetex": False,  # Don't use LaTeX for text handling
    # ------ Axes ------ #
    "axes.linewidth": 1,  # Linewidth of axes edges
    "axes.titlesize": 16,  # Fontsize of the axes title
    "axes.labelsize": 16,  # Fontsize of the x and y axis labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches ±1e3
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    # ------ Horizontal Ticks ------ #
    "xtick.major.size": 4,  # Size (length) of the major xtick locators
    "xtick.major.width": 1,  # Width of the major xtick locators
    "xtick.labelsize": 13,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    # ------ Vertical Ticks ------ #
    "ytick.major.size": 4,  # Size (length) of the major ytick locators
    "ytick.major.width": 1,  # Width of the major ytick locators
    "ytick.labelsize": 13,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    # ----- Grids ----- #
    "grid.linestyle": "--",  # Dashed grids (when explicitely asked for)
    # ------- Legend ------ #
    "legend.loc": "best",  # Default legend location
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.framealpha": 0.85,  # Legend patch transparency factor
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 14,  # Legend text font size
    # ------ Figure ------ #
    "figure.figsize": (10, 6),  # Size of the figure
    "figure.titlesize": 16,  # Size of the figure title
    "figure.subplot.left": 0.13,  # Left side of the subplots of the figure
    "figure.subplot.bottom": 0.15,  # Bottom side of the subplots of the figure
    # ------ Saving ------ #
    "savefig.dpi": 400,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
}

LARGE: dict[str, PlotSetting] = {
    # ------ Lines ------ #
    "lines.linewidth": 1.7,  # Width of plot lines
    "lines.markersize": 8,
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
    "axes.titlesize": 23,  # Fontsize of the axes title
    "axes.labelsize": 23,  # Fontsize of the x and y axis labels
    "axes.formatter.limits": (-4, 5),  # Switch to scientific notations when order of magnitude reaches ±1e3
    "axes.formatter.use_mathtext": True,  # Format with i.e 10^{4} instead of 1e4
    "axes.formatter.useoffset": False,  # Do not use the annoying offset on top of yticks
    # ------ Horizontal Ticks ------ #
    "xtick.major.size": 6,  # Size (length) of the major xtick locators
    "xtick.major.width": 1.5,  # Width of the major xtick locators
    "xtick.labelsize": 18,  # Fontsize of the x axis tick labels
    "xtick.direction": "in",  # Show xticks towards inside of figure
    # ------ Vertical Ticks ------ #
    "ytick.major.size": 6,  # Size (length) of the major ytick locators
    "ytick.major.width": 1.5,  # Width of the major ytick locators
    "ytick.labelsize": 18,  # Fontsize of the y axis tick labels
    "ytick.direction": "in",  # Show yticks towards inside of figure
    # ----- Grids ----- #
    "grid.linestyle": "--",  # Dashed grids (when explicitely asked for)
    # ------- Legend ------ #
    "legend.loc": "best",  # Default legend location
    "legend.frameon": True,  # Make a dedicated patch for the legend
    "legend.framealpha": 0.85,  # Legend patch transparency factor
    "legend.fancybox": True,  # Use rounded box for legend background
    "legend.fontsize": 19,  # Legend text font size
    # ------ Figure ------ #
    "figure.figsize": (16, 10),  # Size of the figure
    "figure.titlesize": 23,  # Size of the figure title
    "figure.subplot.left": 0.13,  # Left side of the subplots of the figure
    "figure.subplot.bottom": 0.15,  # Bottom side of the subplots of the figure
    # ------ Saving ------ #
    "savefig.dpi": 500,  # Saved figure dots per inch
    "savefig.format": "pdf",  # Saved figure file format
}
