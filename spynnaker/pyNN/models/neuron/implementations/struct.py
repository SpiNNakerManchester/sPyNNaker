import numpy
from spinn_utilities.helpful_functions import is_singleton
from spinn_utilities.ranged.ranged_list import RangedList
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.utilities.utility_calls import convert_to


class Struct(object):
    """ Represents a C code structure
    """

    __slots__ = ["__field_types"]

    def __init__(self, field_types):
        """
        :param field_types:\
            The types of the fields, ordered as they appear in the struct
        :type field_types:\
            list of :py:class:`data_specification.enums.data_type.DataType`
        """
        self.__field_types = field_types

    @property
    def field_types(self):
        """ The types of the fields, ordered as they appear in the struct

        :rtype: list of :py:class:`data_specification.enums.data_type.DataType`
        """
        return self.__field_types

    @property
    def numpy_dtype(self):
        """ The numpy data type of the struct

        :rtype: :py:class:`numpy.dtype`
        """
        return numpy.dtype(
            [("f" + str(i), numpy.dtype(data_type.struct_encoding))
             for i, data_type in enumerate(self.field_types)],
            align=True)

    def get_size_in_whole_words(self, array_size=1):
        """ Get the size of the struct in whole words in an array of given\
            size (default 1 item)

        :param array_size: The number of elements in an array of structs
        :rtype: int
        """
        datatype = self.numpy_dtype
        size_in_bytes = array_size * datatype.itemsize
        return (size_in_bytes + 3) // 4

    def get_data(self, values, offset=0, array_size=1):
        """ Get a numpy array of uint32 of data for the given values

        :param values:\
            A list of values with length the same size as the number of fields\
            returned by field_types
        :type values:\
            list of (single value or list of values or RangedList of values)
        :param offset: The offset into each of the values where to start
        :param array_size: The number of structs to generate
        :rtype: numpy.array(dtype="uint32")
        """
        # Create an array to store values in
        data = numpy.zeros(array_size, dtype=self.numpy_dtype)

        # Go through and get the values and put them in the array
        for i, (values, data_type) in enumerate(zip(values, self.field_types)):

            if is_singleton(values):
                data_value = convert_to(values, data_type)
                data["f" + str(i)] = data_value
            elif not isinstance(values, RangedList):
                data_value = [convert_to(v, data_type)
                              for v in values[offset:(offset + array_size)]]
                data["f" + str(i)] = data_value
            else:
                for start, end, value in values.iter_ranges_by_slice(
                        offset, offset + array_size):

                    # Get the values and get them into the correct data type
                    if get_simulator().is_a_pynn_random(value):
                        values = value.next(end - start)
                        data_value = [convert_to(v, data_type) for v in values]
                    else:
                        data_value = convert_to(value, data_type)
                    data["f" + str(i)][
                        start - offset:end - offset] = data_value

        # Pad to whole number of uint32s
        overflow = (array_size * self.numpy_dtype.itemsize) % 4
        if overflow != 0:
            data = numpy.pad(data.view("uint8"), (0, 4 - overflow), "constant")

        return data.view("uint32")

    def read_data(self, data, offset=0, array_size=1):
        """ Read a bytearray of data and convert to struct values

        :param data: The data to be read
        :param offset: Index of the byte at the start of the valid data
        :param array_size: The number of struct elements to read
        :return:\
            a list of lists of data values, one list for each struct element
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
        else:
            # Read in the data values
            numpy_data = numpy.frombuffer(
                data, offset=offset, dtype=self.numpy_dtype, count=array_size)

            # Go through the things to be set
            items_to_return = list()
            for i, data_type in enumerate(self.field_types):

                # Get the data to set for this item
                values = numpy_data["f" + str(i)]

                items_to_return.append(values / float(data_type.scale))

            # Return values read
            return items_to_return
