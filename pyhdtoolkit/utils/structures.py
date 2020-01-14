"""
Created on 2019.11.06
:author: Felix Soubelet (felix.soubelet@cern.ch)

Some tidbits structures for Python programming.
"""


class AttrDict(dict):
    """
    A dict with dot notation.
    Idea and code from:
        http://stackoverflow.com/a/23689767,
        http://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named/
        http://stackoverflow.com/questions/2390827/how-to-properly-subclass-dict-and-override-get-set
    Keys can also be declared with dot notation.
    Example:
        d = AttrDict()
        d["a"] = 1
        d.b = 2
        d -> {'a': 1, 'b': 2}
    If you want this functionality to be nested, you can declare
    nested_attr_dict = lambda
    """

    def __init__(self, *a, **kw):
        dict.__init__(self)
        self.update(*a, **kw)
        self.__dict__ = self

    def __setattr__(self, key, value):
        if key in dict.__dict__:
            raise AttributeError("This key is reserved for the dict methods.")
        dict.__setattr__(self, key, value)

    def __setitem__(self, key, value):
        if key in dict.__dict__:
            raise AttributeError("This key is reserved for the dict methods.")
        dict.__setitem__(self, key, value)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
