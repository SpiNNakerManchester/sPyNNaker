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

import io
import os
import platform
import struct
import tempfile
from data_specification.enums import DataType
from data_specification import DataSpecificationGenerator
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.models.neural_properties.neural_parameter import (
    _Range_Iterator, _Get_Iterator, _SingleValue_Iterator)
from spynnaker.pyNN.utilities.ranged import SpynnakerRangedList


def _iterate_parameter_values(iterator, data_type):
    alist = list()
    while True:
        try:
            (cmd_word_list, _) = next(iterator)
            data = struct.unpack_from(
                "<I{}".format(data_type.struct_encoding),
                cmd_word_list)[1]
            alist.append(data / data_type.scale)
        except StopIteration:
            return alist


def run_spec_check(method):
    if platform.system() == "Windows":
        spec_writer = io.FileIO("test.dat", "wb")
        spec = DataSpecificationGenerator(spec_writer, None)
        try:
            method(spec)
        finally:
            spec.end_specification()
            os.remove("test.dat")
    else:
        with tempfile.NamedTemporaryFile() as temp:
            spec = DataSpecificationGenerator(io.FileIO(temp.name, "wb"), None)
            try:
                method(spec)
            finally:
                spec.end_specification()


def range_list(spec):
    value = SpynnakerRangedList(size=10, value=1.0, key="test")
    value[2:4] = 2.0
    param = NeuronParameter(value, DataType.S1615)
    iterator = param.iterator_by_slice(0, 5, spec)
    values = _iterate_parameter_values(iterator, DataType.S1615)
    assert list(value[0:5]) == values
    assert isinstance(iterator, _Range_Iterator)


def test_range_list():
    run_spec_check(range_list)


def _generator(size):
    yield from range(size)


def range_list_as_list(spec):
    value = SpynnakerRangedList(size=10, value=_generator(10), key="test")
    param = NeuronParameter(value, DataType.S1615)
    iterator = param.iterator_by_slice(0, 5, spec)
    values = _iterate_parameter_values(iterator, DataType.S1615)
    assert list(value[0:5]) == values
    assert isinstance(iterator, _Range_Iterator)


def test_range_list_as_list():
    run_spec_check(range_list_as_list)


def real_list(spec):
    value = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    param = NeuronParameter(value, DataType.S1615)
    iterator = param.iterator_by_slice(0, 5, spec)
    values = _iterate_parameter_values(iterator, DataType.S1615)
    assert list(value[0:5]) == values
    assert isinstance(iterator, _Get_Iterator)


def test_real_list():
    run_spec_check(real_list)


def single_value(spec):
    value = 1.0
    param = NeuronParameter(value, DataType.S1615)
    iterator = param.iterator_by_slice(0, 5, spec)
    values = _iterate_parameter_values(iterator, DataType.S1615)
    assert [value] * 5 == values
    assert isinstance(iterator, _SingleValue_Iterator)


def test_single_value():
    run_spec_check(single_value)
