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
