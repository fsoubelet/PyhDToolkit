Release Notes
=============

The full list of releases can be found in the Github repository's `releases page <https://github.com/fsoubelet/PyhDToolkit/releases>`_.


.. _release_0.20.1:

0.20.1
------

Enhancements
~~~~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.lhc.correct_lhc_global_coupling` function now supports a `call` and a `tolerance` arguments to be given to the `LMDIF` call in `MAD-X`.

See `v0.20.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.20.1>`_ and the `full changes since v0.20.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.20.0...0.20.1>`_.


.. _release_0.20.0:

0.20.0
------

Enhancements
~~~~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.coupling.get_closest_tune_approach` function now supports the `run3` boolean argument introduced in version `0.19.1`, which is used for the ``LHC`` case.
* The `~pyhdtoolkit.cpymadtools.coupling` module now has a new function, `~pyhdtoolkit.cpymadtools.coupling.get_coupling_rdts`, which will return the coupling Resonance Driving Terms throughout all elements in the sequence as columns added to the `tfs.TfsDataFrame` returned after a ``TWISS`` call.
* The `~pyhdtoolkit.cpymadtools.coupling` module now has a new function, `~pyhdtoolkit.cpymadtools.coupling.get_cminus_from_coupling_rdts`, which first calls the new `~pyhdtoolkit.cpymadtools.coupling.get_coupling_rdts` and then wraps the `optics_functions.coupling.closest_tune_approach` to provide an estimate of the :math:`C^{-}` according to the desired calculation method.
* The `~pyhdtoolkit.cpymadtools.lhc` module now has a new function, `~pyhdtoolkit.cpymadtools.lhc.carry_colinearity_knob_over`, which will carry over the powering of ``MQSX`` magnets around an IP to a single side.
* The `~pyhdtoolkit.cpymadtools.lhc` module now has a new function, `~pyhdtoolkit.cpymadtools.lhc.correct_lhc_global_coupling`, which will runs a tricky routine to minimize the global :math:`|C^{-}|` through the ``dqmin`` variable.
* The `~pyhdtoolkit.cpymadtools.lhc` module now has a new function, `~pyhdtoolkit.cpymadtools.lhc.do_kmodulation` which simulates a `K-Modulation` of an inner triplet quadrupole ``Q1`` in a desired IR, and returns a `tfs.TfsDataFrame` of the results.

Documentation
~~~~~~~~~~~~~

* Various docstrings have been corrected on wrong details, and some examples have been added.

Maintenance
~~~~~~~~~~~

* Various private helpers have been added through different modules.
* The minimum required version of `tfs-pandas` has been raised to ``3.2.0``.
* Increased test coverage.

See `v0.20.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.20.0>`_ and the `full changes since v0.19.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.19.1...0.20.0>`_.


.. _release_0.19.1:

0.19.1
------

Maintenance
~~~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.lhc.get_lhc_tune_and_chroma_knobs` function now has a new boolean argument, `run3`, to determine if the standard `_op` knobs should be returned.
* The functions in the `~pyhdtoolkit.cpymadtools.matching` module now also have the `run3` argument, and will call the Run 3 `_op` knobs if this argument is set to `True` and the `LHC` accelerator is passed.
* Fixes have been provided to the various Github Actions workflow of the repository.

See `v0.19.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.19.1>`_ and the `full changes since v0.19.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.19.0...0.19.1>`_.


.. _release_0.19.0:

0.19.0
------

Enhancements
~~~~~~~~~~~~

* The `pyhdtoolkit.plotting` package has a new sub-package, `pyhdtoolkit.plotting.sbs` with modules to plot coupling (`~pyhdtoolkit.plotting.sbs.coupling`) and phase (`~pyhdtoolkit.plotting.sbs.phase`) segment-by-segment results.
* The `pyhdtoolkit.plotting.sbs` package has a new utility module, `~pyhdtoolkit.plotting.sbs.utils`, with helpful functions for plotting.
* The `pyhdtoolkit.cpymadtools.lhc` module has a new function, `~pyhdtoolkit.cpymadtools.lhc.get_lhc_bpms_twiss_and_rdts` to easily get coupling RDTs at all observation points (BPMs) in the LHC sequence.

Documentation
~~~~~~~~~~~~~

* A new gallery was added showcasing the plotting of segment-by-segment coupling and phase results.

Maintenance
~~~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.plotters.LatticePlotter.plot_latwiss` function now plots the quadrupole gradient of a dipole with the same shade as a normal quadrupole.
* A new dependency, the `optics_functions` package, was added.
* The documentation for the `~pyhdtoolkit.maths.plotting` module has been extended.
* Tests were added for the new functionality.
* Input files for various tests have been regrouped in relevant directories for clarity.

