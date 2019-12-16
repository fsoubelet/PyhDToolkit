# Copyright 2019 Felix Soubelet <felix.soubelet@cern.ch>
# MIT License

.PHONY : help black clean condaenv install isort lines pipreq uninstall tests

help:
	@echo "Please use 'make <target>' where <target> is one of:"
	@echo "  black         to recursively apply PEP8 formatting through the 'Black' cli tool."
	@echo "  clean         to recursively remove build, run, and bitecode files/dirs."
	@echo "  condaenv      to 'conda install' the specific 'PHD' environment I use. Personnal."
	@echo "  install       to 'pip install' this package into your activated environment."
	@echo "  isort         to recursively sort import statements. Called by 'make black'."
	@echo "  lines         to count lines of code with the 'tokei' tool."
	@echo "  pipreq        to 'pip install' packages listed in 'requirements.txt' into your activated environment."
	@echo "  uninstall     to uninstall the 'pyhdtoolkit' package from your activated environment."
	@echo "  tests         to run tests with the the pytest package."

all: install

black: isort
		@echo "Linting code to PEP8, default line length is 120."
		@black -l 120 .

clean:
		@echo "Cleaning up distutils remains."
		@rm -rf build
		@rm -rf dist
		@echo "Cleaning up bitecode files. and python cache."
		@find ./ -name '*.py[co]' -exec rm -f {} \;
		@echo "Cleaning up python cache."
		@find ./ -name '__pycache__' | xargs rm -rf

condaenv:
		@echo "Creating conda environment according to 'environment.yml' file."
		@conda env create -f environment.yml
		@echo "Adding 'PHD' environment to ipython kernel."
		@source activate PHD
		@ipython kernel install --user --name=PHD
		@conda deactivate

install: black
		@echo "Installing local package to your active environment."
		@pip install .
		@echo "Logging install date to install_log.txt"
		@date > install_log.txt

isort:
		@echo "Sorting import statements."
		@isort -rc -q .

lines: black
		@tokei .

pipreq:
		@pip install -r requirements.txt

uninstall:
		@pip uninstall pyhdtoolkit

tests: black clean
		@source activate PHD
		@pytest tests