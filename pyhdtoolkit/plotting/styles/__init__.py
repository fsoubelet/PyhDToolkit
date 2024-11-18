"""
.. _plotting-styles:

Plotting Styles
---------------

The **style** submodules provide styles to be used with `~matplotlib`, mostly tailored for my use, and for good results with the plotters in `~pyhdtoolkit.plotting`.
Feel free to use them anyway, as they might be useful to you when using the `~pyhdtoolkit.plotting` submodules, or to be adapted.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from loguru import logger

from . import paper, thesis  # noqa: TID252

PlotSetting = float | bool | str | tuple


def install_mpl_styles() -> None:
    """
    .. versionadded:: 1.0.0

    Installs the styles defined in the `~pyhdtoolkit.plotting.styles` submodules to disk as **.mplstyle**
    files. This way, they can be used with `~matplotlib.pyplot.style.use` without having to import them
    and update the ``rcParams`` directly.
    """
    _install_style_file(thesis.SMALL, "thesis-small")
    _install_style_file(thesis.MEDIUM, "thesis-medium")
    _install_style_file(thesis.LARGE, "thesis-large")
    _install_style_file(paper.SINGLE_COLUMN, "paper-single")
    _install_style_file(paper.DOUBLE_COLUMN, "paper-double")


# ----- Helpers ----- #


# This is meant for use in the sphinx-gallery to help with readability
# as the default matplotlib settings are a bit small
_SPHINX_GALLERY_PARAMS: dict[str, PlotSetting] = {
    "figure.autolayout": True,
    "figure.titlesize": 28,
    "axes.titlesize": 28,
    "legend.fontsize": 24,
    "axes.labelsize": 23,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
}


def _install_style_file(style: dict[str, PlotSetting], stylename) -> None:
    """
    .. versionadded:: 1.0.0

    Writes to disk a **<name>.mplstyle** file in the appropriate directories, translating to matplotlib style
    format the provided style `dict`. This enables one to use the style without importing it directly and
    updating the ``rcParams``, but instead setting the style to use, as so:

    .. code-block:: python

        from matplotlib import pyplot as plt

        plt.style.use("style-name")

    .. note::
        Sometimes, matplotlib will not look for the file in its global config directory, but in the
        activated environment's site-packages data. The file is installed in both places.

    Args:
        style (dict[str, PlotSetting]): The style to be written to disk. One of the styles defined
            in the `~pyhdtoolkit.plotting.styles` submodules.
        stylename (str): The name to associate with the style. This is the name that will be used
            for the file written to disk, and will have to be `plt.use`d to use the style.
    """
    logger.info(f"Installing matplotlib style as '{stylename}'")
    style_content: str = "\n".join(f"{option} : {setting}" for option, setting in style.items())
    mpl_config_stylelib = Path(mpl.get_configdir()) / "stylelib"
    mpl_env_stylelib = Path(plt.style.core.BASE_LIBRARY_PATH)

    logger.debug("Ensuring matplotlib 'stylelib' directory exists")
    mpl_config_stylelib.mkdir(parents=True, exist_ok=True)
    mpl_env_stylelib.mkdir(parents=True, exist_ok=True)
    config_style_file = mpl_config_stylelib / f"{stylename.lower()}.mplstyle"
    env_style_file = mpl_env_stylelib / f"{stylename.lower()}.mplstyle"

    logger.debug(f"Creating style file at '{config_style_file.absolute()}'")
    config_style_file.write_text(style_content.replace("(", "").replace(")", ""))
    logger.debug(f"Creating style file at '{env_style_file.absolute()}'")
    env_style_file.write_text(style_content.replace("(", "").replace(")", ""))
    logger.success(f"You can now use it with 'plt.style.use(\"{stylename.lower()}\")'")
