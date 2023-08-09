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
    defaults, default_parameters, default_initial_values)
from testfixtures.logcapture import LogCapture
import re
# pylint: disable=no-member


def test_nothing():
    unittest_setup()

    @defaults
    class _AClass(object):
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert (_AClass.default_parameters == {
        "param_1": 1, "param_2": 2, "param_3": 3})
    assert _AClass.default_initial_values == {}


def test_parameters():
    unittest_setup()

    @defaults
    class _AClass(object):

        @default_parameters({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert _AClass.default_parameters == {"param_1": 1}
    assert _AClass.default_initial_values == {"param_2": 2, "param_3": 3}


def test_state_variables():
    unittest_setup()

    @defaults
    class _AClass(object):

        @default_initial_values({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert _AClass.default_initial_values == {"param_1": 1}
    assert _AClass.default_parameters == {"param_2": 2, "param_3": 3}


def test_both():
    unittest_setup()

    @defaults
    class _AClass(object):

        @default_parameters({"param_1"})
        @default_initial_values({"param_2"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass

    @defaults
    class _AnotherClass(object):

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

    @defaults
    class _AClass(BaseClass):

        default_parameters = None
        default_initial_values = None

        def __init__(self, param="test"):
            pass

    assert _AClass.default_parameters == {"param": "test"}
    assert _AClass.default_initial_values == {}
    _AClass()


def test_setting_state_variables():
    unittest_setup()

    @defaults
    class _AClass(object):

        @default_parameters({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass

    @defaults
    class _AnotherClass(object):

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
