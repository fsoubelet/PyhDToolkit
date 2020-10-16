# Getting Started

## Installation

This code is compatible with `Python 3.7+`.
There are two possible methods for using this package: either as a Python package with [pip]{target=_blank}, or as a [Docker]{target=_blank} image.

### With pip

You can now install this simply in a virtual environment with:

```bash
> pip install pyhdtoolkit
```

!!! tip "Installation in a virtual environment"
    Don't know what a **virtual environment** is or how to set it up? Here is a good
    [primer on virtual environments][virtual_env_primer]{target=_blank} by RealPython.

??? question "How about a development environment?"

    Sure thing. This repository uses [Poetry]{target=_blank} as a packaging and build tool. To set yourself 
    up, get a local copy through VCS and run:
    
    ```bash
    poetry install
    ```
    
    This repository follows the `Google` docstring format, uses [Black][black_formatter] as a code formatter with a default enforced line length of 100 characters, and [Pylint][pylint_ref] as a linter.
    You can format the code with `make format` and lint it (which will format first) with `make lint`.
    
    Testing builds are ensured after each commit through Github Actions.
    You can run tests locally with the predefined `make tests`, or through `poetry run pytest <options>` for customized options.
    
    Please follow the [Gitflow][gitflow_ref] workflow.

??? question "How can I easily reproduce your research done with this?"

    This repository comes with an `environment.yml` file to reproduce my work `conda` environment, feel free to use it.
    If you checked out from version control, you can install this environment and add it to your ipython kernel by running `make condaenv`.
    You can also make use of a fully-fetched one through Docker as explained below. 

### With Docker

You can directly pull a pre-built image from `Dockerhub` (with tag `latest` being an automated build) with:
```bash
> docker pull fsoubelet/simenv
```

You can then run a server from within the container and bind a local directory to work on.
Assuming you pulled the provided image from Dockerhub, run a jupyterlab server on port `8888` with the command:
```bash
> docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work fsoubelet/simenv
```

[virtual_env_primer]: https://realpython.com/python-virtual-environments-a-primer/
[black_formatter]: https://github.com/psf/black
[Docker]: https://www.docker.com/
[gitflow_ref]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
[pip]: https://pip.pypa.io/en/stable/
[Poetry]: https://python-poetry.org/
[pylint_ref]: https://www.pylint.org/
