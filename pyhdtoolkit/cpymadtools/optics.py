"""
Module cpymadtools.optics
-------------------------

Created on 2020.02.19
:author: Felix Soubelet (felix.soubelet@cern.ch)

A module with functions to access `optics_functions` functionality directly onto `cpymad.madx.Madx` objects.
"""
from typing import Sequence

import optics_functions
import tfs

from cpymad.madx import Madx
from loguru import logger
