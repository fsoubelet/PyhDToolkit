"""
pyhdtoolkit Library
~~~~~~~~~~~~~~~~~~~
pyhdtoolkit is a utility library, written in Python, for my PhD needs.
Mainly particle accelerator physics studies and plotting.

:copyright: (c) 2019 by Felix Soubelet.
:license: MIT, see LICENSE for more details.
"""

from .__version__ import __title__, __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__

from . import cpymadtools
from . import plotting
from . import utils

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())

# Importing * is a bad practice and you should be punished for using it
__all__ = []
