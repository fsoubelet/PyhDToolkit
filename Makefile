# Copyright 2019 Felix Soubelet <felix.soubelet@cern.ch>
# MIT License

# Documentation for most of what you will see here can be found at the following links:
# for the GNU make special targets: https://www.gnu.org/software/make/manual/html_node/Special-Targets.html
# for python packaging: https://docs.python.org/3/distutils/introduction.html

# ANSI escape sequences for colors
B = \033[1m  # bold
C = \033[96m  # cyan
D = \033[34m  # dark blue
E = \033[0m  # end
P = \033[95m  # pink
R = \033[31m  # red
Y = \033[33m  # yellow

.PHONY : help build clean docker docs format install lines lint typing tests

all: install

help:
	@echo "Please use 'make $(R)<target>$(E)' where $(R)<target>$(E) is one of:"
	@echo "  $(R) build $(E)   to build wheel and source distribution with $(P)uv$(E)."
	@echo "  $(R) clean $(E)   to recursively remove build, run and bitecode files/dirs."
	@echo "  $(R) docker $(E)  to build a $(P)Docker$(E) container image replicating said environment (and other goodies)."
	@echo "  $(R) docs $(E)    to build the documentation for the package with $(P)Sphinx$(E)."
	@echo "  $(R) format $(E)  to recursively apply PEP8 formatting through the $(P)Black$(E) and $(P)isort$(E) cli tools."
	@echo "  $(R) install $(E) to install this package into the current environment (editable install)."
	@echo "  $(R) lines $(E)   to count lines of code with the $(P)tokei$(E) tool."
	@echo "  $(R) lint $(E)    to lint the code though $(P)Ruff$(E)."
	@echo "  $(R) tests $(E)   to run the test suite with $(P)pytest$(E) (parallelized)."


# ----- Dev Targets ----- #

build:
	@echo "Re-building wheel and dist"
	@rm -rf dist
	@uv build
	@echo "Created build is located in the $(C)dist$(E) folder."

clean:
	@echo "Cleaning up documentation pages."
	@rm -rf doc_build
	@rm -rf plot_directive
	@echo "Cleaning up sphinx-gallery build artifacts."
	@rm -rf docs/gallery
	@rm -rf docs/gen_modules
	@echo "Cleaning up package build remains."
	@rm -rf build
	@rm -rf dist
	@rm -rf pyhdtoolkit.egg-info
	@rm -rf .eggs
	@echo "Cleaning up bitecode files and python cache."
	@find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	@echo "Cleaning up Jupyter notebooks cache."
	@find . -type d -name "*.ipynb_checkpoints" -exec rm -rf {} +
	@echo "Cleaning up pytest cache & test artifacts."
	@find . -type d -name '*.pytest_cache' -exec rm -rf {} + -o -type f -name '*.pytest_cache' -exec rm -rf {} +
	@find . -type f -name 'fc.*' -delete -o -type f -name 'fort.*' -delete
	@find . -type f -name 'checkpoint_restart.*' -delete -o -type f -name 'internal_mag_pot.*' -delete
	@echo "Cleaning up mypy cache."
	@find . -type d -name "*.mypy_cache" -exec rm -rf {} +
	@echo "Cleaning up coverage reports."
	@find . -type f -name '.coverage*' -exec rm -rf {} + -o -type f -name 'coverage.xml' -delete
	@echo "All cleaned up!\n"

docker:
	@echo "Building $(P)simenv$(E) Docker image with $(D)PHD$(E) conda environment, with tag $(P)latest$(E)."
	@docker build -f ./docker/Dockerfile -t simenv .
	@docker tag simenv simenv:latest
	@echo "Done. You can run this with $(P)docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work simenv$(E)."

docs:
	@echo "Building static pages with $(D)Sphinx$(E)."
	@uv run python -m sphinx -v -b html docs doc_build -d doc_build

format:
	@echo "Formatting code in $(C)docs$(E), $(C)tests$(E) and $(C)pyhdtoolkit$(E)."
	@uvx isort docs && uvx black docs
	@uvx isort tests && uvx black tests
	@uvx isort pyhdtoolkit && uvx black pyhdtoolkit
	@echo "Formatting code to PEP8 with $(P)isort$(E) and $(P)Black$(E) for $(C)examples$(E) folder."
	@uvx isort examples && uvx black -l 95 examples

install:
	@echo "Installing (editable) the package in the current environment."
	@uv pip install --editable .

lines:
	@echo "Counting lines of code with $(P)tokei$(E)."
	@tokei .

lint:
	@echo "Linting code with $(P)Ruff$(E)."
	@uvx ruff check pyhdtoolkit

tests:
	@uv run python -m pytest -n auto -v

# Catch-all unknow targets without returning an error. This is a POSIX-compliant syntax.
.DEFAULT:
	@echo "Make caught an invalid target."
	@echo "See help output below for available targets."
	@echo ""
	@make help
