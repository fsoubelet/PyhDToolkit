# About PyhDToolkit

## Purpose

This package is an all-in-one collection of baseline utilities I use in my PhD work.
Most of the codes here have their use in my day-to-day work, but not necessarily in our team's softwares.

## Functionality

For now, `PyhDToolkit` provides some of the following features:

- A `cpymadtools` module with tools to integrate with [`cpymad`][cpymad], a Python bindings library for the [`MAD-X`][madx] code; including generators, matching routines, plotting utilities etc.
- A `maths` module to incorporate useful methods used in analysis.
- An `optics` module for particle accelerator physics related calculations and analysis.
- A `plotting` module for my favorite defaults and helpers.
- A `tfstools` module similar to `cpymadtools`, with functionality revolving around handling `tfs` files and plotting their contents.
- A `utils` module for various Python and UNIX utilities.

## Roadmap

In addition to developping current modules, more will be added to better incorporate with the workhorse softwares of the OMC team, notably [`tfs-pandas`][tfs] and [`omc3`][omc3].
Foreseen development includes:

- Expansion of the `optics` module to include most simple calculations on beam properties.
- Expansion of the `cpymadtools` with utilities as their needs arise in my studies.
- A `sixtracklibtools` module for utility functions surrounding the use of [`sixtracklib`][sixtracklib], eventually.

[cpymad]: https://github.com/hibtc/cpymad
[madx]: https://mad.web.cern.ch/mad/
[omc3]: https://github.com/pylhc/omc3
[tfs]: https://github.com/pylhc/tfs
[sixtracklib]: https://github.com/SixTrack/sixtracklib
