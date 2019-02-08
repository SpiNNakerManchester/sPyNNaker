from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spynnaker.pyNN.models.defaults import (
    defaults, default_parameters, default_initial_values)


def test_nothing():
    @defaults
    class _AClass(object):
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert(_AClass.default_parameters == {
        "param_1": 1, "param_2": 2, "param_3": 3})
    assert(_AClass.default_initial_values == {})


def test_parameters():
    @defaults
    class _AClass(object):

        @default_parameters({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert(_AClass.default_parameters == {"param_1": 1})
    assert(_AClass.default_initial_values == {"param_2": 2, "param_3": 3})


def test_state_variables():
    @defaults
    class _AClass(object):

        @default_initial_values({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert(_AClass.default_initial_values == {"param_1": 1})
    assert(_AClass.default_parameters == {"param_2": 2, "param_3": 3})


def test_both():
    @defaults
    class _AClass(object):

        @default_parameters({"param_1"})
        @default_initial_values({"param_2"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert(_AClass.default_parameters == {"param_1": 1})
    assert(_AClass.default_initial_values == {"param_2": 2})


def test_abstract():
    @add_metaclass(AbstractBase)
    class BaseClass(object):

        @abstractproperty
        @staticmethod
        def default_parameters():
            pass

        @abstractproperty
        @staticmethod
        def default_initial_values():
            pass

    @defaults
    class _AClass(BaseClass):

        default_parameters = None
        default_initial_values = None

        def __init__(self, param="test"):
            pass

    assert(_AClass.default_parameters == {"param": "test"})
    assert(_AClass.default_initial_values == {})
    _AClass()
