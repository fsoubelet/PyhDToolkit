Release Notes
=============

The full list of releases can be found in the Github repository's `releases page <https://github.com/fsoubelet/PyhDToolkit/releases>`.

.. _release_0.5.0:

0.5.0
-----

Enhancements
~~~~~~~~~~~~

* Python 3.8 compatibility.
* Added an ``optics`` module.
* Added slots to classes.
* Almost fully covered in tests.

Bug Fixes
~~~~~~~~~

* Important fix of the lattice matchers in ``cpymadtools``.

Maintenance
~~~~~~~~~~~

* Fully type hinted the package.
* Improved logging.
* Replaced ``tqdm`` with ``rich``.
* Updated dependencies.
* Added some development tools and configurations.

See `v0.5.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.5.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.4.1...0.5.0>`_.


.. _release_0.4.1:

0.4.1
-----

Bug Fixes
~~~~~~~~~

* Quick fix of a type hinting issue causing imports to crash.

See `v0.4.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.4.1>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.4.0...0.4.1>`_.


.. _release_0.4.0:

0.4.0
-----

Enhancements
~~~~~~~~~~~~

* Optimization of the Docker image.
* Removal of the ``fsbox`` dependency.
* Use of ``loguru`` library for logging, and improved logging.
* Refactored commandline argument parsing for scripts.
* Improved type hinting.

Maintenance
~~~~~~~~~~~

* Renaming pyhdtoolkit.math to pyhdtoolkit.maths to avoid namespace clashes if trying to use the standard library's math module.
* Removing many functions from pyhdtoolkit.maths.nonconvex_phase_sync module as they were needed for notebooks but not this package.

See `v0.4.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.4.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.3.0...0.4.0>`_.


.. _release_0.3.0:

0.3.0
-----

Enhancements
~~~~~~~~~~~~

* The ``helpers`` module now has a ``Parameters`` class for beam and machine parameters calculations. Only one function yet.
* The ``plotters`` module now has an ``AperturePlotter`` class with a function to plot physical aperture.
* The ``latwiss`` module has received a major overhaul.

  - ``plot_latwiss`` has better defaults in values and plotting styles, as well as new args and kwargs options for customization.
  - ``plot_machine_survey`` also has better defaults, and offers the options to plot while differentiating magnetic elements.

See `v0.3.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.3.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.2.1...0.3.0>`_.


.. _release_0.2.1:

0.2.1
-----

Enhancements
~~~~~~~~~~~~

* New module for AC Dipole or Free Oscillations (with amplitude offset) tracking (in scripts).

Maintenance
~~~~~~~~~~~

* Some slight changes to **README**, **Makefile** and **Dockerfile**.

See `v0.2.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.2.1>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.2.0...0.2.1>`_.


.. _release_0.2.0:

0.2.0
-----

Enhancements
~~~~~~~~~~~~

* An **EVM** implementation for nonconvex phase synchronisation (in module ``omc_math``).
* Logging and contexts utilities from ``fsbox`` (props to ``pylhc/omc3`` for creating those).

See `v0.2.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.2.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.1.1...0.2.0>`_.