"""
pyhdtoolkit Library
~~~~~~~~~~~~~~~~~~~
pyhdtoolkit is a utility library, written in Python, for my PhD needs.
Mainly particle accelerator physics studies and plotting.

:copyright: (c) 2019 by Felix Soubelet.
:license: MIT, see LICENSE for more details.
"""

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

from . import cpymadtools, plotting
from .__version__ import __author__, __author_email__, __description__, __license__, __title__, __url__, __version__

# Utils should not be part of the high-level import as pyhdtoolkit.a_util_function. I may change my mind on that.
# from . import utils


logging.getLogger(__name__).addHandler(NullHandler())

# Importing * is a bad practice and you should be punished for using it
__all__ = []