See `v0.19.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.19.0>`_ and the `full changes since v0.18.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.18.0...0.19.0>`_.


.. _release_0.18.0:

0.18.0
------

Enhancements
~~~~~~~~~~~~

* The `pyhdtoolkit.utils._misc` module has a new function,  `~pyhdtoolkit.utils._misc.add_markers_around_lhc_ip` to add `MAD-X` markers around a given IP in order to increase the resolution of the TWISS calls in the IP vicinity.
* The `pyhdtoolkit.utils._misc` module has a new function,  `~pyhdtoolkit.utils._misc.get_lhc_ips_positions`, to determine the longitudinal position (S variable) of LHC IPs from a dataframe.
* The `pyhdtoolkit.utils._misc` module has a new function,  `~pyhdtoolkit.utils._misc.draw_ip_locations`, to add labels with the location of LHC IPs to a given `~matplotlib.axes.Axes` object.
* The `LHC Rigid Waist Shift` gallery has been improved, and now shows a visualization of the waist shift and two ways to calculate its value.

Bug Fixes
~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.orbit.lhc_orbit_variables` function does not return a wrong `on_phi_IR5` variable anymore.

Maintenance
~~~~~~~~~~~

* The dependency on `matplotlib` has been pinned to `<3.5` to avoid issues with the documentation plot style, to be fixed later on. 
* The bibliography file for the package's documentation has been cleaned up.
* The Github icon in the documentation pages now redirects to the proper pages.
* The documentation for the `~pyhdtoolkit.maths.nonconvex_phase_sync` has been improved.
* Some additional files necessary for the documentation additions are now included in the repo, but not the package.

See `v0.18.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.18.0>`_ and the `full changes since v0.17.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.17.0...0.18.0>`_.


.. _release_0.17.0:

0.17.0
------

Enhancements
~~~~~~~~~~~~

* The `pyhdtoolkit.cpymadtools.matching` module has two new wrapper functions, `~pyhdtoolkit.cpymadtools.matching.match_tunes` and `~pyhdtoolkit.cpymadtools.matching.match_chromaticities`, to perform matching on either tunes or chromaticities only.
* The `pyhdtoolkit.cpymadtools.lhc` module has a new utility function, `~pyhdtoolkit.cpymadtools.lhc.get_magnets_powering`, to get the percentage of magnets' max powering used in a given configuration.
* The `pyhdtoolkit.cpymadtools.utils` module has a new function, `~pyhdtoolkit.cpymadtools.utils.export_madx_table`, to conveniently export an internal table to disk with proper regex filtering in a way that can be read by ``MAD-X`` later on. 
* The `pyhdtoolkit.cpymadtools.constants` module now includes a regex for the `(HL)LHC` triplets. Beware that ``MAD-X`` itself does not understand all regex features.

Bug Fixes
~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.twiss.get_pattern_twiss` function now properly handles being given specific *columns*.

Maintenance
~~~~~~~~~~~

* The deprecated `pyhdtoolkit.cpymadtools.lhc.match_no_coupling_through_ripkens` function has been removed, its replacement in the `pyhdtoolkit.cpymadtools.coupling` module should be used.
* The deprecated `pyhdtoolkit.cpymadtools.lhc._get_k_strings` function has been removed, its replacement in the `pyhdtoolkit.cpymadtools.utils` module should be used.
* The deprecated `pyhdtoolkit.cpymadtools.matching.get_closest_tune_approach` function has been removed, its replacement in the `pyhdtoolkit.cpymadtools.coupling` module should be used.
* The deprecated `pyhdtoolkit.cpymadtools.matching.get_lhc_tune_and_chroma_knobs` function has been removed, its replacement in the `pyhdtoolkit.cpymadtools.lhc` module should be used.
* The `pyhdtoolkit.cpymadtools.lhc._get_k_strings` helper function is now deprecated and has been moved to `pyhdtoolkit.cpymadtools.utils._get_k_strings`.
* The internal imports in the package have been reworked, and sub-packages now only expose their modules through ``__all__`` opposed to some of the modules' contents previously.
* Some tests have been added.

