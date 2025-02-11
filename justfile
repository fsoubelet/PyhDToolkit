# Copyright 2019 Felix Soubelet <felix.soubelet@cern.ch>
# MIT License

# ----- Dev Targets ----- #

# build the package sdist and wheel
build:
	rm -rf dist
	uv build

# clean up build artifacts, documentation pages and other temporary files
clean:
	rm -rf doc_build
	rm -rf plot_directive
	rm -rf docs/gallery
	rm -rf docs/gen_modules
	rm -rf build
	rm -rf dist
	rm -rf pyhdtoolkit.egg-info
	rm -rf .eggs
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	find . -type d -name "*.ipynb_checkpoints" -exec rm -rf {} +
	find . -type d -name '*.pytest_cache' -exec rm -rf {} + -o -type f -name '*.pytest_cache' -exec rm -rf {} +
	find . -type f -name 'fc.*' -delete -o -type f -name 'fort.*' -delete
	find . -type f -name 'checkpoint_restart.*' -delete -o -type f -name 'internal_mag_pot.*' -delete
	find . -type d -name "*.mypy_cache" -exec rm -rf {} +
	find . -type f -name '.coverage*' -exec rm -rf {} + -o -type f -name 'coverage.xml' -delete

# build a docker image with a working pyhdtoolkit environment
docker:
	docker build -f ./docker/Dockerfile -t simenv .
	docker tag simenv simenv:latest

# build the documentation pages
docs:
	uv run python -m sphinx -v -b html docs doc_build -d doc_build

# run the isort and black tools on the codebase
format:
  uvx isort docs && uvx black docs
  uvx isort tests && uvx black tests
  uvx isort pyhdtoolkit && uvx black pyhdtoolkit
  uvx isort examples && uvx black -l 95 examples/*.py

# install (editable) the package in the current environment
install:
	uv pip install --editable .

# count the lines of code with tokei
lines:
	tokei .

# run the Ruff linter on the codebase
lint:
	uvx ruff check pyhdtoolkit

# run the test suite (parallelized) with pytest
tests:
	uv run python -m pytest -n auto -v
