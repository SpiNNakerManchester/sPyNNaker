from spinn_utilities.ranged.abstract_list import AbstractList
from data_specification.enums import DataType, Commands
from data_specification.exceptions import UnknownTypeException
from six import Iterator


class _Range_Iterator(Iterator):
    __slots__ = [
        "_cmd_pair",
        "_datatype",
        "_index",
        "_iterator",
        "_spec",
        "_stop_range"]

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """ Iterator over a RangedList which is range based

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        # pylint: disable=too-many-arguments
        self._iterator = value.iter_ranges_by_slice(slice_start, slice_stop)

        # Initially the index will be out of range which will force the
        # iterator to be called, and set self._cmd_pair
        self._index = 0
        self._stop_range = 0
        self._datatype = datatype
        self._spec = spec
        self._cmd_pair = (None, None)

    def __next__(self):
        # We pre-update the index here as the first value in the range
        # was done at the last iteration, or else this is the first iteration
        # and we need to force the iterator to be called
        self._index += 1
        if self._index < self._stop_range:
            return self._cmd_pair
        (self._index, self._stop_range, current) = next(self._iterator)
        self._cmd_pair = self._spec.create_cmd(
            data=current, data_type=self._datatype)
        return self._cmd_pair


class _Get_Iterator(Iterator):
    __slots__ = [
        "_datatype",
        "_index",
        "_slice_stop",
        "_spec",
        "_value"]

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """ Iterator over a standard collection that supports __getitem__

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        # pylint: disable=too-many-arguments
        self._value = value
        self._datatype = datatype
        self._index = slice_start
        self._slice_stop = slice_stop
        self._spec = spec

    def __next__(self):
        if self._index >= self._slice_stop:
            raise StopIteration
        cmd_pair = self._spec.create_cmd(
            data=self._value[self._index], data_type=self._datatype)
        self._index += 1
        return cmd_pair


class _SingleValue_Iterator(Iterator):
    __slots__ = [
        "_cmd_pair",
        "_index",
        "_stop"]

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """ Iterator that repeats the single values the required number of\
            times.

        Allows a single Value parameter to be treated the same as parameters\
        with len. \
        Caches `cmd_word_list` and `cmd_string` so they are only created once.

        :param value: The list or Abstract list holding the data
        :param datatype: The type of each element of data
        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        """
        # pylint: disable=too-many-arguments
        self._cmd_pair = spec.create_cmd(data=value, data_type=datatype)
        self._index = slice_start
        self._stop = slice_stop

    def __next__(self):
        if self._index >= self._stop:
            raise StopIteration
        self._index += 1
        return self._cmd_pair


class NeuronParameter(object):
    __slots__ = [
        "_data_type",
        "_value"]

    def __init__(self, value, data_type):
        self._value = value
        if data_type not in DataType:
            raise UnknownTypeException(
                data_type.value, Commands.WRITE.name)  # @UndefinedVariable
        self._data_type = data_type

    def get_value(self):
        return self._value

    def get_dataspec_datatype(self):
        return self._data_type

    def iterator_by_slice(self, slice_start, slice_stop, spec):
        """ Creates an Iterator.

        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        :return: Iterator
        """
        if isinstance(self._value, AbstractList):
            return _Range_Iterator(
                self._value, self._data_type, slice_start, slice_stop, spec)
        if hasattr(self._value, '__getitem__'):
            return _Get_Iterator(
                self._value, self._data_type, slice_start, slice_stop, spec)
        return _SingleValue_Iterator(
            self._value, self._data_type, slice_start, slice_stop, spec)
