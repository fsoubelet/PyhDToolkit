Release Notes
=============

The full list of releases can be found in the Github repository's `releases page <https://github.com/fsoubelet/PyhDToolkit/releases>`.

.. _release_0.8.4:

0.8.4
-----

Enhancements
~~~~~~~~~~~~

* Added an *xoffset* variable to ``plot_latwiss``, allowing to center the plot on a specific element.

Maintenance
~~~~~~~~~~~

* The machine layout plotting in ``plot_latwiss`` has been exported to its own function. It is a private function.

See `v0.8.4 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.4>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.3...0.8.4>`_.


.. _release_0.8.3:

0.8.3
-----

Enhancements
~~~~~~~~~~~~

* Added a function in ``cpymadtools.twiss`` to export the entire twiss table to a *TfsDataFrame*.

See `v0.8.3 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.3>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.2...0.8.3>`_.


.. _release_0.8.2:

0.8.2
-----

Enhancements
~~~~~~~~~~~~

* Added a ``maths.utils`` module with convenience functions related to magnitude.
* Added an ``optics.ripken`` module with functions to calculate beam size according to Lebedev and Bogacz's formalism.
* Added a convenience logging setup function in ``utils.defaults``.
* ``plot_latwiss`` now adds a legend for different elements in the layout.
* ``plot_latwiss`` can now optionally plot BPM patches.
* ``plot_latwiss`` now accepts kwargs that will be transmitted to the layout plotting function.

Bug Fixes
~~~~~~~~~

* ``get_pattern_twiss`` now properly capitalizes variable names in the returned *TfsDataFrame*.
* ``plot_latwiss`` now only draws elements in the desired area when *xlimits* is provided, for a drastic speedup on big machines.

Maintenance
~~~~~~~~~~~

* The *PLOT_PARAMS* have been moved to ``utils.defaults``.
* The ``get_pattern_twiss`` default argument values now select the entire twiss table.
* ``plot_latwiss`` changed the parameter *plot_sextupoles* to *k2l_lim*, creating a dedicated axis for sextupole patches in the layout.
* The ``plotting.settings`` module has been removed.
* ``plot_latwiss`` doesn't force the pdf format when saving the figure anymore.

See `v0.8.2 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.2>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.1...0.8.2>`_.


.. _release_0.8.1:

0.8.1
-----

Bug Fixes
~~~~~~~~~

* Fixed inacurrate logging statements during tunes and chromaticities matching.

Maintenance
~~~~~~~~~~~

* Removed the unused **scripts** folder as well as the scripts' dependencies.

See `v0.8.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.1.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.0...0.8.1>`_.


.. _release_0.8.0:

0.8.0
-----

Enhancements
~~~~~~~~~~~~

* Added a ``twiss`` submodule to easily get specific patterns.
* Added a ``track`` submodule to handle particle tracking with ``MAD-X``'s ``TRACK`` command.
* Added utilities to get ``TWISS`` frame for specific IP or IR locations.
* Added utilities to ``MAKETHIN`` for (HL)LHC sequences.
* Added a utility to install an AC dipole in LHC beam 1.

Bug Fixes
~~~~~~~~~

* Closest tune approach determination now properly handles explicit targets.

Maintenance
~~~~~~~~~~~

* The ``cpymadtools`` now use *madx* as a parameter name instead of *cpymad_instance*.
* Relaxed dependencies.

See `v0.8.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.7.0...0.8.0>`_.


.. _release_0.7.0:

0.7.0
-----

Enhancements
~~~~~~~~~~~~

* Added an ``errors`` submodule to handle (HL)LHC magnetic errors setup.
* Added a ``matching`` submodule with routines for ``MAD-X`` matching and closest tune approach determination.
* Added an ``orbit`` submodule to handle (HL)LHC orbit variables setup.
* Added a ``ptc`` submodule with routines for ``MAD-X`` ``PTC`` operations.
* Added a ``special`` submodule with routines for personal use cases for (HL)LHC in ``MAD-X``.

Maintenance
~~~~~~~~~~~

* Cleanup of some modules.
* Improved test coverage.
* Tweaks to dev configurations.

See `v0.7.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.7.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.6.0...0.7.0>`_.


.. _release_0.6.0:

0.6.0
-----

Enhancements
~~~~~~~~~~~~

* Full compatibility across OSes (thanks to ``cpymad``'s progress).
* Added a ``tfstools`` module.
* Added a ``beam`` module in ``optics``.
* Added an (experimental) ``timedata`` module in ``plotting``.

Documentation
~~~~~~~~~~~~~

* Added a docs dependency.
* Started documentation site.

Maintenance
~~~~~~~~~~~

* Improved object validation with ``pydantic``.
* Made ``cpymad`` a default dependency.
* Updated dependencies.
* Moved CI to Github Actions, now covers all platforms.
* Improved test coverage.

See `v0.6.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.6.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.5.0...0.6.0>`_.


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