from spinn_utilities.ranged.abstract_list import AbstractList


class NeuronParameter(object):
    def __init__(self, value, datatype):
        self._value = value
        self._datatype = datatype

    def get_value(self):
        return self._value

    def get_dataspec_datatype(self):
        return self._datatype

    def start_iterator_by_slice(self, slice_start, slice_stop):
        if isinstance(self._value, AbstractList):
            self._iterator = self._value.iter_by_slice(
                slice_start=slice_start, slice_stop=slice_stop)
            return True
        return False

    def next(self):
        return self._iterator.next()
