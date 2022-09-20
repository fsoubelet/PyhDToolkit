import platform
import sys

import pytest

from pyhdtoolkit.version import VERSION, version_info


def test_version_info():
    info = version_info()
    assert isinstance(info, str)
    assert VERSION in info
    assert f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}" in info
    assert platform.platform() in info
