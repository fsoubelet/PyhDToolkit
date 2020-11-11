# About PyhDToolkit

## Purpose

This package is meant to be an all-in-one collection of utilities and scripts I use in my PhD work.
Most of the codes here have their use in my day-to-day work, but not necessarily in our team's softwares.

## Functionality

For now, `PyhDToolkit` provides some of the following features:

- Useful tools to integrate with [`cpymad`][cpymad], a Python bindings library for the [`MAD-X`][madx] code, including generators, matching routines and plotting utilities.
- A `maths` module to incorporate useful methods used in analysis.
- A `plotting` module for my favorite defaults and helpers.
- An `optics` module for particle accelerator physics related calculations and analysis.
- A `scripts` module to handle different simulations setups.
- A `tfstools` module similar to `cpymadtools`, with functionality revolving around handling `tfs` files and plotting their contents.
- A `utils` module for various utilities.

## Roadmap

In addition to developping current modules, more will be added to better incorporate with the workhorse softwares of the OMC team, notably [`tfs-pandas`][tfs] and [`omc3`][omc3].
Foreseen development includes:

- Expansion of existing modules, particularly the `optics` module to include most simple calculations on beam properties.
- An `omcwrapper` module to handle different usecases of the `omc3` package.
- A `sixtracklibtools` module for utility functions surrounding the use of `sixtracklib`.

[cpymad]: https://github.com/hibtc/cpymad
[madx]: https://mad.web.cern.ch/mad/
[omc3]: https://github.com/pylhc/omc3
[tfs]: https://github.com/pylhc/tfs