See `v0.17.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.17.0>`_ and the `full changes since v0.16.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.16.1...0.17.0>`_.


.. _release_0.16.1:

0.16.1
------

Maintenance
~~~~~~~~~~~

* The **info** level logging statements in the `pyhdtoolkit.cpymadtools` modules have been adjusted to **debug** level. Info logging is left to the user.
* The **warning** level logging statements in the `pyhdtoolkit.cpymadtools` modules have been modified to give a bit more information.

See `v0.16.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.16.1>`_ and the `full changes since v0.16.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.16.0...0.16.1>`_.


.. _release_0.16.0:

0.16.0
------

Enhancements
~~~~~~~~~~~~

* A new module, `pyhdtoolkit.cpymadtools.coupling` has been added, and now hosts functions to get the closest tune approach (`~pyhdtoolkit.cpymadtools.coupling.get_closest_tune_approach`) and match coupling through ``Ripken`` parameters (`~pyhdtoolkit.cpymadtools.coupling.match_no_coupling_through_ripkens`).
* The `pyhdtoolkit.cpymadtools.lhc` module has a new function, `~pyhdtoolkit.cpymadtools.lhc.get_lhc_bpms_list`, which returns the list of monitoring BPMs for the current LHC sequence in use.
* The `pyhdtoolkit.cpymadtools.lhc` module now hosts the `~pyhdtoolkit.cpymadtools.lhc.get_lhc_tune_and_chroma_knobs` function.
* The `pyhdtoolkit.cpymadtools.plotters.plot_machine_layout` have now been made public api.
* The ``DEFAULT_TWISS_COLUMNS`` constant in `pyhdtoolkit.cpymadtools.constants` now includes the element length.
* A new private ``_misc`` module has been added to the `~pyhdtoolkit.utils` sub-package.

Bug Fixes
~~~~~~~~~

* The `~pyhdtoolkit.cpymadtools.plotters.AperturePlotter.plot_aperture` and `~pyhdtoolkit.cpymadtools.plotters.LatticePlotter.plot_latwiss` functions now properly propagate the *xoffset* and *xlimits* parameters to `~pyhdtoolkit.cpymadtools.plotters.plot_machine_layout`, which restores the proper functionality for these parameters and speeds up the plotting significantly when they are used.
* The `~pyhdtoolkit.cpymadtools.coupling.get_closest_tune_approach` function now does not provide chromaticiy targets in its matching, as it can mess up the algorithm when given ``CHROM`` which it does.
* The `~pyhdtoolkit.cpymadtools.matching.match_tunes_and_chromaticities` function now properly handles the knobs sent depending on the matching targets. For instance, only tune knobs are varied when only tune targets are provided. Explicitely given knobs are always sent.
* The `~pyhdtoolkit.cpymadtools.twiss.get_twiss_tfs` function now calls the ``TWISS`` command from ``MAD-X`` and accepts keyword arguments.

Documentation
~~~~~~~~~~~~~

* All docstrings have been reviewed and now include examples. Those mentioning caveats have been given special admonitions to do so.
* The documentation has gone through a **major** overhaul and is now built on ``sphinx`` and its extensions. It now also includes a quickstart tutorial, a gallery of examples, a contributing guide and a reference bibliography. Feedback on the new documentation is very welcome.

Maintenance
~~~~~~~~~~~

* The deprecated `pyhdtoolkit.cpymadtools.special` module has been removed.
* The functions in `pyhdtoolkit.cpymadtools.plotters` do not enforce any ``rcParams`` anymore, and these are fully left to the user.
* The `pyhdtoolkit.cpymadtools.lhc.match_no_coupling_through_ripkens`, `pyhdtoolkit.cpymadtools.matching.get_closest_tune_approach` and `pyhdtoolkit.cpymadtools.matching.get_lhc_tune_and_chroma_knobs` functions have been deprecated in favor of their counterparts in other modules. They will be removed in a future release.

See `v0.16.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.16.0>`_ and the `full changes since v0.15.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.15.1...0.16.0>`_.


.. _release_0.15.1:

0.15.1
------

Bug Fixes
~~~~~~~~~

* The ``misalign_lhc_ir_quadrupoles`` function in the ``cpymadtools.errors`` module can now properly handle several IPs at the same time. Its *ip* parameter has been renamed to *ips* and properly expects a sequence.

