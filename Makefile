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

.PHONY : help checklist clean condaenv docker documentation format install interrogate lines lint tests type

all: install

help:
	@echo "Please use 'make $(R)<target>$(E)' where $(R)<target>$(E) is one of:"
	@echo "  $(R) clean $(E)  \t  to recursively remove build, run, and bitecode files/dirs."
	@echo "  $(R) condaenv $(E)  \t  to $(D)conda create$(E) the specific 'PHD' environment I use. Personnal."
	@echo "  $(R) docker $(E)  \t  to build a $(P)Docker$(E) container image replicating said environment (and other goodies)."
	@echo "  $(R) docs $(E)  \t  to build the documentation for the package."
	@echo "  $(R) format $(E)  \t  to recursively apply PEP8 formatting through the $(P)Black$(E) and $(P)isort$(E) cli tools."
	@echo "  $(R) install $(E)  \t  to $(D)poetry install$(E) this package into the project's virtual environment."
	@echo "  $(R) lines $(E)  \t  to count lines of code with the $(P)tokei$(E) tool."
	@echo "  $(R) lint $(E)  \t  to lint the code though $(P)Pylint$(E)."
	@echo "  $(R) tests $(E)  \t  to run tests with the $(P)pytest$(E) package."
	@echo "  $(R) typing $(E)  \t  to run type checking with the $(P)mypy$(E) package."

build:
	@echo "Re-building wheel and dist"
	@rm -rf dist
	@poetry build
	@echo "Created build is located in the $(C)dist$(E) folder."

clean:
	@echo "Cleaning up documentation pages."
	@rm -rf doc_build
	@rm -rf plot_directive
	@echo "Cleaning up distutils remains."
	@rm -rf build
	@rm -rf dist
	@rm -rf pyhdtoolkit.egg-info
	@rm -rf .eggs
	@echo "Cleaning up bitecode files and python cache."
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	@echo "Cleaning up pytest cache & test artifacts."
	@find . -type d -name '*.pytest_cache' -exec rm -rf {} + -o -type f -name '*.pytest_cache' -exec rm -rf {} +
	@find . -type f -name 'fc.*' -delete -o -type f -name 'fort.*' -delete
	@echo "Cleaning up mypy cache."
	@find . -type d -name "*.mypy_cache" -exec rm -rf {} +
	@echo "Cleaning up coverage reports."
	@find . -type f -name '.coverage*' -exec rm -rf {} + -o -type f -name 'coverage.xml' -delete
	@echo "All cleaned up!\n"

condaenv:
	@echo "Creating $(D)PHD$(E) conda environment according to '$(C)environment.yml$(E)' file."
	@conda env create -f docker/environment.yml
	@echo "Adding $(D)PHD$(E) environment to base ipython kernel."
	@source activate PHD
	@ipython kernel install --user --name=PHD
	@conda deactivate

docs: clean
	@echo "Building static pages with $(D)Sphinx$(E)."
	@poetry run python -m sphinx -b html docs doc_build -d doc_build

docker:
	@echo "Building $(P)simenv$(E) Docker image with $(D)PHD$(E) conda environment, with tag $(P)latest$(E)."
	@docker build -f ./docker/Dockerfile -t simenv .
	@docker tag simenv simenv:latest
	@echo "Done. You can run this with $(P)docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work simenv$(E)."

format:
	@echo "Sorting imports with $(P)isort$(E) and formatting code to PEP8 with $(P)Black$(E), max line length is 120 characters."
	@poetry run isort . && black .

install: format clean
	@echo "Installing through $(D)Poetry$(E), with dev dependencies but no extras."
	@poetry install -v

lines: format
	@tokei .

lint: format
	@echo "Linting code with $(P)Pylint$(E)."
	@poetry run pylint pyhdtoolkit/

tests: format clean
	@poetry run pytest --no-flaky-report -n auto -p no:sugar
	@make clean

typing: format
	@echo "Checking code typing with $(P)mypy$(E)."
	@poetry run mypy pyhdtoolkit
	@make clean

# Catch-all unknow targets without returning an error. This is a POSIX-compliant syntax.
.DEFAULT:
	@echo "Make caught an invalid target! See help output below for available targets."
	@make help
