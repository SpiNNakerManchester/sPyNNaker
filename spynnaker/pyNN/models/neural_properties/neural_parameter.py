from spinn_utilities.ranged.abstract_list import AbstractList
from data_specification.enums import DataType, Commands
from data_specification import constants, exceptions
import decimal
import struct


class _List_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop):
        self._iterator = value.iter_by_slice(
                slice_start=slice_start, slice_stop=slice_stop)
        self._datatype = datatype

    def next(self):
        return (self._iterator.next(), self._datatype)


class _Range_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop):
        self._iterator = value.iter_ranges_by_slice(slice_start, slice_stop)
        # We want the inner iterator to throw a Stopiteration the first time
        self._index = 0
        self.stop_range = 0
        self._datatype = datatype

    def next(self):
        self._index += 1
        if self._index < self.stop_range:
            return (self._current, self._datatype)
        else:
            (self._index, self.stop_range, self._current) = \
                self._iterator.next()
            return (self._current, self._datatype)


class _Get_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop):
        self._value = value
        self._datatype = datatype
        self._index = slice_start
        self._slice_stop = slice_stop

    def next(self):
        if self._index >= self._slice_stop:
            raise StopIteration
        result = self._value[self._index]
        self._index += 1
        return (result, self._datatype)


class NeuronParameter(object):
    def __init__(self, value, data_type):
        self._value = value
        if data_type not in DataType:
            raise exceptions.DataSpecificationUnknownTypeException(
                data_type.value, Commands.WRITE.name)  # @UndefinedVariable
        self._data_type = data_type

    def get_value(self):
        return self._value

    def get_dataspec_datatype(self):
        return self._data_type

    def iterator_by_slice(self, slice_start, slice_stop):
        if isinstance(self._value, AbstractList):
            if self._value.range_based:
                return _Range_Iterator(
                    self._value, self._data_type, slice_start, slice_stop)
            else:
                return _List_Iterator(
                    self._value, self._data_type, slice_start, slice_stop)
        return _Get_Iterator(
            self._value, self._data_type, slice_start, slice_stop)
