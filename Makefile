.PHONY : black clean_pyc install isort lines tests

all: install

black: isort
	black -v -l 120 .

clean_pyc:
	-find . -name '*.py[co]' -exec rm {} \;

install:
	pip install .

isort:
	isort -rc .

lines: black
	tokei .

tests: black clean_pyc
	pytest tests