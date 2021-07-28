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
from pyNN.random import RandomDistribution
from spinn_utilities.helpful_functions import is_singleton
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities.utility_calls import convert_to


class Struct(object):
    """ Represents a C code structure.
    """

    __slots__ = ["__field_types"]

    def __init__(self, field_types):
        """
        :param list(~data_specification.enums.DataType) field_types:
            The types of the fields, ordered as they appear in the struct.
        """
        self.__field_types = field_types

    @property
    def field_types(self):
        """ The types of the fields, ordered as they appear in the struct.

        :rtype: list(~data_specification.enums.DataType)
        """
        return self.__field_types

    @property
    def numpy_dtype(self):
        """ The numpy data type of the struct

        :rtype: ~numpy.dtype
        """
        return numpy.dtype(
            [("f" + str(i), numpy.dtype(data_type.struct_encoding))
             for i, data_type in enumerate(self.field_types)],
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

    def get_data(self, values, vertex_slice, atoms_shape):
        """ Get a numpy array of uint32 of data for the given values

        :param values:
            A list of values with length the same size as the number of fields
            returned by field_types
        :type values:
            list(int or float or list(int) or list(float) or
            ~spinn_utilities.ranged.RangedList)
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to get values for
        :param tuple(int) atoms_shape: The shape of the atoms in the vertex
        :rtype: ~numpy.ndarray(dtype="uint32")
        """
        # Create an array to store values in
        data = numpy.zeros(vertex_slice.n_atoms, dtype=self.numpy_dtype)

        # Go through and get the values and put them in the array
        for i, (values, data_type) in enumerate(zip(values, self.field_types)):

            if is_singleton(values):
                data_value = convert_to(values, data_type)
                data["f" + str(i)] = data_value
            else:
                indices = vertex_slice.get_raster_ids(atoms_shape)
                in_values = [
                    values[int(j)]
                    if not isinstance(values[int(j)], RandomDistribution)
                    else values[int(j)].next() for j in indices]
                data_value = [convert_to(v, data_type)
                              for v in in_values]
                data["f" + str(i)] = data_value

        # Pad to whole number of uint32s
        overflow = (len(data) * self.numpy_dtype.itemsize) % BYTES_PER_WORD
        if overflow != 0:
            data = numpy.pad(
                data.view("uint8"), (0, BYTES_PER_WORD - overflow), "constant")

        return data.view("uint32")

    def read_data(self, data, offset=0, array_size=1):
        """ Read a bytearray of data and convert to struct values

        :param data: The data to be read
        :type data: bytes or bytearray
        :param int offset: Index of the byte at the start of the valid data
        :param int array_size: The number of struct elements to read
        :return:
            a list of lists of data values, one list for each struct element
        :rtype: list(float)
        """
        if self.numpy_dtype.itemsize == 0:
            return numpy.zeros(0, dtype=self.numpy_dtype)

        # Prepare items to return
        items_to_return = list()

        # It could be possible that a component has no parameters
        # (for example, InputTypeCurrent): this needs to be dealt with,
        # as numpy.frombuffer does not like an empty type
        if len(self.numpy_dtype) == 0:
            return items_to_return

        # Read in the data values
        numpy_data = numpy.frombuffer(
            data, offset=offset, dtype=self.numpy_dtype, count=array_size)

        # Go through the things to be set
        items_to_return = list()
        for i, data_type in enumerate(self.field_types):
            # Get the data to set for this item
            values = numpy_data["f" + str(i)]
            # TODO: types that are integers should become integers
            items_to_return.append(values / float(data_type.scale))

        # Return values read
        return items_to_return
