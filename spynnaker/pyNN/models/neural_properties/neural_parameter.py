from spinn_utilities.ranged.abstract_list import AbstractList
from data_specification.enums import DataType, Commands
from data_specification import exceptions


class _List_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        Iterator over a RangedList which is list based

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        self._iterator = value.iter_by_slice(
                slice_start=slice_start, slice_stop=slice_stop)
        self._datatype = datatype
        self._spec = spec

    def next(self):
        (cmd_word_list, cmd_string) = self._spec.create_cmd(
            data=self._iterator.next(), data_type=self._datatype)
        return (cmd_word_list, cmd_string)


class _Range_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        Iterator over a RangedList which is range based

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        self._iterator = value.iter_ranges_by_slice(slice_start, slice_stop)
        # We want the inner iterator to throw a Stopiteration the first time
        self._index = 0
        self.stop_range = 0
        self._datatype = datatype
        self._spec = spec

    def next(self):
        self._index += 1
        if self._index < self.stop_range:
            return (self._cmd_word_list, self._cmd_string)
        else:
            (self._index, self.stop_range, current) = \
                self._iterator.next()
            (self._cmd_word_list, self._cmd_string) = self._spec.create_cmd(
                data=current, data_type=self._datatype)
            return (self._cmd_word_list, self._cmd_string)


class _Get_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        Iterator over a standard collection that supports __get_item__

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        self._value = value
        self._datatype = datatype
        self._index = slice_start - 1
        self._slice_stop = slice_stop
        self._spec = spec

    def next(self):
        self._index += 1
        if self._index >= self._slice_stop:
            raise StopIteration
        (cmd_word_list, cmd_string) = self._spec.create_cmd(
            data=self._value[self._index], data_type=self._datatype)
        return (cmd_word_list, cmd_string)


class _SingleValue_Iterator(object):

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        Iterator that repeats the single values the required number of times

        Allows a single Value parameter to be treated the same as parameters
        with len
        Caches cmd_word_list and cmd_string so they are only created once.

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        (self._cmd_word_list, self._cmd_string) = spec.create_cmd(
            data=value, data_type=datatype)
        # We want the inner iterator to throw a Stopiteration the first time
        self._index = slice_start
        self._stop = slice_stop

    def next(self):
        self._index += 1
        if self._index >= self._stop:
            raise StopIteration
        return (self._cmd_word_list, self._cmd_string)


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

    def iterator_by_slice(self, slice_start, slice_stop, spec):
        """
        Creates an Iterator
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        :return: Iterator
        """
        if isinstance(self._value, AbstractList):
            if self._value.range_based:
                return _Range_Iterator(
                    self._value, self._data_type, slice_start, slice_stop,
                    spec)
            else:
                return _List_Iterator(
                    self._value, self._data_type, slice_start, slice_stop,
                    spec)
        if hasattr(self._value, '__getitem__'):
            return _Get_Iterator(
                self._value, self._data_type, slice_start, slice_stop, spec)
        return _SingleValue_Iterator(
            self._value, self._data_type, slice_start, slice_stop, spec)