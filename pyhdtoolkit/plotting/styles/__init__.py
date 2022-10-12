"""
.. _plotting-styles:

Plotting Styles
---------------

The **style** submodules provide styles to be used with `~matplotlib`, mostly tailored for my use, and for good results with the plotters in `~pyhdtoolkit.plotting`.
Feel free to use them anyway, as they might be useful to you when using the `~pyhdtoolkit.plotting` submodules, or to be adapted.
"""
from typing import Dict, Union

from loguru import logger

from . import paper, thesis

PlotSetting = Union[float, bool, str, tuple]


def install_mpl_style() -> None:
    """
    .. versionadded:: 0.9.1

    Writes to disk a **phd.mplstyle** file in the appropriate directories, translating to matplotlib style
    format the ``PLOT_PARAMS`` defined in this module. This enables one to use the style without importing
    ``PLOT_PARAMS`` directly and updating the ``rcParams``, but instead setting the style to use, as so:

    .. code-block:: python

        from matplotlib import pyplot as plt
        plt.style.use("phd")

    .. note::
        Sometimes, matplotlib will not look for the file in its global config directory, but in the
        activated environment's site-packages data. The file is installed in both places.
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


# This is meant for use in the sphinx-gallery to help with readability
# as the default matplotlib settings are a bit small
_SPHINX_GALLERY_PARAMS: Dict[str, PlotSetting] = {
    "figure.autolayout": True,
    "figure.titlesize": 28,
    "axes.titlesize": 28,
    "legend.fontsize": 24,
    "axes.labelsize": 23,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
}