See `v0.15.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.15.1>`_ and the `full changes since v0.15.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.15.0...0.15.1>`_.


.. _release_0.15.0:

0.15.0
------

Enhancements
~~~~~~~~~~~~

* The ``LatticePlotter.plot_latwiss`` function in the ``cpymadtools.plotters`` module can now plot the k1 gradient of dipoles that have one, if asked to, which will appear with a lower alpha than regular quadrupoles. A new boolean parameter *plot_dipole_k1* is used for this.
* Type hints have been added to all elements of the ``cpymadtools.constants`` module.
* A new module, ``cpymadtools.correctors``, has been added with currently functionality to query LHC triplet and arc corrector powering status (relatively to their max powering).
* A new function, ``reset_bump_flags`` in the ``cpymadtools.special`` module which will reset all LHC IP bump flags to 0.
* Several new constants have been introduced in the ``cpymadtools.constants`` module:

  - Supplementing the ``DEFAULT_TWISS_COLUMNS`` list, a similar but slightly different one, ``MONITOR_TWISS_COLUMNS``, has been added with elements present in OMC macros.
  - Constants lists for LHC IP bump flags have been added: ``LHC_CROSSING_ANGLE_FLAGS``, ``LHC_PARALLEL_SEPARATION_FLAGS``, ``LHC_IP_OFFSET_FLAGS``, ``LHC_ANGLE_FLAGS``, ``LHC_EXPERIMENT_STATE_FLAGS`` and ``LHC_IP2_SPECIAL_FLAGS``.
  - Constants lists for LHC triplets corrector knobs have been added: ``LHC_KQSX_KNOBS``, ``LHC_KCSX_KNOBS``, ``LHC_KCSSX_KNOBS``, ``LHC_KCOX_KNOBS``, ``LHC_KCOSX_KNOBS``, ``LHC_KCTX_KNOBS`` with their signification in comments.
  - Constants lists for LHC arc corrector knobs have been added: ``LHC_KQTF_KNOBS``, ``LHC_KQS_KNOBS``, ``LHC_KSF_KNOBS``, ``LHC_KSS_KNOBS``, ``LHC_KCS_KNOBS``, ``LHC_KCO_KNOBS``, ``LHC_KCD_KNOBS``, ``LHC_KO_KNOBS`` with their signification in comments.

Maintenance
~~~~~~~~~~~

* The ``CORRECTOR_LIMITS`` dict of dict in the ``cpymadtools.constants`` module has been changed to a simple dictionary and renamed ``HLLHC_CORRECTOR_LIMITS`` as it only contained HighLumi values.
* Exceptions are properly logged as exceptions, with stack information.
* The entire ``cpymadtools.special`` module is deprecated and its contents have been mirrored in a new ``cpymadtools.lhc`` module. Users are encouraged to use the new module, as ``cpymadtools.special`` will be removed in a future release.

See `v0.15.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.15.0>`_ and the `full changes since v0.14.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.14.1...0.15.0>`_.


.. _release_0.14.1:

0.14.1
------

Maintenance
~~~~~~~~~~~

* Both tracking functions ``ptc_track_particle`` and ``track_single_particle`` in respectively the ``cpymadtools.ptc`` and ``cpymadtools.track`` modules now log a warning when a string value is given to their *sequence* argument. Giving a value means the provided sequence will be ``USE``-ed in ``MAD-X``, leading to a loss of set errors, orbit corrections etc whch the user should be well aware of. This caveat has been added to the functions' docstrings. An info level log has also been added at the start of each function for consistency with the rest of the package.

See `v0.14.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.14.1>`_ and the `full changes since v0.14.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.14.0...0.14.1>`_.


.. _release_0.14.0:

0.14.0
------

Enhancements
~~~~~~~~~~~~

* Added a new ``AperturePlotter`` class in the ``cpymadtools.plotters`` module replacing the old one, with functionality to plot the aperture tolerances as calculated from the ``APERTURE`` command in ``MAD-X``, jointly with the lattice layout.
* Added a ``CrossingSchemePlotter`` class in the ``cpymadtools.plotters`` module, with functionality to plot the orbit crossings at LHC IPs.
* The new ``TuneDiagramPlotter.plot_tune_diagram`` function in the ``cpymadtools.plotters`` module is now more customisable, can be given a title, a figure size, add legends, differentiate between resonance lines of different orders and given a specific order up to which to plot resonance lines.

