.. _examples-index:

.. _gallery:

=======
Gallery
=======

This page contains a gallery showcasing either plotting functionality provided in `~pyhdtoolkit.cpymadtools.plotters`, or plots made from results of convenient functions available in `~pyhdtoolkit`.

.. important::
    The examples shown here are plotted with the default ``rcParams`` of matplotlib. If one uses this 
    package and sets their own preferences or uses their own **mplstyle**, the resulting plots might 
    look significantly different.

    The package provides a plotting style in the `~pyhdtoolkit.utils.default` module, which should be 
    compatible with the plotters. One can use the style in two ways:

    .. panels::

        Update the ``rcParams`` at runtime with:

        .. code-block:: python

            from matplotlib import pyplot as plt
            from pyhdtoolkit.utils.defaults import PLOT_PARAMS

            plt.rcParams.update(PLOT_PARAMS)

        ---

        Do a one-time install of the style as an **.mplstyle** file to import in matplotlib:

        .. code-block:: python

            from matplotlib import pyplot as plt
            from pyhdtoolkit.utils import defaults

            defaults.install_mpl_style()  # only run once
            plt.style.use("phd")

Click on any image thumbnail to see the full image and source code.
