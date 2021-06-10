# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.abstract_base import AbstractBase, abstractproperty
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
    assert(_AClass.default_parameters == {
        "param_1": 1, "param_2": 2, "param_3": 3})
    assert(_AClass.default_initial_values == {})


def test_parameters():
    unittest_setup()
    @defaults
    class _AClass(object):

        @default_parameters({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert(_AClass.default_parameters == {"param_1": 1})
    assert(_AClass.default_initial_values == {"param_2": 2, "param_3": 3})


def test_state_variables():
    unittest_setup()
    @defaults
    class _AClass(object):

        @default_initial_values({"param_1"})
        def __init__(self, param_1=1, param_2=2, param_3=3):
            pass
    assert(_AClass.default_initial_values == {"param_1": 1})
    assert(_AClass.default_parameters == {"param_2": 2, "param_3": 3})


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
    assert(_AClass.default_parameters == {"param_1": 1})
    assert(_AClass.default_initial_values == {"param_2": 2})
    assert(_AnotherClass.default_parameters == {"param_2": 2})
    assert(_AnotherClass.default_initial_values == {"param_1": 1})


def test_abstract():
    unittest_setup()
    class BaseClass(object, metaclass=AbstractBase):

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
        match = line_matcher.match(record.getMessage())
        if record.levelname == "WARNING" and match:
            warning_variables.add(match.group(1))

    print("Found warnings for variables {}".format(warning_variables))
    assert(all(item in warning_variables for item in expected))
    assert(all(item not in warning_variables for item in not_expected))
