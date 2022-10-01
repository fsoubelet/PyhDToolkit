.. _examples-index:

.. _gallery:

=======
Gallery
=======

This page contains a gallery showcasing either plotting functionality provided in the `pyhdtoolkit.plotting`
submodules, or plots made from results of convenient functions available in `~pyhdtoolkit`.

.. important::
    The examples shown here are plotted with a customized but simple ``rcParams`` style. If one uses
    this package and sets their own preferences or uses their own **mplstyle**, the resulting plots
    might look significantly different.

    The package provides a plotting style in the `~pyhdtoolkit.utils.defaults` module, which should be 
    compatible with the plotters. One can use the style in two ways:

    .. tabbed:: Import and Set the Style

        Update the ``rcParams`` at runtime with:

            .. prompt:: python >>>

                from matplotlib import pyplot as plt
                from pyhdtoolkit.utils.defaults import PLOT_PARAMS

                plt.rcParams.update(PLOT_PARAMS)

    .. tabbed:: Install and Load the Style

        Do a one-time install of the style as an **.mplstyle** file to import in `~matplotlib`:

            .. prompt:: python >>>

                from matplotlib import pyplot as plt
                from pyhdtoolkit.utils import defaults

                defaults.install_mpl_style()  # only run this once
                plt.style.use("phd")  # created file is 'phd.mplstyle'

    In both cases, re-updating the ``rcParams`` later on will always overwrite these settings.

Click on any image thumbnail to see the corresponding gallery page with full images and access to the source code.
