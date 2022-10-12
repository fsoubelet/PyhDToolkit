"""
.. _plotting-styles-paper:

Paper Styles
-------------

This module contains different styles to be used with `~matplotlib`, tailored for figures to be included in my journal papers.
The end results should insert themselves seamlessly with the rest of the paper.
All plots are included as either a single or double column figure in these papers.

The following are available:

- ``SINGLE``:
- ``DOUBLE``:
"""
from typing import Dict, Union

PlotSetting = Union[float, bool, str, tuple]


SINGLE: Dict[str, PlotSetting] = {}

DOUBLE: Dict[str, PlotSetting] = {}
