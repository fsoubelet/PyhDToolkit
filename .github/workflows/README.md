# Continuous Integration Workflows

This package implements different workflows for CI.
They are organised as follows.

## Documentation

The `documentation` workflow builds the documentation.
It runs on `ubuntu-latest` and the latest supported Python version.
If the workflow is run from `master` it pushes the successfully build documentation to the `gh-pages` branch.
If run from a `pull_request` the documentation is uploaded as an artifact to allow manual checks.

## Testing Suite

Tests are ensured in the `tests` workflow.
Tests run on a matrix of all supported operating systems and all currently supported Python versions.

## Test Coverage

Test coverage is calculated in the `coverage` workflow.
It runs on `ubuntu-latest` and our latest supported Python version, and reports the coverage results of the test suite to `Codecov`.

## Regular Testing

A `cron` workflow triggers every Saturday at 12:00 (UTC time) and runs the full testing suite, on all supported operating systems and supported Python versions.
It is very similar to the normal Testing Suite, but in addition also runs on `Python 3.x` so that newly released Python versions that would break tests are automatically included.

## Publishing

Publishing to `PyPI` is done through the `publish` workflow, which triggers anytime a `release` is made on GitHub.
It runs on `ubuntu-latest` and the latest supported Python version.

It builds the package (source distribution and `wheel`), checks the created artifacts, and pushes to `PyPI` if checks are successful.
No matrix is needed for this build as `pyhdtoolkit` is a pure python package and generates `*-py3-none-any.whl` wheels.
