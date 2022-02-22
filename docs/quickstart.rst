.. _quickstart:

Quickstart
==========

.. _quickstart-install:

Installation
------------

This package is tested for and supports `Python 3.7+`.
You can install it simply from ``PyPI`` in a virtual environment with:

.. prompt:: bash

    pip install pyhdtoolkit

.. tip::
    Don't know what a virtual environment is or how to set it up?
    Here is a good primer on `virtual environments <https://realpython.com/python-virtual-environments-a-primer/>`_ by `RealPython`.

To setup a development environment, see the :doc:`contributing instructions <contributing>`.


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
    import pyhdtoolkit.utils

Cpymadtools
^^^^^^^^^^^

The core of ``PyhDToolkit`` is the `~pyhdtoolkit.cpymadtools` sub-package.
It provides an ensemble of functionality to perform operations with and from `~cpymad.madx.Madx` objects;
and conveniently setup, run, analyze and plot ``MAD-X`` simulations and their results.

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
* Perform useful routines with a clean pythonic interface (for instance :ref:`betatron coupling  <cpymadtools-coupling>` calculation and handling, :ref:`errors assignments <cpymadtools-errors>`);
* Conveniently create different useful plots after a simulation thanks to the :ref:`plotters classes <cpymadtools-plotters>`;
* Run :ref:`(HL)LHC <cpymadtools-lhc>` specific functionality, mostly tailored to my work. 

One can find many examples of the `~pyhdtoolkit.cpymadtools` apis' use in the :ref:`gallery <gallery>` section of this documentation.

Utilities
^^^^^^^^^

The :ref:`utils <pyhdtoolkit-utils>` module contains useful functions to setup logging or
plotting :ref:`defaults <utils-defaults>`, run external programs through the :ref:`command line <utils-cmdline>`, 
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
    A useful tidbit is this line which sets up the logging level for functions in the package:

    .. prompt:: python >>>

        from pyhdtoolkit.utils import defaults
        defaults.config_logger(level="trace")  # lowest level used, will give ALL logging

Additional Helpers
^^^^^^^^^^^^^^^^^^

Other sub-packages provide helper functionality mostly used internally in the package, but may be of use to you.
:ref:`Plotting <pyhdtoolkit-plotting>` gives access to helpers for `~matplotlib` plots; :ref:`models <pyhdtoolkit-models>`
provides `~pydantic`-validated classes for data handling throughout the package; :ref:`optics <pyhdtoolkit-optics>` to useful
beam optics parameters calculations; and :ref:`maths <pyhdtoolkit-maths>` to some statistical utilities.