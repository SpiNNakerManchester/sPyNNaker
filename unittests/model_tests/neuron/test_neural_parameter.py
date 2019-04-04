import os
import struct
from six.moves import xrange
from spinn_storage_handlers import FileDataWriter
from data_specification.enums import DataType
from data_specification import DataSpecificationGenerator
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.models.neural_properties.neural_parameter import (
    _Range_Iterator, _Get_Iterator, _SingleValue_Iterator)
from spynnaker.pyNN.utilities.ranged import SpynnakerRangedList
from unittests.mocks import MockSimulator


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


def test_range_list():
    MockSimulator().setup()

    spec_writer = FileDataWriter("test.dat")
    spec = DataSpecificationGenerator(spec_writer, None)
    try:
        value = SpynnakerRangedList(size=10, value=1.0, key="test")
        value[2:4] = 2.0
        param = NeuronParameter(value, DataType.S1615)
        iterator = param.iterator_by_slice(0, 5, spec)
        values = _iterate_parameter_values(iterator, DataType.S1615)
        assert list(value[0:5]) == values
        assert isinstance(iterator, _Range_Iterator)
    finally:
        spec.end_specification()
        os.remove("test.dat")


def _generator(size):
    for i in xrange(size):
        yield i


def test_range_list_as_list():
    MockSimulator.setup()

    spec_writer = FileDataWriter("test.dat")
    spec = DataSpecificationGenerator(spec_writer, None)
    try:
        value = SpynnakerRangedList(size=10, value=_generator(10), key="test")
        param = NeuronParameter(value, DataType.S1615)
        iterator = param.iterator_by_slice(0, 5, spec)
        values = _iterate_parameter_values(iterator, DataType.S1615)
        assert list(value[0:5]) == values
        assert isinstance(iterator, _Range_Iterator)
    finally:
        spec.end_specification()
        os.remove("test.dat")


def test_real_list():
    MockSimulator.setup()

    spec_writer = FileDataWriter("test.dat")
    spec = DataSpecificationGenerator(spec_writer, None)
    try:
        value = range(10)
        param = NeuronParameter(value, DataType.S1615)
        iterator = param.iterator_by_slice(0, 5, spec)
        values = _iterate_parameter_values(iterator, DataType.S1615)
        assert list(value[0:5]) == values
        assert isinstance(iterator, _Get_Iterator)
    finally:
        spec.end_specification()
        os.remove("test.dat")


def test_single_value():
    MockSimulator.setup()

    spec_writer = FileDataWriter("test.dat")
    spec = DataSpecificationGenerator(spec_writer, None)
    try:
        value = 1.0
        param = NeuronParameter(value, DataType.S1615)
        iterator = param.iterator_by_slice(0, 5, spec)
        values = _iterate_parameter_values(iterator, DataType.S1615)
        assert [value] * 5 == values
        assert isinstance(iterator, _SingleValue_Iterator)
    finally:
        spec.end_specification()
        os.remove("test.dat")
