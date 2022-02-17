Welcome to PyhDToolkit's documentation!
=======================================

This package is an all-in-one collection of baseline utilities I use in my PhD work.
Most of the codes here have their use in my day-to-day work, but not necessarily in our team's softwares.

Highlights
----------

* Conveniently control MAD-X_ simulations through the cpymad_ package.
* Easily plot results of simulations (surveys, lattices, optics functions, phase space, etc).
* Enjoy data-validated pydantic_ models of results.
* Perform mathematical analysis of simulation data.
* Manage contexts, configurations and logging.
* Monitor HTCondor_ jobs.

Status
------

PyhDToolkit is a personnal project, and combined with my PhD I have very limited time to work on it.
However, feedback and bug reports are very welcome, please get in touch via the `GitHub issue tracker <https://github.com/zarr-developers/zarr-python/issues>`_.

Installation
------------

PyhDToolkit is available to install from ``PyPI`` or from VCS.

Install PyhDToolkit from PyPI::

    pip install pyhdtoolkit

To install the latest development version of PyhDToolkit, you can use pip with the
latest GitHub master::

    pip install git+https://github.com/fsoubelet/PyhDToolkit.git

The code base comes with a useful Makefile.
To work with PyhDToolkit source code in development, on needs Poetry_ and should install from ``GitHub``::

    git clone --recursive https://github.com/fsoubelet/PyhDToolkit.git
    cd pyhdtoolkit
    make install

To verify that any of your changes keeps the package stable, run the test suite::

    make tests


Contents
--------

.. toctree::
    :maxdepth: 2

    tutorial
    api
    release
    contributing

Citing
------

If you have a use of these codes, please consider citing them.
The repository has a `CERN <https://zenodo.org/badge/latestdoi/227081702/>`_ provided by Zenodo_, and all versions can be cited with the following BibTeX entry:

.. code-block:: bibtex

   @software{pyhdtoolkit,
     author       = {Felix Soubelet},
     title        = {fsoubelet/PyhDToolkit},
     publisher    = {Zenodo},
     doi          = {10.5281/zenodo.4268804},
     url          = {https://doi.org/10.5281/zenodo.4268804}
   }

Acknowledgments
---------------

The following people have contributed to the development of PyhDToolkit by contributing code,
documentation, code reviews, comments and/or ideas:

* :user:`Felix Soubelet <fsoubelet>`
* :user:`Joschua Dilly <joschd>`
* :user:`Axel Poyet <apoyet>`
* :user:`Michael Hofer <mihofer>`
* :user:`Tobias Persson <tpersson>`

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _MAD-X: https://mad.web.cern.ch/mad/
.. _cpymad: https://hibtc.github.io/cpymad/
.. _pydantic: https://pydantic-docs.helpmanual.io/
.. _HTCondor: https://htcondor.org/
.. _Poetry: https://python-poetry.org/
.. _Zenodo: https://zenodo.org