Maintenance
~~~~~~~~~~~

* Functions from the ``cpymadtools.latwiss`` module have into a class named ``LatticePlotter`` in the ``cpymadtools.plotters`` module.
* The old ``AperturePlotter`` class in the ``cpymadtools.plotters`` module has been renamed to ``BeamEnvelopePlotter`` to reflect its role, and functions in this class have also been renamed accordingly.
* The old ``TuneDiagramPlotter.plot_blank_tune_diagram`` function in the ``cpymadtools.plotters`` module has replaced the ``TuneDiagramPlotter.plot_tune_diagram`` function and taken its name.
* The phd matplotlib style has a new setting for legend.framealpha set at 0.9.
* The ``cpymadtools.latwiss`` module has been removed.
* The old ``TuneDiagramPlotter.plot_blank_tune_diagram`` function in the ``cpymadtools.plotters`` module has been removed.

See `v0.14.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.14.0>`_ and the `full changes since v0.13.3 <https://github.com/fsoubelet/PyhDToolkit/compare/0.13.3...0.14.0>`_.


.. _release_0.13.3:

0.13.3
------

Enhancements
~~~~~~~~~~~~

* The ``plot_machine_layout`` function in ``cpymadtools.latwiss`` now accepts keyword arguments which are transmitted to `~matplotlib.pyplot.scatter` calls.
* The ``TuneDiagramPlotter.plot_blank_tune_diagram`` function in ``cpymadtools.plotters`` now has a *figsize* argument.

Bug Fixes
~~~~~~~~~

* All plotting functions in the ``cpymadtools`` module now have ``LaTeX``-compatible text elements.
* The ``plot_latwiss`` and ``plot_machine_survey`` functions in ``cpymadtools.latwiss`` now properly detect element types from ``TWISS`` table properties and does not rely on naming anymore.
* The ``plot_machine_layout`` function in ``cpymadtools.latwiss`` now correctly scales the colorbar to the full length of the machine and now to 1.
* The ``match_tunes_and_chromaticities`` function in ``cpymadtools.matching`` now properly handles being given either only tune targets or only chromaticity targets.
* The *BeamParameters* class in ``models.beam`` now properly builds in all cases and has a ``__repr__``.
* Fixed some calls to the ``SELECT`` command via ``cpymad`` which might previously have had unintended side effects.

Maintenance
~~~~~~~~~~~

* All functions in the ``cpymadtools`` module which offer the *telescopic_squeeze* argument now have it default to True to reflect operational scenarios of run III.
* The ``correct_lhc_orbit`` function in ``cpymadtools.orbit`` now takes a required sequence positional argument.
* The ``correct_lhc_orbit`` function in ``cpymadtools.orbit`` now defaults its mode argument to micado like the ``CORRECT`` command in ``MAD-X`` does.
* The ``AperturePlotter.plot_aperture`` function in ``cpymadtools.plotters`` now has a default figsize argument of (13, 20) instead of 15, 15.
* The minimum required version of ``tfs-pandas`` is now 3.0.0.

See `v0.13.3 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.13.3>`_ and the `full changes since v0.13.2 <https://github.com/fsoubelet/PyhDToolkit/compare/0.13.2...0.13.3>`_.


.. _release_0.13.2:

0.13.2
------

Bug Fixes
~~~~~~~~~

* Fixed the ``get_pattern_twiss function`` in ``cpymadtools.twiss``. Starting with ``cpymad`` 1.9.0, ``Table.selected_rows()`` now actually returns the indices of the selected elements rather than returning a boolean mask. The previous (faulty) behavior had been worked around in ``get_pattern_twiss``, which is now an issue. The correct ``Table.selected_rows()`` behavior is now used.

Maintenance
~~~~~~~~~~~

* The minimum ``cpymad`` required version is now 1.9.0.

See `v0.13.2 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.13.2>`_ and the `full changes since v0.13.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.13.1...0.13.2>`_.


.. _release_0.13.1:

0.13.1
------

Bug Fixes
~~~~~~~~~

* Fixed both AC Dipole installation routines in the ``cpymadtoolks.special`` module, which now use the implementation from ``omc3``'s model_creator and will provide similar results.

See `v0.13.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.13.1>`_ and the `full changes since v0.13.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.13.0...0.13.1>`_.


.. _release_0.13.0:

0.13.0
------

