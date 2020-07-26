"""
cpymadtools package
~~~~~~~~~~~~~~~~~~~
cpymadtools is a collection of utilities that integrate within my workflow with the `cpymad` library.

:copyright: (c) 2019 by Felix Soubelet.
:license: MIT, see LICENSE for more details.
"""
from loguru import logger

from .helpers import LatticeMatcher, Parameters
from .lattice_generators import LatticeGenerator
from .latwiss import LaTwiss
from .plotters import AperturePlotter, DynamicAperturePlotter, PhaseSpacePlotter, TuneDiagramPlotter

try:
    import cpymad
except ModuleNotFoundError:
    logger.warning("The cpymad tools are unavailable since the cpymad module is not importable")


# Importing * is a bad practice and you should be punished for using it
__all__ = []
