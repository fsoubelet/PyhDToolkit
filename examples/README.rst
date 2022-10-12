.. _examples-index:

.. _gallery:

=======
Gallery
=======

This page contains a gallery showcasing either plotting functionality provided in the `pyhdtoolkit.plotting`
submodules, or plots made from results of convenient functions available in `~pyhdtoolkit`.

.. important::
    The examples shown here are plotted with a customized but simple ``rcParams`` style, simply for
    visibility in these galleries. If one uses this package and sets their own preferences or uses
    their own **mplstyle**, the resulting plots might look significantly different.

    The package provides several plotting styles in the `~pyhdtoolkit.plotting.styles` submodules,
    which are tailored for good rendering in my LaTeX documents and are made for good compatibility
    with the various plotters in `~pyhdtoolkit.plotting`. These styles are described in the 
    :ref:`styles <plotting-styles>` documentation section.

    One can use them in two ways, shown below with as example the ``MEDIUM`` style defined in
    `pyhdtoolkit.plotting.styles.thesis`.

    .. tabbed:: Import and Set the Style

        Update the ``rcParams`` at runtime with:

            .. prompt:: python >>>

                from matplotlib import pyplot as plt
                from pyhdtoolkit.plotting.styles.thesis import MEDIUM

                plt.rcParams.update(MEDIUM)
                # plotting code here

        Or, for a temporary update of the ``rcParams``:

            .. prompt:: python >>>

                from matplotlib import pyplot as plt
                from pyhdtoolkit.plotting.styles.thesis import MEDIUM

                with plt.rc_context(MEDIUM):
                    # Plotting code here

    .. tabbed:: Install the Styles and Load One

        Do a one-time install of the styles as **.mplstyle** files to use in `~matplotlib`:

            .. prompt:: python >>>

                from matplotlib import pyplot as plt
                from pyhdtoolkit.plotting.styles import install_mpl_styles

                install_mpl_styles()  # only run this once
                plt.style.use("thesis-medium")  # loaded from created file 'thesis-medium.mplstyle'

    In both cases, re-updating the ``rcParams`` later on will always overwrite these settings.

Click on any image thumbnail to see the corresponding gallery page with full images and access to the source code.
