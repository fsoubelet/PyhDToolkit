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
# Y = \033[33m  # yellow

.PHONY : help build clean docker docs format install lines lint typing alltests quicktests slowtests

all: install

help:
	@echo "Please use 'make $(R)<target>$(E)' where $(R)<target>$(E) is one of:"
	@echo "  $(R) build $(E)  \t  to build wheel and source distribution with $(P)Hatch$(E)."
	@echo "  $(R) clean $(E)  \t  to recursively remove build, run and bitecode files/dirs."
	@echo "  $(R) docker $(E)  \t  to build a $(P)Docker$(E) container image replicating said environment (and other goodies)."
	@echo "  $(R) docs $(E)  \t  to build the documentation for the package with $(P)Sphinx$(E)."
	@echo "  $(R) format $(E)  \t  to recursively apply PEP8 formatting through the $(P)Black$(E) and $(P)isort$(E) cli tools."
	@echo "  $(R) install $(E)  \t  to $(C)pip install$(E) this package into the current environment."
	@echo "  $(R) lines $(E)  \t  to count lines of code with the $(P)tokei$(E) tool."
	@echo "  $(R) lint $(E)  \t  to lint the code though $(P)Pylint$(E)."
	@echo "  $(R) typing $(E)  \t  to run type checking on the codebase with $(P)MyPy$(E)."
	@echo "  $(R) alltests $(E)  \t  to run the full test suite with $(P)pytest$(E)."
	@echo "  $(R) quicktests $(E) \t  to run tests not involving $(D)pyhdtoolkit.cpymadtools$(E) with $(P)Pytest$(E)."
	@echo "  $(R) slowtests $(E)  \t  to run tests involving $(D)pyhdtoolkit.cpymadtools$(E) with $(P)Pytest$(E)."


# ----- Dev Tools Targets ----- #

build:
	@echo "Re-building wheel and dist"
	@rm -rf dist
	@hatch build --clean
	@echo "Created build is located in the $(C)dist$(E) folder."

clean:
	@echo "Cleaning up documentation pages."
	@rm -rf doc_build
	@rm -rf plot_directive
	@echo "Cleaning up sphinx-gallery build artifacts."
	@rm -rf docs/gallery
	@rm -rf docs/gen_modules
	@echo "Cleaning up distutils remains."
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
	@python -m sphinx -v -b html docs doc_build -d doc_build

format:
	@echo "Formatting code to PEP8 with $(P)isort$(E) and $(P)Black$(E) for $(C)docs$(E), $(C)pyhdtoolkit$(E) and $(C)tests$(E) folders. Max line length is 120 characters."
	@python -m isort . && black .
	@echo "Formatting code to PEP8 with $(P)isort$(E) and $(P)Black$(E) for $(C)examples$(E) folder. Max line length is 95 characters."
	@python -m isort examples && black -l 95 examples

install: format clean
	@echo "Installing with $(D)pip$(E) in the current environment."
	@python -m pip install . -v

lines: format
	@tokei .

lint: format
	@echo "Linting code with $(P)Pylint$(E)."
	@python -m pylint pyhdtoolkit/

typing: format
	@echo "Checking code typing with $(P)mypy$(E)."
	@python -m mypy pyhdtoolkit
	@make clean


# ----- Tests Targets ----- #

quicktests:  # all tests not involving pyhdtoolkit.cpymadtools
	@python -m pytest -k "not test_cpymadtools" -n auto -v

slowtests:  # all tests for pyhdtoolkit.cpymadtools
	@python -m pytest -k "test_cpymadtools" -n auto -v

alltests:
	@python -m pytest -n auto -v

# Catch-all unknow targets without returning an error. This is a POSIX-compliant syntax.
.DEFAULT:
	@echo "Make caught an invalid target! See help output below for available targets."
	@make help
