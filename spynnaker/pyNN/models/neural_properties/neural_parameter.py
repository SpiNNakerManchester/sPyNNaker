# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.ranged.abstract_list import AbstractList
from data_specification.enums import DataType, Commands
from data_specification.exceptions import UnknownTypeException


class _Range_Iterator(object):
    """ Iterator over a :py:class:`~spinn_utilities.ranged.RangedList` \
        which is range based
    """
    __slots__ = [
        "__cmd_pair",
        "__datatype",
        "__index",
        "__iterator",
        "__spec",
        "__stop_range"]

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        :param ~spinn_utilities.ranged.AbstractList value:
            The abstract list holding the data
        :param ~data_specification.enums.DataType datatype:
            The type of each element of data
        :param int slice_start: Inclusive start of the range
        :param int slice_stop: Exclusive end of the range
        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
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


class _Get_Iterator(object):
    """ Iterator over a standard collection that supports ``__getitem__``
    """
    __slots__ = [
        "__datatype",
        "__index",
        "__slice_stop",
        "__spec",
        "__value"]

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        :param value: The list holding the data
        :type value: list(int) or list(float) or list(bool) or ~numpy.ndarray
        :param ~data_specification.enums.DataType datatype:
            The type of each element of data
        :param int slice_start: Inclusive start of the range
        :param int slice_stop: Exclusive end of the range
        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
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


class _SingleValue_Iterator(object):
    """ Iterator that repeats the single values the required number of times.

    Allows a single Value parameter to be treated the same as parameters with
    len. Caches `cmd_word_list` and `cmd_string` so they are only created once.
    """
    __slots__ = [
        "__cmd_pair",
        "__index",
        "__stop"]

    def __init__(self, value, datatype, slice_start, slice_stop, spec):
        """
        :param value: The simple value that is the data for each element
        :type value: int or float or bool
        :param ~data_specification.enums.DataType datatype:
            The type of each element of data
        :param int slice_start: Inclusive start of the range
        :param int slice_stop: Exclusive end of the range
        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
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
    """ A settable parameter of a neuron model.
    """

    __slots__ = [
        "__data_type",
        "__value"]

    def __init__(self, value, data_type):
        """
        :param value: what the value of the parameter is; if a list or array,
            potentially provides a different value for each neuron
        :type value: int or float or bool or list(int) or list(float) or
            list(bool) or ~numpy.ndarray or
            ~spinn_utilities.ranged.AbstractList
        :param ~data_specification.enums.DataType data_type:
            The serialization type of the parameter in the neuron model.
        """
        self.__value = value
        if data_type not in DataType:
            raise UnknownTypeException(
                data_type.value, Commands.WRITE.name)  # @UndefinedVariable
        self.__data_type = data_type

    def get_value(self):
        """ What the value of the parameter is; if a list or array,\
            potentially provides a different value for each neuron.

        :rtype: int or float or bool or list(int) or list(float) or
            list(bool) or ~numpy.ndarray or
            ~spinn_utilities.ranged.AbstractList
        """
        return self.__value

    def get_dataspec_datatype(self):
        """ Get the serialization type of the parameter in the neuron model.

        :rtype: ~data_specification.enums.DataType
        """
        return self.__data_type

    def iterator_by_slice(self, slice_start, slice_stop, spec):
        """ Creates an iterator over the commands to use to write the\
            parameter to the data specification being generated.

        :param int slice_start: Inclusive start of the range
        :param int slice_stop: Exclusive end of the range
        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to eventually write to.
            (Note that this does not actually do the write).
        :return: Iterator that produces a command to write to the
            specification for each element in the slice.
        :rtype: iterator(tuple(bytearray, str))
        """
        if isinstance(self.__value, AbstractList):
            return _Range_Iterator(
                self.__value, self.__data_type, slice_start, slice_stop, spec)
        if hasattr(self.__value, '__getitem__'):
            return _Get_Iterator(
                self.__value, self.__data_type, slice_start, slice_stop, spec)
        return _SingleValue_Iterator(
            self.__value, self.__data_type, slice_start, slice_stop, spec)
