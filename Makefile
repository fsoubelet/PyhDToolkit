.PHONY : black clean_pyc install isort tests

all: install

black: isort
	black -v -l 120 .

clean_pyc:
	-find . -name '*.py[co]' -exec rm {} \;

install: tests
	pip install .

isort:
	isort -rc .

tests: isort black clean_pyc
	pytest tests