Enhancements
~~~~~~~~~~~~

* Added a ``install_ac_dipole_as_matrix`` function in the ``cpymadtools.special`` module to install an AC Dipole element as a matrix, which will reflect its effect on twiss functions (which the kicker implementation does not). This matrix implementation cannot be used to influence particle tracking.

Bug Fixes
~~~~~~~~~

* The ``install_ac_dipole_as_kicker`` function now properly sets the element location to avoid a negative drift (location taken from omc3's model_creator) if the sequence wasn't previously made ``THIN`` (which it should).
* The ``install_ac_dipole_as_kicker`` function now makes a use, sequence=... call after installing the element. Beware this means errors, correctors etc that were set / loaded will be lost.

Maintenance
~~~~~~~~~~~

* The ``install_ac_dipole`` function in ``cpymadtools.special`` is now named ``install_ac_dipole_as_kicker``. This kicker implementation **cannot** be used to affect twiss functions, only particle tracking.

See `v0.13.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.13.0>`_ and the `full changes since v0.12.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.12.0...0.13.0>`_.


.. _release_0.12.0:

0.12.0
------

Enhancements
~~~~~~~~~~~~

* Added a ``models`` module in ``cpymadtools`` to hold various ``pydantic`` models for data manipulated in the library functions.
* Added a ``query_beam_attributes`` function in ``cpymadtools.parameters`` that returns a parsed and validated *MADXBeam* with all ``BEAM`` attributes from the ``MAD-X`` process based on the currently defined beam.
* Added a ``ptc_twiss`` function in ``cpymadtools.ptc`` to conveniently create the ``PTC`` universe and perform a ``TWISS`` command according to the Ripken-Mais formalism.
* Added a ``ptc_track_particle`` function in ``cpymadtools.ptc`` to conveniently create the ``PTC`` universe and perform particle tracking similarly to ``cpymadtools.track.track_single_particle``.
* Added a ``get_footprint_lines`` function in ``cpymadtools.tune`` to obtain the (Qx, Qy) points needed to plot the footprint based on the *TfsDataFrame* returned by ``make_footprint_table``. To be considered experimental.
* Added a ``get_footprint_patches`` function in ``cpymadtools.tune`` to obtain a collection of ``matplotlib.patches.Polygon`` elements needed to plot the footprint based on the *TfsDataFrame* returned by ``make_footprint_table``. To be considered experimental.
* The ``get_table_tfs`` function in ``cpmadtools.utils`` now takes a *headers_table* argument to choose an internal table to use for headers.

Maintenance
~~~~~~~~~~~

* The default energy value in ``cpymadtools.special.make_lhc_beams`` has been changed to 7000 [GeV] to reflect run III scenario.
* The value for npart in ``cpymadtools.special.make_lhc_beams`` has been changed to 1.15e11 to reflect run III scenario.
* The ``make_footprint_table`` in ``cpymadtools.tune`` now returns a *TfsDataFrame* instead of a `~pandas.DataFrame`, the headers of which are populated with useful values for other functions.
* The ``beam_parameters`` function in ``cpymadtools.parameters`` has been moved to the ``optics.beam`` module and renamed ``compute_beam_parameters``.
* The default ``patch.linewidth`` value in the phd matplotlib style has been changed to 1.5.

See `v0.12.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.12.0>`_ and the `full changes since v0.11.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.11.0...0.12.0>`_.


.. _release_0.11.0:

0.11.0
------

Enhancements
~~~~~~~~~~~~

* Added a ``cpymadtools.utils`` module with convenience functions for ``cpymad.mad.Madx`` objects, for now containing a single function ``get_table_tfs`` which turns an internal ``MAD-X`` table into a *TfsDataFrame*.
* The ``get_amplitude_detuning`` and ``get_rdts`` functions in the ``cpymadtools.ptc`` module now have a fringe argument defaulting to False in order to enable fringe field calculations.
* The ``get_amplitude_detuning`` and ``get_rdts`` functions in the ``cpymadtools.ptc`` module now transmit keyword arguments to respectively ``ptc_normal`` and ``ptc_twiss``.

Documentation
~~~~~~~~~~~~~

* The ``get_amplitude_detuning`` and ``get_rdts`` functions in the ``cpymadtools.ptc`` module now contain extensive docstrings detailing their inner workings as well as parameters used in internal MAD-X commands.


See `v0.11.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.11.0>`_ and the `full changes since v0.10.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.10.0...0.11.0>`_.


.. _release_0.10.0:

0.10.0
------

Enhancements
~~~~~~~~~~~~

* The ``track_single_particle`` function in the ``cpymadtools.track`` module can now take a sequence defining observation points as argument.
* The ``track_single_particle`` function in the ``cpymadtools.track`` module can now take keyword arguments to be transmitted to the ``TRACK`` command in ``MAD-X``.

Maintenance
~~~~~~~~~~~

* The ``track_single_particle`` function in the ``cpymadtools.track`` module now defaults initial tracking coordinates to all 0.
* The ``track_single_particle`` function in the ``cpymadtools.track`` module now returns a dictionary, with one keys per defined observation point and as a value the corresponding track table. The special case where *ONETABLE* is given to ``TRACK`` as a keyword argument is handled, and then a single entry taken from the appropriate table with be found in the returned dictionary.

See `v0.10.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.10.0>`_ and the `full changes since v0.9.2 <https://github.com/fsoubelet/PyhDToolkit/compare/0.9.2...0.10.0>`_.


.. _release_0.9.2:

0.9.2
-----

Enhancements
~~~~~~~~~~~~

* Added a ``match_no_coupling_through_ripkens`` function in the ``cpymadtools.special`` module as a 0-coupling matching routine through cross-term Ripken parameters at a given location.

Bug Fixes
~~~~~~~~~

* The ``install_mpl_style`` function now installs the **.mplstyle** file also in the site-packages location for ``matplotlib``, which is sometimes where it will look when running ``plt.style.use("phd")``.
* The closest tune approach routine now properly makes use of madx.batch() to restore settings.
* The plotting functions in the ``cpymadtools.latwiss`` module have updated ``LaTeX``-compatible labels.
* The ``plot_survey`` function in the ``cpymadtools.latwiss`` module now uses clearer markers to indicate the machine survey, properly matches the colormaps of the plotted dipoles and the colorbar when using ``show_elements=True`` and lets the user config handle savefig options.

See `v0.9.2 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.9.2>`_ and the `full changes since v0.9.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.9.1...0.9.2>`_.


.. _release_0.9.1:

0.9.1
-----

Enhancements
~~~~~~~~~~~~

* Added an ``install_mpl_style`` function in the ``utils.defaults`` module to create a **phd.mplstyle** file in ``matplotlib``'s stylelib directory, making the style callable through ``plt.style.use("phd")``.

Maintenance
~~~~~~~~~~~

* The *PLOT_PARAMS* dictionary in ``utils.defaults`` has been updated.
* The ``numba`` library's used has been removed, easing the package's dependencies.

See `v0.9.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.9.1>`_ and the `full changes since v0.9.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.9.0...0.9.1>`_.


.. _release_0.9.0:

0.9.0
-----

Enhancements
~~~~~~~~~~~~

* Added a ``misalign_lhc_ir_quadrupoles`` function in the ``cpymadtools.errors`` module to conveniently apply ``EALIGN`` to IR quadrupoles.
* Added a ``misalign_lhc_triplets function`` in the ``cpymadtools.errors``, convenience wrapper around the aforementioned one for triplets.
* Added a ``correct_lhc_orbit`` function in the ``cpymadtools.orbit`` module to perform orbit correction using MCB.* elements in the LHC.
* Added a ``vary_independent_ir_quadrupoles`` function in the ``cpymadtools.special`` module to conveniently send the vary commands for the desired quadrupoles in the IRs.
* Added a ``tune`` module in ``cpymadtools`` with currently a ``make_footprint_table`` function that creates a ``DYNAP`` setup according to parameters and returns the generated table.
* Added A ``utils.htc_monitor`` module with functionality to query the ``HTCondor`` queue, process the returned data and nicely display it. To be ran directly, but different functionality can be imported.

Bug Fixes
~~~~~~~~~

* Fixed an issue in ``plot_latwiss`` where the function would sometimes mishandle the *xlimits* argument.
* Fixed a mistake in ``apply_lhc_rigidity_waist_shift_knob`` where the side argument would be ignored if uppercase.

Maintenance
~~~~~~~~~~~

* The *telescopic_squeeze* parameter in ``match_tunes_and_chromaticities`` now defaults to True, to reflect the LHC scenario as of Run III.
* The ``get_ips_twiss`` and ``get_ir_twiss`` functions have been moved from ``cpymadtools.special`` to ``cpymadtools.twiss``.
* Added dependencies: ``pydantic``, ``rich`` and ``pendulum``. The ``llvmlite`` dependency is also added explicitely, though it is a dependency of ``numba`` and the version constraint is here to guarantee ``pyhdtoolkit`` will build on Python 3.9.
* Tests now include Python 3.9.

See `v0.9.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.9.0>`_ and the `full changes since v0.8.5 <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.5...0.9.0>`_.


.. _release_0.8.5:

0.8.5
-----

Bug Fixes
~~~~~~~~~

* The ``match_tunes_and_chromaticities`` function now properly behaves if some of the targets are set to 0.

Maintenance
~~~~~~~~~~~

* The default behavior in lattice slicing is changed to have makedipedge as False, which compensates the effect of the default slicing style ``TEAPOT``.

See `v0.8.5 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.5>`_ and the `full changes since v0.8.4 <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.4...0.8.5>`_.


.. _release_0.8.4:

0.8.4
-----

Enhancements
~~~~~~~~~~~~

* Added an *xoffset* variable to ``plot_latwiss``, allowing to center the plot on a specific element.

Maintenance
~~~~~~~~~~~

* The machine layout plotting in ``plot_latwiss`` has been exported to its own function. It is a private function.

See `v0.8.4 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.4>`_ and the `full changes since v0.8.3 <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.3...0.8.4>`_.


.. _release_0.8.3:

0.8.3
-----

Enhancements
~~~~~~~~~~~~

* Added a function in ``cpymadtools.twiss`` to export the entire twiss table to a *TfsDataFrame*.

See `v0.8.3 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.3>`_ and the `full changes since v0.8.2 <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.2...0.8.3>`_.


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

See `v0.8.2 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.2>`_ and the `full changes since v0.8.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.1...0.8.2>`_.


.. _release_0.8.1:

0.8.1
-----

Bug Fixes
~~~~~~~~~

* Fixed inacurrate logging statements during tunes and chromaticities matching.

Maintenance
~~~~~~~~~~~

* Removed the unused **scripts** folder as well as the scripts' dependencies.

See `v0.8.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.1.0>`_ and the `full changes since v0.8.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.8.0...0.8.1>`_.


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

See `v0.8.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.8.0>`_ and the `full changes since v0.7.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.7.0...0.8.0>`_.


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

See `v0.7.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.7.0>`_ and the `full changes since v0.6.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.6.0...0.7.0>`_.


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

See `v0.6.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.6.0>`_ and the `full changes since v0.5.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.5.0...0.6.0>`_.


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

See `v0.5.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.5.0>`_ and the `full changes since v0.4.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.4.1...0.5.0>`_.


.. _release_0.4.1:

0.4.1
-----

Bug Fixes
~~~~~~~~~

* Quick fix of a type hinting issue causing imports to crash.

See `v0.4.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.4.1>`_ and the `full changes since v0.4.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.4.0...0.4.1>`_.


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

See `v0.4.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.4.0>`_ and the `full changes since v0.3.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.3.0...0.4.0>`_.


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

See `v0.3.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.3.0>`_ and the `full changes since v0.2.1 <https://github.com/fsoubelet/PyhDToolkit/compare/0.2.1...0.3.0>`_.


.. _release_0.2.1:

0.2.1
-----

Enhancements
~~~~~~~~~~~~

* New module for AC Dipole or Free Oscillations (with amplitude offset) tracking (in scripts).

Maintenance
~~~~~~~~~~~

* Some slight changes to **README**, **Makefile** and **Dockerfile**.

See `v0.2.1 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.2.1>`_ and the `full changes since v0.2.0 <https://github.com/fsoubelet/PyhDToolkit/compare/0.2.0...0.2.1>`_.


.. _release_0.2.0:

0.2.0
-----

Enhancements
~~~~~~~~~~~~

* An **EVM** implementation for nonconvex phase synchronisation (in module ``omc_math``).
* Logging and contexts utilities from ``fsbox`` (props to ``pylhc/omc3`` for creating those).

See `v0.2.0 release notes on GitHub <https://github.com/fsoubelet/PyhDToolkit/releases/tag/0.2.0>`_ and the `full changes from the previous release <https://github.com/fsoubelet/PyhDToolkit/compare/0.1.1...0.2.0>`_.