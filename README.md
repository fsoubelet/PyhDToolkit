# PyhDToolkit: An all-in-one toolkit package for Python work in my PhD.

This repository is a package gathering a number of Python utilities for my work.

## Installation

This code is compatible with `Python 3.6+`.
If for some reason you have a need for it, you should first install the prerequisites with:
```bash
make pipreq
```

Then, you can simply install it with:
```bash
pip install --editable git+https://github.com/fsoubelet/PyhDToolkit.git@master#egg=pyhdtoolkit
```

The `--editable` flag should only be included if you intend to make some hotfix changes to the site-package.
If you intend on making actual changes, then you should clone this repository through VCS, and install it into a virtual environment.
With `git`, this would be:
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

This repository respects the PyCharm docstring format, uses [Black][black_formatter] as a code formatter with a default enforced line length of 120 characters, and [Pylint][pylint_ref] as a linter.
You can format the code with:
```bash
make black
```

You can lint the code with:
```bash
make lint
```

VCS is done through [git][git_ref] and follows the [Gitflow][gitflow_ref] workflow.
As a consequence, make sure to always install from `master`.

## Miscellaneous

Feel free to explore the `Makefile` and make use of the functions it offers.
You will get an idea of what functionality is available to you by running:
```bash
make help
```

### Environment 

This repository currently comes with an `environment.yml` file to reproduce a fully compatible conda environment.
You can install this environment and add it to your ipython kernel by running:
```bash
make condaenv
```

### Container

A Dockerfile is included if you want to build a container image from source.
You can do so, building with the tag `simenv`, with the command:
```bash
make docker-build
```

Alternatively, you can directly pull a pre-built image from Dockerhub with:
```bash
make docker-pull
```

You can then run your container in interactive mode, and use the already activated conda environment for your work.
It is highly advised to run with `--init` for zombie processes protection, see [Tini][tini_ref] for details.
Assuming you pulled the provided image from Dockerhub, the command is then:
```bash
docker run -it --rm --init fsoubelet/simenv
```

If you want to do some exploration through a `jupyter` interface then you need to tell your container to install it first, as it is not bundled in miniconda, then add the custom environment kernelspec.
The following command will take care of all this:
```bash
docker run -it --rm --init -p 8888:8888 fsoubelet/simenv /bin/bash -c "/opt/conda/bin/conda install -c conda-forge jupyterlab -y --quiet > /dev/null && mkdir /opt/notebooks && /opt/conda/envs/PHD/bin/ipython kernel install --user --name=PHD && /opt/conda/bin/jupyter lab --notebook-dir=/opt/notebooks --ip='*' --port=8888 --no-browser --allow-root"
```

You can then copy the provided token and head to `localhost:8888` on your local machine.

## License

Copyright &copy; 2019-2020 Felix Soubelet. [MIT License][license]

[black_formatter]: https://github.com/psf/black
[gitflow_ref]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
[git_ref]: https://git-scm.com/
[license]: https://github.com/fsoubelet/PyhDToolkit/blob/master/LICENSE
[oci_ref]: https://www.opencontainers.org/
[pylint_ref]: https://www.pylint.org/
[tini_ref]: https://github.com/krallin/tini