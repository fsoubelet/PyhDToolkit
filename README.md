<h1 align="center">
  <b>pyhdtoolkit</b>
</h1>

<p align="center">
  <!-- PyPi Version -->
  <a href="https://pypi.org/project/pyhdtoolkit">
    <img alt="PyPI Version" src="https://img.shields.io/pypi/v/pyhdtoolkit?label=PyPI&logo=PyPI">
  </a>

  <!-- Github Release -->
  <a href="https://github.com/fsoubelet/PyhDToolkit/releases">
    <img alt="Github Release" src="https://img.shields.io/github/v/release/fsoubelet/PyhDToolkit?color=orange&label=Release&logo=Github">
  </a>

  <br/>

  <!-- Travis Build -->
  <a href="https://travis-ci.org/github/fsoubelet/PyhDToolkit">
    <img alt="Travis Build" src="https://img.shields.io/travis/fsoubelet/pyhdtoolkit?label=Travis%20CI&logo=Travis">
  </a>

  <!-- Code Coverage -->
  <a href="https://codeclimate.com/github/fsoubelet/PyhDToolkit/maintainability">
    <img alt="Code Coverage" src="https://img.shields.io/codeclimate/maintainability/fsoubelet/PyhDToolkit?label=Maintainability&logo=Code%20Climate">
  </a>

  <!-- Docker Build -->
  <a href="https://hub.docker.com/r/fsoubelet/simenv">
    <img alt="Docker Build" src="https://img.shields.io/docker/cloud/build/fsoubelet/simenv?label=Docker%20Build&logo=Docker">
  </a>

  <br/>

  <!-- Code style -->
  <a href="https://github.com/psf/Black">
    <img alt="Code Style" src="https://img.shields.io/badge/Code%20Style-Black-9cf.svg">
  </a>

  <!-- Linter -->
  <a href="https://github.com/PyCQA/pylint">
    <img alt="Linter" src="https://img.shields.io/badge/Linter-Pylint-ce963f.svg">
  </a>

  <!-- Build tool -->
  <a href="https://github.com/python-poetry/poetry">
    <img alt="Build tool" src="https://img.shields.io/badge/Build%20Tool-Poetry-4e5dc8.svg">
  </a>

  <!-- Test runner -->
  <a href="https://github.com/pytest-dev/pytest">
    <img alt="Test runner" src="https://img.shields.io/badge/Test%20Runner-Pytest-ce963f.svg">
  </a>

  <!-- License -->
  <a href="https://github.com/fsoubelet/PyhDToolkit/blob/master/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/fsoubelet/PyhDToolkit?color=9cf&label=License">
  </a>
</p>

<p align="center">
  ♻️ An all-in-one package for Python work in my PhD
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img alt="Made With Python" src="https://forthebadge.com/images/badges/made-with-python.svg">
  </a>
</p>

## Installation

This code is compatible with `Python 3.6+`.
If for some reason you have a need for it, create & activate a virtual enrivonment, then install with pip:
```bash
> pip install pyhdtoolkit
```

This repository respects the [PEP 518][pep_518_ref] development and build recommandations, and [Poetry][poetry_ref] as a tool to do so.
If you intend on making changes, clone this repository through VCS and set yourself up with:
```bash
> git clone https://github.com/fsoubelet/PyhDToolkit.git
> cd PyhDToolkit
> poetry install
```

## Standards, Testing, Tools and VCS

This repository follows the `Google` docstring format, uses [Black][black_formatter] as a code formatter with a default enforced line length of 100 characters, and [Pylint][pylint_ref] as a linter.
You can format the code with `make format` and lint it (which will format first) with `make lint`.

Testing builds are ensured after each commit through Travis-CI.
You can run tests locally with the predefined `make tests`, or through `poetry run pytest <options>` for customized options.

VCS is done through [git][git_ref] and follows the [Gitflow][gitflow_ref] workflow.
As a consequence, make sure to always install from `master`.

## Miscellaneous

Feel free to explore the `Makefile` for sensible defaults commands.
You will get an idea of what functionality is available by running `make help`.

### Python Environment

This repository currently comes with an `environment.yml` file to reproduce my work `conda` environment.
You can install this environment and add it to your ipython kernel by running `make condaenv`.

### Container

You can directly pull a pre-built image - tag `latest` is an automated build - from `Dockerhub` with:
```bash
> docker pull fsoubelet/simenv
```

You can then run the container in interactive mode, and make use of the already activated `conda` environment.
It is highly advised to run with `--init` for zombie processes protection (see [Tini][tini_ref] for details).
Assuming you pulled the provided image from Dockerhub, the command is then (remove the `--rm` flag if you wish to preserve it after running):
```bash
> docker run -it --rm --init fsoubelet/simenv
```

If you want to do some exploration through `jupyter` you will need to install it first as it is not bundled in the image, then add the custom environment kernelspec.
Run the following command before heading over to `localhost:8888`:
```bash
> docker run -it --rm --init -p 8888:8888 fsoubelet/simenv /bin/bash -c "/opt/conda/bin/conda install -c conda-forge jupyterlab -y --quiet > /dev/null && mkdir /opt/notebooks && /opt/conda/envs/PHD/bin/ipython kernel install --user --name=PHD && /opt/conda/bin/jupyter lab --notebook-dir=/opt/notebooks --ip='*' --port=8888 --no-browser --allow-root"
```

## License

Copyright &copy; 2019-2020 Felix Soubelet. [MIT License][license]

[black_formatter]: https://github.com/psf/black
[docker_cp_doc]: https://docs.docker.com/engine/reference/commandline/cp/
[gitflow_ref]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
[git_ref]: https://git-scm.com/
[license]: https://github.com/fsoubelet/PyhDToolkit/blob/master/LICENSE
[oci_ref]: https://www.opencontainers.org/
[pep_518_ref]: https://www.python.org/dev/peps/pep-0518/
[poetry_ref]: https://github.com/python-poetry/poetry
[pylint_ref]: https://www.pylint.org/
[tini_ref]: https://github.com/krallin/tini
