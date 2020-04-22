# Copyright 2019 Felix Soubelet <felix.soubelet@cern.ch>
# MIT License

# Documentation for most of what you will see here can be found at the following links:
# for the GNU make special targets: https://www.gnu.org/software/make/manual/html_node/Special-Targets.html
# for python packaging: https://docs.python.org/3/distutils/introduction.html

# ANSI escape sequences for bold, cyan, dark blue, end, pink and red.
B = \033[1m
C = \033[96m
D = \033[34m
E = \033[0m
P = \033[95m
R = \033[31m

.PHONY : help checklist clean condaenv docker-build format install lines lint tests

all: install

help:
	@echo "Please use 'make $(R)<target>$(E)' where $(R)<target>$(E) is one of:"
	@echo "  $(R) checklist $(E)      to print a pre-release check-list."
	@echo "  $(R) clean $(E)          to recursively remove build, run, and bitecode files/dirs."
	@echo "  $(R) condaenv $(E)       to 'conda create' the specific 'PHD' environment I use. Personnal."
	@echo "  $(R) docker-build $(E)   to build a container image replicating said environment (and other goodies)."
	@echo "  $(R) format $(E)         to recursively apply PEP8 formatting through the 'Black' cli tool."
	@echo "  $(R) install $(E)        to 'poetry install' this package into the project's virtual environment."
	@echo "  $(R) lines $(E)          to count lines of code with the 'tokei' tool."
	@echo "  $(R) lint $(E)           to lint the code though 'PyLint'."
	@echo "  $(R) tests $(E)          to run tests with the the pytest package."

checklist:
	@echo "Here is a small pre-release check-list:"
	@echo "  - Check you are on a tagged $(P)feature/release$(E) branch (see Gitflow workflow)."
	@echo "  - Run $(D)poetry bump$(E) with the right argument and update the version number in $(C)__init__.py$(E)."
	@echo "  - Check the $(P)feature/release$(E) branch tag matches this release's package version."
	@echo "  - After merging and pushing this release from $(P)master$(E) to $(P)origin/master$(E):"
	@echo "     - Run $(D)poetry build$(E) to create a tarball of the new version."
	@echo "     - Run $(D)poetry publish$(E) to push the new version to PyPI."
	@echo "     - Create a Github release and upload the created tarball."
	@echo "     - Run 'make $(R)clean$(E)'."

clean:
	@echo "Cleaning up distutils remains."
	@rm -rf build
	@rm -rf dist
	@rm -rf pyhdtoolkit.egg-info
	@rm -rf .eggs
	@echo "Cleaning up bitecode files and python cache."
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	@echo "Cleaning up pytest cache."
	@find . -type d -name '*.pytest_cache'  -exec rm -rf {} + -o -type f -name '*.pytest_cache' -exec rm -rf {} +
	@echo "All cleaned up!\n"

condaenv:
	@echo "Creating $(D)PHD$(E) conda environment according to '$(C)environment.yml$(E)' file."
	@conda env create -f environment.yml
	@echo "Adding $(D)PHD$(E) environment to base ipython kernel."
	@source activate PHD
	@ipython kernel install --user --name=PHD
	@conda deactivate

docker-build:
	@echo "Building docker image with $(D)PHD$(E) conda environment, with tag $(P)simenv$(E)."
	@docker build -t simenv .
	@echo "Done. You can run this with $(P)docker run -it --rm --init simenv$(E)."

format:
	@echo "Formatting code to PEP8, default line length is 120."
	@poetry run black .

install: format clean
	@echo "Installing through $(D)poetry$(E), with dev dependencies but no extras."
	@poetry install -v

lines: format
	@tokei .

lint: format
	@echo "Linting code, ignoring the following message IDs:"
	@echo "  - $(P)C0330$(E) $(C)'bad-continuation'$(E) since it somehow doesn't play friendly with $(B)Black$(E)."
	@echo "  - $(P)W0106$(E) $(C)'expression-not-assigned'$(E) since it triggers on class attribute reassignment."
	@echo "  - $(P)C0103$(E) $(C)'invalid-name'$(E) because there are too many at the moment :(."
	@echo "  - $(P)E0401$(E) $(C)'import error'$(E) because PyLint is confused with the conda environments."
	@echo "  - $(P)W1202$(E) $(C)'logging-format-interpolation'$(E) because on this, PyLint is full of shit.\n"
	@poetry run pylint -j 0 --max-line-length=120 --disable=C0330,W0106,C0103,W1202,R0903,E0401 pyhdtoolkit/

tests: format clean
	@poetry run pytest --no-flaky-report --verbose
	@make clean

# Catch-all unknow targets without returning an error. This is a POSIX-compliant syntax.
.DEFAULT:
	@echo "Make caught an invalid target! See help output below for available targets."
	@make help
