import pathlib

import matplotlib
import matplotlib.pyplot as plt

from pyhdtoolkit.plotting.styles import install_mpl_styles


def test_mplstyles_install():
    install_mpl_styles()

    for expected_name in ("thesis-small", "thesis-medium", "thesis-large", "paper-single", "paper-double"):
        assert (pathlib.Path(matplotlib.get_configdir()) / "stylelib" / f"{expected_name}.mplstyle").is_file()
        assert (pathlib.Path(plt.style.core.BASE_LIBRARY_PATH) / f"{expected_name}.mplstyle").is_file()
