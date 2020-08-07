"""
utils package
~~~~~~~~~~~~~~~~~~~
These are miscellaneous modules with functions that sometime tunr out useful to my workflow.
These are mainly wrappers around lower-level tools, or simply just additional niceties.

:copyright: (c) 2019 by Felix Soubelet.
:license: MIT, see LICENSE for more details.
"""

from .cmdline import CommandLine
from .executors import MultiProcessor, MultiThreader
from .printutil import END, Background, Foreground, Styles
