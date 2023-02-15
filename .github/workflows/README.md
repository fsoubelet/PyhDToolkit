# Continuous Integration Workflows

This package implements different workflows for CI.
They are organised as follows.

### Documentation

The `documentation` workflow triggers on any push to master, builds the documentation and pushes it to the `gh-pages` branch (if the build is successful).
It runs on `ubuntu-latest` and `Python 3.9`.

### Testing Suite

Tests are ensured in the `tests` workflow, which triggers on all pushes.
Tests run on a matrix of all GitHub Actions supported operating systems for all supported Python versions (currently `3.8+`).

### Test Coverage

Test coverage is calculated in the `coverage` wokflow, which triggers on pushes to `master` and any push to a `pull request`.
It runs on `ubuntu-latest` and `Python 3.9`, and reports the coverage results of the test suite to `Codecov`.

### Regular Testing

A `cron` workflow triggers every Saturday at 12:00 (UTC time) and runs the full testing suite, on all GitHub Actions supported operating systems for all supported Python versions (currently `3.8+`).
It also runs on `Python 3.x` so that newly released Python versions that would break tests are automatically detected and reported.

### Publishing

Publishing to `PyPI` is done through the `publish` workflow, which triggers anytime a `release` is made of the GitHub repository and runs on `ubuntu-latest` and `Python 3.9`.
It builds a source distribution (`tar.gz`) and a `wheel` of the package, and pushes to `PyPI` if the builds are successful.
No matrix is needed for this build as `pyhdtoolkit` is a pure python package and generates `*-py3-none-any.whl` wheels.