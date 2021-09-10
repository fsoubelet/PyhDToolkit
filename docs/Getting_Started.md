# Getting Started

## Installation

This package is tested for and supports `Python 3.7+`, although it should be compatible with `Python 3.6`.
You can install it simply in a virtual environment with:

```bash
pip install pyhdtoolkit
```

!!! tip "Installation in a virtual environment"
    Don't know what a **virtual environment** is or how to set it up? Here is a good
    [primer on virtual environments][virtual_env_primer] by RealPython.

??? question "How about a development environment?"

    Sure thing. This repository uses [Poetry] as a packaging and build tool. To set yourself 
    up, get a local copy through VCS and run:
    
    ```bash
    poetry install
    ```
    
    This repository follows the `Google` docstring format, uses [Black][black_formatter] as a code formatter with a default enforced line length of 100 characters, and [Pylint][pylint_ref] as a linter.
    You can format the code with `make format` and lint it (which will format first) with `make lint`.
    
    Testing builds are ensured after each commit through Github Actions.
    You can run tests locally with the predefined `make tests`, or through `poetry run pytest <options>` for customized options.

??? question "How can I easily reproduce your research done with this?"

    This repository comes with an `environment.yml` file to reproduce my work `conda` environment, feel free to use it.
    If you checked out from version control, you can install this environment and add it to your ipython kernel by running `make condaenv`.
    
    If you are comfortable with containers, a fully-fetched one is provided and accessible through Docker as explained below. 

## Using With Docker

Docker provides an easy way to get access to a fully-fledged environment identical to the one I use, for reproducibility of my results.
You can directly pull a pre-built image from `Dockerhub` with:
```bash
docker pull fsoubelet/simenv
```

You can then run a server from within the container and bind a local directory to work on.
Assuming you pulled the provided image from Dockerhub, run a jupyterlab server on port `8888` with the command:
```bash
docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work fsoubelet/simenv
```

Any jupyter notebook or Python files in the mounted directory can then be used / ran with an environment identical to mine.

## Examples

One can find some example notebooks showcasing use of `pyhdtoolkit` in the following [repository][workflows_repo].

## Citing

If you have a use of these codes, please consider citing them.
The repository has a [DOI] provided by [Zenodo], and all versions can be cited with the following BibTeX entry:
```bibtex
@software{pyhdtoolkit,
  author       = {Felix Soubelet},
  title        = {fsoubelet/PyhDToolkit},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.4268804},
  url          = {https://doi.org/10.5281/zenodo.4268804}
}
```

To cite a specific version, select the version on the package's page on Zotero and export the BibTex entry at the bottom right of the page.

[virtual_env_primer]: https://realpython.com/python-virtual-environments-a-primer/
[black_formatter]: https://github.com/psf/black
[Docker]: https://www.docker.com/
[gitflow_ref]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
[pip]: https://pip.pypa.io/en/stable/
[Poetry]: https://python-poetry.org/
[pylint_ref]: https://www.pylint.org/
[workflows_repo]: https://github.com/fsoubelet/Workflows
[DOI]: https://zenodo.org/badge/latestdoi/227081702
[Zenodo]: https://zenodo.org
