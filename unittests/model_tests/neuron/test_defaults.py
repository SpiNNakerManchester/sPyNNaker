# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.defaults import (
    AbstractProvidesDefaults, default_parameters, default_initial_values)
from testfixtures import LogCapture  # type: ignore[import]
import re
# pylint: disable=no-member


def test_nothing():
    unittest_setup()

    class _AClass(AbstractProvidesDefaults):
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert (_AClass.default_parameters == {
        "param_1": 1, "param_2": 2, "param_3": 3})
    assert _AClass.default_initial_values == {}


def test_parameters():
    unittest_setup()

    class _AClass(AbstractProvidesDefaults):

        @default_parameters({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert _AClass.default_parameters == {"param_1": 1}
    assert _AClass.default_initial_values == {"param_2": 2, "param_3": 3}


def test_state_variables():
    unittest_setup()

    class _AClass(AbstractProvidesDefaults):

        @default_initial_values({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert _AClass.default_initial_values == {"param_1": 1}
    assert _AClass.default_parameters == {"param_2": 2, "param_3": 3}


def test_both():
    unittest_setup()

    class _AClass(AbstractProvidesDefaults):

        @default_parameters({"param_1"})
        @default_initial_values({"param_2"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass

    class _AnotherClass(AbstractProvidesDefaults):

        @default_initial_values({"param_1"})
        @default_parameters({"param_2"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert _AClass.default_parameters == {"param_1": 1}
    assert _AClass.default_initial_values == {"param_2": 2}
    assert _AnotherClass.default_parameters == {"param_2": 2}
    assert _AnotherClass.default_initial_values == {"param_1": 1}


def test_abstract():
    unittest_setup()

    class BaseClass(object, metaclass=AbstractBase):

        @property
        @staticmethod
        @abstractmethod
        def default_parameters():
            pass

        @property
        @staticmethod
        @abstractmethod
        def default_initial_values():
            pass

    #@defaults
    #class _AClass(BaseClass):
    class _AClass(AbstractProvidesDefaults):

        default_parameters = None
        default_initial_values = None

        def __init__(self, param="test"):
            pass

    # this no longer works
    #assert _AClass.default_parameters == {"param": "test"}
    #assert _AClass.default_initial_values == {}
    _AClass()


def test_setting_state_variables():
    unittest_setup()

    class _AClass(AbstractProvidesDefaults):

        @default_parameters({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass

    class _AnotherClass(AbstractProvidesDefaults):

        @default_initial_values({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass

    with LogCapture() as lc:
        _AClass(param_1=1)
        _check_warnings(lc, [], ["param_1", "param_2", "param_3"])
    with LogCapture() as lc:
        _AClass(param_2=2)
        _check_warnings(lc, ["param_2"], ["param_1", "param_3"])
    with LogCapture() as lc:
        _AClass(param_3=3)
        _check_warnings(lc, ["param_3"], ["param_1", "param_2"])

    with LogCapture() as lc:
        _AnotherClass(param_1=1)
        _check_warnings(lc, ["param_1"], ["param_2", "param_3"])
    with LogCapture() as lc:
        _AnotherClass(param_2=2)
        _check_warnings(lc, [], ["param_1", "param_2", "param_3"])
    with LogCapture() as lc:
        _check_warnings(lc, [], ["param_1", "param_2", "param_3"])
        _AnotherClass(param_3=3)

from spinn_utilities.classproperty import classproperty
from typing import (
    Any, Callable, cast, Dict, FrozenSet, Optional, Mapping, Sequence,
    Tuple, TYPE_CHECKING)
from spynnaker.pyNN.models.defaults import get_map_from_init
import inspect
import logging
from types import MappingProxyType

class AbstractDefaults(object):

    #def __init__(self,*args, **kwargs):
    #        print("arges", args, "kwargs", kwargs)

    @staticmethod
    def __get_init_params_and_svars(the_cls: type) -> Tuple[
        Callable, Optional[FrozenSet[str]], Optional[FrozenSet[str]]]:
        init = getattr(the_cls, "__init__")
        while hasattr(init, "_method"):
            init = getattr(init, "_method")
        params = None
        if hasattr(init, "_parameters"):
            params = getattr(init, "_parameters")
        svars = None
        if hasattr(init, "_state_variables"):
            svars = getattr(init, "_state_variables")
        return init, params, svars

    @classproperty
    def default_parameters(  # pylint: disable=no-self-argument
            cls) -> Mapping[str, Any]:
        """
        Get the default values for the parameters of the model.

        :rtype: dict(str, Any)
        """
        print("default_parameters")
        init, params, svars = cls.__get_init_params_and_svars(
            cast(type, cls))
        cls.default_parameters = get_map_from_init(
            init, skip=svars, include=params)
        return cls.default_parameters

    @classproperty
    def default_initial_values(  # pylint: disable=no-self-argument
            cls) -> Mapping[str, Any]:
        """
        Get the default initial values for the state variables of the model.

        :rtype: dict(str, Any)
        """
        print("default_initial_values")
        init, params, svars = cls.__get_init_params_and_svars(
            cast(type, cls))
        if params is None and svars is None:
            return {}
        cls.default_initial_values = get_map_from_init(init, skip=params, include=svars)
        return cls.default_initial_values
#class BClass(AbstractDefaults):
class BClass(AbstractProvidesDefaults):

    @default_parameters({"param_1"})
    @default_initial_values({"param_2"})
    def __init__(self, param_1=1, param_2=2, param_3=3):
        pass


def test_check_weird():
    unittest_setup()

    bc = BClass()
    print(1)
    a = BClass.default_parameters
    b = BClass.default_initial_values
    print(a, b)
    print(2)
    a1 = bc.default_parameters
    b1 = bc.default_initial_values
    print(a1, b1)

def _check_warnings(lc, expected, not_expected):
    line_matcher = re.compile(
        "Formal PyNN specifies that (.*) should be set using initial_values"
        " not cell_params")
    warning_variables = set()
    for record in lc.records:
        match = line_matcher.match(str(record.msg))
        if record.levelname == "WARNING" and match:
            warning_variables.add(match.group(1))

    print("Found warnings for variables {}".format(warning_variables))
    assert all(item in warning_variables for item in expected)
    assert all(item not in warning_variables for item in not_expected)
