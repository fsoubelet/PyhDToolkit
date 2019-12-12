.PHONY : black clean_pyc install tests

all: install

black:
	black -v -l 120 .

clean_pyc:
	-find . -name '*.py[co]' -exec rm {} \;

install: tests
	pip install .

tests: black clean_pyc
	pytest tests