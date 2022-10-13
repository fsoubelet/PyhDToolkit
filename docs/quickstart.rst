.. _quickstart-top:

Quickstart
==========

.. _quickstart-install:

Installation
------------

This package is tested for and supports `Python 3.8+`.
You can install it simply from ``PyPI`` in a virtual environment with:

.. prompt:: bash

    python -m pip install pyhdtoolkit

.. tip::
    Don't know what a virtual environment is or how to set it up?
    Here is a good primer on `virtual environments <https://realpython.com/python-virtual-environments-a-primer/>`_ by `RealPython`.

To set up a development environment, see the :doc:`contributing instructions <contributing>`.


.. _quickstart-docker:

Using With Docker
-----------------

Docker provides an easy way to get access to a fully-fledged environment identical to the one I use for reproducibility.
One can directly pull a pre-built image from Dockerhub with:

.. prompt:: bash

    docker pull fsoubelet/simenv

You can then run a jupyter server from within the container and bind a local directory to work on.
Assuming the command above has beem ran and the image pulled from Dockerhub, one can run a jupyterlab server on port ``8888`` with the command: 

.. prompt:: bash

    docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work fsoubelet/simenv

Any jupyter notebook or Python files in the mounted directory can then be used or ran with an environment identical to mine.


.. quickstart-five-minutes:

5 Minutes to PyhDToolkit
------------------------

One can use the library by simply importing it:

.. prompt:: python >>>

    import pyhdtoolkit

This will include only the core components of ``PyhDToolkit``.
The different sub-packages must be imported separately, depending on your needs:

.. prompt:: python >>>

    import pyhdtoolkit.cpymadtools
    import pyhdtoolkit.maths
    import pyhdtoolkit.models
    import pyhdtoolkit.optics
    import pyhdtoolkit.plotting
    import pyhdtoolkit.utils

Cpymadtools
^^^^^^^^^^^

The core of ``PyhDToolkit`` is the :ref:`cpymadtools <pyhdtoolkit-cpymadtools>` sub-package.
It provides an ensemble of functionality to perform operations with and from `~cpymad.madx.Madx` objects;
and conveniently setup, run and analyze ``MAD-X`` simulations and their results.

All the public apis in the `~pyhdtoolkit.cpymadtools` work in the same fashion: call them with as first argument your
`~cpymad.madx.Madx` instance, and then any `args` and `kwargs` relevant to the functionality at hand.
Let's say one has initiated their ``MAD-X`` simulation through `~cpymad.madx.Madx` as follows:

.. prompt:: python >>>

    from cpymad.madx import Madx
    madx = Madx()

Then using the `~pyhdtoolkit.cpymadtools` apis goes as:

.. prompt:: python >>>

    from pyhdtoolkit.cpymadtools import super_cool_function  # pretend it exists ;)
    super_cool_function(madx, *args, **kwargs)

In the `~pyhdtoolkit.cpymadtools` one will find modules to:

* Encompass existing ``MAD-X`` commands, such as for example :ref:`matching <cpymadtools-matching>` or :ref:`tracking <cpymadtools-track>`;
* Perform useful routines with a clean pythonic interface (for instance :ref:`betatron coupling  <cpymadtools-coupling>` calculation and handling, :ref:`errors assignments <cpymadtools-errors>` or :ref:`table querying <cpymadtools-utils>`);
* Run :ref:`(HL)LHC <cpymadtools-lhc>` specific functionality, mostly tailored to my work. 

One can find many examples of the `~pyhdtoolkit.cpymadtools` apis' use in the :ref:`gallery <gallery>` section of this documentation.

Plotting
^^^^^^^^

The :ref:`plotting <pyhdtoolkit-plotting>` sub-package provides a set of functions to create plots supporting or showcasing  the results of ``MAD-X`` simulations.
It also provides convenience plotting utilities and a set of `matplotlib` styles that work well in conjunction with the various plotting APIs.

Some public apis in `~pyhdtoolkit.plotting` can be used as standalone while others work in the same way as the `~pyhdtoolkit.cpymadtools` apis, by being called with a `~cpymad.madx.Madx` instance as first arguments and then any `args` and `kwargs` relevant to plotting.
In the second case, relevant data for the plotting is directly queried and computed by interacting with the `~cpymad.madx.Madx` instance.

Using the `~pyhdtoolkit.plotting` apis goes as:

.. tabbed:: Standalone

    .. prompt:: python >>>

        from pyhdtoolkit.plotting.tune import plot_tune_diagram  # for instance
        plot_tune_diagram(max_order=6, differentiate_orders=True)  # and enjoy the result!

.. tabbed:: Interacting with MAD-X

    Let's say one has initiated their ``MAD-X`` simulation through `~cpymad.madx.Madx` as follows:

    .. prompt:: python >>>

        from cpymad.madx import Madx
        madx = Madx()
        # do some simulation with this instance

    Then using the api goes as:

    .. prompt:: python >>>

        from pyhdtoolkit.plotting.aperture import plot_aperture  # for instance
        plot_aperture(madx, *args, **kwargs)  # and enjoy the result!


One can find many examples of the `~pyhdtoolkit.plotting` apis' use in the :ref:`gallery <gallery>` section of this documentation.

Utilities
^^^^^^^^^

The :ref:`utils <pyhdtoolkit-utils>` module contains useful functions to set up :ref:`logging <utils-logging>`, run external programs through the :ref:`command line <utils-cmdline>`, 
run your functions through :ref:`useful contexts <utils-contexts>`, easily wrap and :ref:`parallelise <utils-executors>`
functions, or perform many convenient :ref:`operations <utils-operations>` on miscellaneous Python objects.

For instance, one can safely run an input at the commandline with:

.. prompt:: python >>>

    from pyhdtoolkit.utils.cmdline import CommandLine
    CommandLine.run("sleep 5")

Alternatively one can easily parallelise an I/O-intensive function through multithreading with:

.. prompt:: python >>>

    from pyhdtoolkit.utils.executors import MultiThreader
    Threader = MultiThreader()
    results = Threader.execute_function(
        func=your_io_heavy_function,
        func_args=list_of_args_for_each_call,
        n_processes=some_int_up_to_you,
    )

.. tip::
    A useful tidbit is the following which sets up the logging level for functions in the package:

    .. prompt:: python >>>

        from pyhdtoolkit.utils import logging
        logging.config_logger(level="trace")  # the lowest level used, will give ALL logging

Additional Helpers
^^^^^^^^^^^^^^^^^^

Other sub-packages provide helper functionality mostly used internally in the package, but may be of use to you.
:ref:`Plotting <pyhdtoolkit-plotting>` gives access to many plotting functions; :ref:`models <pyhdtoolkit-models>`
provides `~pydantic`-validated classes for data handling throughout the package; :ref:`optics <pyhdtoolkit-optics>` to useful
beam optics parameters calculations; and :ref:`maths <pyhdtoolkit-maths>` to some statistical utilities.