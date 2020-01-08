# PyhDToolkit: An all-in-one toolkit package for Python work in my PhD.

This repository is a package gathering a number of Python utilities for my work.

## Installation

This code is compatible with `Python 3.6+`.
If for some reason you have a need for this package, first install the prerequisites with:
```bash
make pipreq
```

Then, you can simply install it with:
```bash
pip install -e git+https://github.com/fsoubelet/PyhDToolkit.git@master#egg=pyhdtoolkit
```

The `-e` flag should only be included if you intend to make some hotfix changes to the site-package.
If you intend on making actual changes, then you should clone this repository through VCS, and install it into your virtual environment with:
```bash
git clone https://github.com/fsoubelet/PyhDToolkit.git
cd PyhDToolkit
make
```

## Testing

Tests are currently a work in progress.
Testing builds are ensured after each commit through Travis-CI.

You can run tests locally with:
```bash
make tests
```

## Standards, Tools and VCS

This repository respects the PyCharm docstring format, and uses [Black][black_formatter] as a code formatter.
The default enforced line length is 120 characters.
You can lint the code with:
```bash
make black
```

VCS is done through [git][git_ref] and follows the [Gitflow][gitflow_ref] workflow.
As a consequence, make sure to always install from `master`.

## Miscellaneous Goodies

Feel free to explore the `Makefile` and make use of the functions it offers.
You can get an idea of what is available to you by running:
```bash
make help
```

This repository currently comes with an `environment.yml` file to reproduce a fully compatible conda environment.
You can install this environment and add it to your ipython kernel by running:
```bash
make condaenv
```

A Dockerfile and later on an [OCI][oci_ref]-compliant file are to come.

## License

Copyright &copy; 2019-2020 Felix Soubelet. [MIT License][license]

[black_formatter]: https://github.com/psf/black
[gitflow_ref]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
[git_ref]: https://git-scm.com/
[license]: https://github.com/fsoubelet/PyhDToolkit/blob/master/LICENSE
[oci_ref]: https://www.opencontainers.org/