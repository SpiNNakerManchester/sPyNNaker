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


def convert_value(data, data_type, create_command_str):
    """ Insert command to write a value one or more times to the current\
        write pointer, causing the write pointer to move on by the number\
        of bytes required to represent the data type. The data is passed\
        as a parameter to this function


    Based on https://github.com/SpiNNakerManchester/DataSpecification/blob/
    master/data_specification/data_specification_generator.py
    WRITE_VALUE method

    :param data: the data to write as a float.
    :type data: float
    :param data_type: the type to convert data to
    :type data_type: :py:class:`DataType`
    :return: Nothing is returned
    :rtype: None
    :raise data_specification.exceptions.DataUndefinedWriterException:\
        If the binary specification file writer has not been initialised
    :raise spinn_storage_handlers.exceptions.DataWriteException:\
        If a write to external storage fails
    :raise data_specification.exceptions.\
        DataSpecificationParameterOutOfBoundsException:\
        * If repeats_register is None, and repeats is out of range
        * If repeats_register is not a valid register id
        * If data_type is an integer type, and data has a fractional part
        * If data would overflow the data type
    :raise data_specification.exceptions.\
        DataSpecificationUnknownTypeException: If the data type is not\
        known
    :raise data_specification.exceptions.\
        DataSpecificationInvalidSizeException: If the data size is invalid
    :raise data_specification.exceptions.\
        DataSpecificationNoRegionSelectedException: If no region has been \
        selected to write to
    """
    # if self.current_region is None:
    #    raise exceptions.DataSpecificationNoRegionSelectedException(
    #        "WRITE")


    data_size = data_type.size
    if data_size == 1:
        cmd_data_len = constants.LEN2
        data_len = 0
    elif data_size == 2:
        cmd_data_len = constants.LEN2
        data_len = 1
    elif data_size == 4:
        cmd_data_len = constants.LEN2
        data_len = 2
    elif data_size == 8:
        cmd_data_len = constants.LEN3
        data_len = 3
    else:
        raise exceptions.DataSpecificationInvalidSizeException(
            data_type.name, data_size,
            Commands.WRITE.name)  # @UndefinedVariable

    """
    if repeats_is_register is False:
        if (repeats <= 0) or (repeats > 255):
            raise exceptions.\
                DataSpecificationParameterOutOfBoundsException(
                    "repeats", repeats, 0, 255,
                    Commands.WRITE.name)  # @UndefinedVariable
    else:
        if (repeats < 0) or (repeats >= constants.MAX_REGISTERS):
            raise exceptions.\
                DataSpecificationParameterOutOfBoundsException(
                    "repeats_is_register", repeats_is_register, 0,
                    (constants.MAX_REGISTERS - 1),
                    Commands.WRITE.name)  # @UndefinedVariable
    """

    if (data_type.min > data) or (data_type.max < data):
        raise exceptions.DataSpecificationParameterOutOfBoundsException(
            "data", data, data_type.min, data_type.max,
            Commands.WRITE.name)  # @UndefinedVariable

    parameters = 1
    cmd_string = None
    if create_command_str:
        cmd_string = "WRITE data=0x%8.8X" % data

    repeat_reg_usage = constants.NO_REGS
    if create_command_str:
        cmd_string = "{0:s}, repeats={1:d}".format(cmd_string, 1)

    cmd_word = (
        (cmd_data_len << 28) |
        (Commands.WRITE.value << 20) |  # @UndefinedVariable
        (repeat_reg_usage << 16) | (data_len << 12) | 1)
        # 1 comes from parameters = 1 |= repeats (which is 1)

    data_value = decimal.Decimal("{}".format(data)) * data_type.scale
    padding = 4 - data_type.size if data_type.size < 4 else 0

    cmd_word_list = struct.pack(
        "<I{}{}x".format(data_type.struct_encoding, padding),
        cmd_word, data_value)
    if create_command_str:
        cmd_string = "{0:s}, dataType={1:s}".format(
            cmd_string, data_type.name)

    return cmd_word_list, cmd_string
