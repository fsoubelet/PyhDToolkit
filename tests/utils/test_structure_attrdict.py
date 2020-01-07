import pytest

from pyhdtoolkit.utils.structures import AttrDict


def test_attrdict_default_none():
    attr_dict = AttrDict()
    assert attr_dict == {}


def test_dotdict_set_attribute():
    attr_dict = AttrDict()
    attr_dict.a = 1
    assert attr_dict["a"] == 1


def test_dotdict_access_attribute():
    attr_dict = AttrDict()
    attr_dict["a"] = 1
    assert attr_dict.a == 1


def test_update_attrdict():
    attr_dict = AttrDict()
    attr_dict.a = 1
    attr_dict.update({"b": 2})
    assert attr_dict == {"a": 1, "b": 2}


def test_attrdict_attribute_error():
    attr_dict = AttrDict()
    with pytest.raises(AttributeError):
        assert attr_dict.foo


def test_attrdict_key_error():
    attr_dict = AttrDict()
    with pytest.raises(KeyError):
        assert attr_dict["foo"]


def test_attrdict_del_attribute():
    attr_dict = AttrDict({"a": 1})
    del attr_dict.a
    with pytest.raises(KeyError):
        assert attr_dict["a"]
