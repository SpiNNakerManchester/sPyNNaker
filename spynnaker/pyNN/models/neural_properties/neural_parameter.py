from six import Iterator
from spinn_utilities.ranged.abstract_list import AbstractList
from data_specification.enums import DataType, Commands
from data_specification.exceptions import UnknownTypeException


class _Range_Iterator(Iterator):
    __slots__ = [
        "__cmd_pair",
        "__datatype",
        "__index",
        "__iterator",
        "__spec",
        "__stop_range"]

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
        self.__iterator = value.iter_ranges_by_slice(slice_start, slice_stop)

        # Initially the index will be out of range which will force the
        # iterator to be called, and set self._cmd_pair
        self.__index = 0
        self.__stop_range = 0
        self.__datatype = datatype
        self.__spec = spec
        self.__cmd_pair = (None, None)

    def __next__(self):
        # We pre-update the index here as the first value in the range
        # was done at the last iteration, or else this is the first iteration
        # and we need to force the iterator to be called
        self.__index += 1
        if self.__index < self.__stop_range:
            return self.__cmd_pair
        (self.__index, self.__stop_range, current) = next(self.__iterator)
        self.__cmd_pair = self.__spec.create_cmd(
            data=current, data_type=self.__datatype)
        return self.__cmd_pair


class _Get_Iterator(Iterator):
    __slots__ = [
        "__datatype",
        "__index",
        "__slice_stop",
        "__spec",
        "__value"]

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
        self.__value = value
        self.__datatype = datatype
        self.__index = slice_start
        self.__slice_stop = slice_stop
        self.__spec = spec

    def __next__(self):
        if self.__index >= self.__slice_stop:
            raise StopIteration
        cmd_pair = self.__spec.create_cmd(
            data=self.__value[self.__index], data_type=self.__datatype)
        self.__index += 1
        return cmd_pair


class _SingleValue_Iterator(Iterator):
    __slots__ = [
        "__cmd_pair",
        "__index",
        "__stop"]

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
        self.__cmd_pair = spec.create_cmd(data=value, data_type=datatype)
        self.__index = slice_start
        self.__stop = slice_stop

    def __next__(self):
        if self.__index >= self.__stop:
            raise StopIteration
        self.__index += 1
        return self.__cmd_pair


class NeuronParameter(object):
    __slots__ = [
        "__data_type",
        "__value"]

    def __init__(self, value, data_type):
        self.__value = value
        if data_type not in DataType:
            raise UnknownTypeException(
                data_type.value, Commands.WRITE.name)  # @UndefinedVariable
        self.__data_type = data_type

    def get_value(self):
        return self.__value

    def get_dataspec_datatype(self):
        return self.__data_type

    def iterator_by_slice(self, slice_start, slice_stop, spec):
        """ Creates an Iterator.

        :param slice_start: Inclusive start of the range
        :param slice_stop: Exclusive end of the range
        :param spec: The data specification to write to
        :type spec: DataSpecificationGenerator
        :return: Iterator
        """
        if isinstance(self.__value, AbstractList):
            return _Range_Iterator(
                self.__value, self.__data_type, slice_start, slice_stop, spec)
        if hasattr(self.__value, '__getitem__'):
            return _Get_Iterator(
                self.__value, self.__data_type, slice_start, slice_stop, spec)
        return _SingleValue_Iterator(
            self.__value, self.__data_type, slice_start, slice_stop, spec)
