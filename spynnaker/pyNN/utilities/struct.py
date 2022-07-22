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

import numpy
from enum import Enum
from pyNN.random import RandomDistribution
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities.utility_calls import convert_to
from spynnaker.pyNN.models.common.param_generator_data import (
    get_generator_type, param_generator_id, param_generator_params,
    type_has_generator)
from spinn_utilities.helpful_functions import is_singleton

REPEAT_PER_NEURON_FLAG = 0xFFFFFFFF


class StructRepeat(Enum):
    """ How a struct repeats, or not, in memory
    """
    #: Indicates a single global struct
    GLOBAL = 0

    #: Indicates a struct that repeats per neuron
    PER_NEURON = 1


class Struct(object):
    """ Represents a C code structure.
    """

    __slots__ = [
        "__fields",
        "__repeat_type",
        "__default_values"
    ]

    def __init__(self, fields, repeat_type=StructRepeat.PER_NEURON,
                 default_values=None):
        """
        :param fields:
            The types and names of the fields, ordered as they appear in the
            struct.
        :type fields: list(~data_specification.enums.DataType, str)
        :param StructRepeat repeat_type: How the structure repeats
        :param default_values:
            Dict of field name -> value to use when values doesn't contain the
            field
        :type default_values: dict(str->int or float) or None
        """
        self.__fields = fields
        self.__repeat_type = repeat_type
        self.__default_values = default_values or dict()

    @property
    def fields(self):
        """ The types and names of the fields, ordered as they appear in the
            struct.

        :rtype: list(~data_specification.enums.DataType, str)
        """
        return self.__fields

    @property
    def repeat_type(self):
        """ How the structure repeats

        :rtype: StructRepeat
        """
        return self.__repeat_type

    @property
    def numpy_dtype(self):
        """ The numpy data type of the struct

        :rtype: ~numpy.dtype
        """
        return numpy.dtype(
            [(name, numpy.dtype(data_type.struct_encoding))
             for data_type, name in self.__fields],
            align=True)

    def get_size_in_whole_words(self, array_size=1):
        """ Get the size of the struct in whole words in an array of given\
            size (default 1 item)

        :param int array_size: The number of elements in an array of structs
        :rtype: int
        """
        datatype = self.numpy_dtype
        size_in_bytes = array_size * datatype.itemsize
        return (size_in_bytes + (BYTES_PER_WORD - 1)) // BYTES_PER_WORD

    def get_data(self, values, offset=0, array_size=None):
        """ Get a numpy array of uint32 of data for the given values

        :param values: The values to fill in the data with
        :type values: dict(str->one of int, float or AbstractList)
        :param int offset:
            The offset into the values to start from
        :param array_size:
            The number of struct copies to generate, or None if this is a
            non-repeating struct.
        :type array_size: int or None
        :rtype: ~numpy.ndarray(dtype="uint32")
        """
        if array_size is None:
            if not self.__repeat_type == StructRepeat.GLOBAL:
                raise ValueError(
                    "Repeating structures must specify an array size")
            array_size = 1
        elif self.__repeat_type == StructRepeat.GLOBAL and array_size != 1:
            raise ValueError("Global Structures cannot repeat more than once")

        # Create an array to store values in
        data = numpy.zeros(array_size, dtype=self.numpy_dtype)

        if not self.__fields:
            return data.view("uint32")

        # Go through and get the values and put them in the array
        for data_type, name in self.__fields:
            if name in values:
                all_values = values[name]
                if is_singleton(all_values):
                    data[name] = convert_to(all_values, data_type)
                else:
                    for start, end, value in all_values.iter_ranges_by_slice(
                            offset, offset + array_size):
                        # Get the values and convert to the correct data type
                        if isinstance(value, RandomDistribution):
                            r_vals = value.next(end - start)
                            data_value = [
                                convert_to(v, data_type) for v in r_vals]
                        else:
                            data_value = convert_to(value, data_type)
                        data[name][start - offset:end - offset] = data_value
            else:
                value = self.__default_values[name]
                data_value = convert_to(value, data_type)
                data[name] = data_value

        # Pad to whole number of uint32s
        overflow = (array_size * self.numpy_dtype.itemsize) % BYTES_PER_WORD
        if overflow != 0:
            data = numpy.pad(
                data.view("uint8"), (0, BYTES_PER_WORD - overflow), "constant")

        return data.view("uint32")

    def get_generator_data(self, values, offset=0, array_size=None):
        """ Get a numpy array of uint32 of data to generate the given values

        :param ~dict-like values:
            The values to fill in the data with
        :param int offset:
            The offset into the values to start from.  This is ignored for a
            non-repeating struct, or one where array_size is None.
        :param array_size:
            The number of struct copies to generate, or None if this is a
            non-repeating struct, or a struct where the same value will repeat
            for all entries regardless of how many.  In this latter case, the
            value from values (or default_values from the initialiser) must
            be a single value for all entries.
        :type array_size: int or None
        :rtype: ~numpy.ndarray(dtype="uint32")
        """
        n_repeats = array_size
        if array_size is None:
            if self.__repeat_type == StructRepeat.GLOBAL:
                array_size = 1
                n_repeats = 1
            else:
                n_repeats = REPEAT_PER_NEURON_FLAG
        elif self.__repeat_type == StructRepeat.GLOBAL and array_size != 1:
            raise ValueError("Global Structures cannot repeat more than once")

        # Start with bytes per repeat, size of data (0 as filled in later),
        # total number of repeats and number of elements in struct
        data = [self.numpy_dtype.itemsize, n_repeats, 0, len(self.__fields)]
        gen_data = list()

        # Go through all values and add in generator data for each
        for data_type, name in self.__fields:

            # Store the writer type
            data.append(get_generator_type(data_type))

            # If we have an array that varies with neuron number
            if array_size is None:
                # There must be a single item for this to work
                data.append(1)
                data.append(REPEAT_PER_NEURON_FLAG)
                if name in values:
                    value = values[name]
                    if not is_singleton(value):
                        value = value.get_single_value_all()
                else:
                    value = self.__default_values[name]
                data.append(param_generator_id(value))
                gen_data.append(param_generator_params(value))

            # If we have a pre-set array size, the values might vary
            else:

                # If we have a range list for the value, generate for the range
                if name in values:
                    vals = values[name]

                    if is_singleton(vals):
                        data.append(1)
                        data.append(array_size)
                        data.append(param_generator_id(vals))
                        gen_data.append(param_generator_params(vals))
                    else:

                        # Store where to update with the number of items and
                        # set to 0 to start
                        n_items_index = len(data)
                        data.append(0)
                        n_items = 0

                        # Go through and get the data for each value
                        for start, stop, value in vals.iter_ranges_by_slice(
                                offset, offset + array_size):
                            n_items += 1
                            # This is the metadata
                            data.append(stop - start)
                            data.append(param_generator_id(value))
                            # This data goes after *all* the metadata
                            gen_data.append(param_generator_params(value))
                        data[n_items_index] = n_items
                else:
                    # Just a single value for all neurons
                    value = self.__default_values[name]
                    data.append(1)
                    data.append(array_size)
                    data.append(param_generator_id(value))
                    gen_data.append(param_generator_params(value))

        # Update with size *before* adding generator parameters
        data[2] = len(data) * BYTES_PER_WORD

        # Add the generator parameters after the rest of the data
        all_data = [numpy.array(data, dtype="uint32")]
        all_data.extend(gen_data)

        # Make it one
        return numpy.concatenate(all_data)

    @property
    def is_generatable(self):
        return all(type_has_generator(data_type)
                   for data_type, _name in self.__fields)

    def read_data(self, data, values, data_offset=0, offset=0,
                  array_size=None):
        """ Read a bytearray of data and write to values

        :param data: The data to be read
        :type data: bytes or bytearray
        :param ~spinn_utilities.ranged.RangeDictionary values:
            The values to update with the read data
        :param int data_offset:
            Index of the byte at the start of the valid data.
        :param int offset:
            The first index into values to write to.
        :param array_size:
            The number of struct copies to read, or None if this is a
            non-repeating struct.
        :type array_size: int or None
        """
        if array_size is None:
            if not self.__repeat_type == StructRepeat.GLOBAL:
                raise ValueError(
                    "Repeating structures must specify an array size")
            array_size = 1
        elif self.__repeat_type == StructRepeat.GLOBAL and array_size != 1:
            raise ValueError("Global Structures cannot repeat more than once")

        if not self.__fields:
            return

        # Read in the data values
        numpy_data = numpy.frombuffer(
            data, offset=data_offset, dtype=self.numpy_dtype, count=array_size)

        for data_type, name in self.fields:
            # Ignore fields that can't be set
            if name in values:
                # Get the data to set for this item
                value = data_type.decode_numpy_array(numpy_data[name])
                if self.__repeat_type == StructRepeat.GLOBAL:
                    values[name] = value[0]
                else:
                    values[name].set_value_by_slice(
                        offset, offset + array_size, value)
