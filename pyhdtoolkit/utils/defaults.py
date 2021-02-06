"""
Module utils.defaults
---------------------

Created on 2019.11.12
:author: Felix Soubelet (felix.soubelet@cern.ch)

Provides defaults to import for different settings.
"""
from pathlib import Path

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
