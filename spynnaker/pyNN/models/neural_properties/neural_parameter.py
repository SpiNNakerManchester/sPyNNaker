from spinn_utilities.ranged.abstract_list import AbstractList


class _List_Iterator(object):

    def __init__(self, iterator, datatype):
        self._iterator = iterator
        self._datatype = datatype

    def next(self):
        return (self._iterator.next(), self._datatype)


class _Get_Iterator(object):

    def __init__(self, a_list, datatype, slice_start, slice_stop):
        self._a_list = a_list
        self._datatype = datatype
        self._index = slice_start
        self._slice_stop = slice_stop

    def next(self):
        if self._index >= self._slice_stop:
            raise StopIteration
        result = self._a_list[self._index]
        self._index += 1
        return (result, self._datatype)


class NeuronParameter(object):
    def __init__(self, value, datatype):
        self._value = value
        self._datatype = datatype

    def get_value(self):
        return self._value

    def get_dataspec_datatype(self):
        return self._datatype

    def iterator_by_slice(self, slice_start, slice_stop):
        if isinstance(self._value, AbstractList):
            return _List_Iterator(self._value.iter_by_slice(
                slice_start=slice_start, slice_stop=slice_stop),
                self._datatype)
        return _Get_Iterator(
            self._value, self._datatype, slice_start, slice_stop)
