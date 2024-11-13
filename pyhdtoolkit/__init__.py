"""
pyhdtoolkit library
-------------------

pyhdtoolkit is a utility library, written in
Python, for my PhD needs. Mainly particle
accelerator physics studies and plotting.

:copyright: (c) 2019 by Felix Soubelet.
:license: MIT, see LICENSE for more details.
"""

from . import cpymadtools, maths, models, optics, plotting, utils, version  # noqa: F401, TID252

__title__ = "pyhdtoolkit"
__description__ = "An all-in-one toolkit package to easy my Python work in my PhD."
__url__ = "https://github.com/fsoubelet/PyhDToolkit"
__version__ = version.VERSION
__author__ = "Felix Soubelet"
__author_email__ = "felix.soubelet@cern.ch"
__license__ = "MIT"
