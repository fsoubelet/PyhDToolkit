.PHONY : black clean_pyc install

all: install

clean_pyc:
	-find . -name '*.py[co]' -exec rm {} \;

black:
	black -v -l 120 .

install: clean_pyc
	pip install -e .
