# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy
from numpy import uint32, integer
from numpy.typing import NDArray
from enum import Enum
from pyNN.random import RandomDistribution
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from spinn_utilities.helpful_functions import is_singleton
from pacman.model.graphs.common import Slice
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities.utility_calls import convert_to
from spynnaker.pyNN.models.common.param_generator_data import (
    get_generator_type, param_generator_id, param_generator_params,
    type_has_generator)
from spinn_utilities.ranged.abstract_list import AbstractList
from spinn_utilities.ranged.range_dictionary import RangeDictionary

REPEAT_PER_NEURON_FLAG = 0xFFFFFFFF


class StructRepeat(Enum):
    """
    How a structure repeats, or not, in memory.
    """
    #: Indicates a single global struct
    GLOBAL = 0

    #: Indicates a struct that repeats per neuron
    PER_NEURON = 1


class Struct(object):
    """
    Represents a C code structure.
    """
    __slots__ = (
        "__fields",
        "__repeat_type",
        "__default_values")

    def __init__(
            self, fields: Sequence[Tuple[DataType, str]],
            repeat_type: StructRepeat = StructRepeat.PER_NEURON,
            default_values: Optional[Dict[str, Union[int, float]]] = None):
        """
        :param fields:
            The types and names of the fields, ordered as they appear in the
            structure.
        :type fields: list(~data_specification.enums.DataType, str)
        :param StructRepeat repeat_type: How the structure repeats
        :param default_values:
            Dict of field name -> value to use when values doesn't contain the
            field
        :type default_values: dict(str, int or float) or None
        """
        self.__fields = fields
        self.__repeat_type = repeat_type
        self.__default_values = default_values or dict()

    @property
    def fields(self) -> Sequence[Tuple[DataType, str]]:
        """
        The types and names of the fields, ordered as they appear in the
        structure.

        :rtype: list(~data_specification.enums.DataType, str)
        """
        return self.__fields

    @property
    def repeat_type(self) -> StructRepeat:
        """
        How the structure repeats.

        :rtype: StructRepeat
        """
        return self.__repeat_type

    @property
    def numpy_dtype(self) -> numpy.dtype:
        """
        The numpy data type of the structure.

        :rtype: ~numpy.dtype
        """
        return numpy.dtype(
            [(name, numpy.dtype(data_type.struct_encoding))
             for data_type, name in self.__fields],
            align=True)

    def get_size_in_whole_words(self, array_size: int = 1) -> int:
        """
        Get the size of the structure in whole words in an array of given
        size (default 1 item).

        :param int array_size: The number of elements in an array of structures
        :rtype: int
        """
        datatype = self.numpy_dtype
        size_in_bytes = array_size * datatype.itemsize
        return (size_in_bytes + (BYTES_PER_WORD - 1)) // BYTES_PER_WORD

    def get_data(self, values: Dict[str, Union[int, float, AbstractList]],
                 vertex_slice: Optional[Slice] = None) -> NDArray[uint32]:
        """
        Get a numpy array of uint32 of data for the given values.

        :param values: The values to fill in the data with
        :type values: dict(str, int or float or AbstractList)
        :param vertex_slice:
            The vertex slice to get the data for, or `None` if the structure is
            global.
        :type vertex_slice: Slice or None
        :rtype: ~numpy.ndarray(dtype="uint32")
        """
        n_items = 1
        if vertex_slice is None:
            if self.__repeat_type != StructRepeat.GLOBAL:
                raise ValueError(
                    "Repeating structures must specify a vertex_slice")
        elif self.__repeat_type == StructRepeat.GLOBAL:
            raise ValueError("Global Structures do not have a slice")
        else:
            n_items = vertex_slice.n_atoms

        # Create an array to store values in
        data = numpy.zeros(n_items, dtype=self.numpy_dtype)

        if not self.__fields:
            return data.view(uint32)

        # Go through and get the values and put them in the array
        for data_type, name in self.__fields:
            if name in values:
                all_vals = values[name]

                if is_singleton(all_vals):
                    # If there is just one value for everything, use it
                    # everywhere
                    data[name] = convert_to(all_vals, data_type)
                elif self.__repeat_type == StructRepeat.GLOBAL:
                    # If there is a ranged list for global struct,
                    # we might need to read a single value
                    assert isinstance(all_vals, AbstractList)
                    data[name] = convert_to(
                        all_vals.get_single_value_all(), data_type)
                else:
                    assert isinstance(all_vals, AbstractList)
                    assert vertex_slice is not None
                    self.__get_data_for_slice(
                        data, all_vals, name, data_type, vertex_slice)
            else:
                # If there is only a default value, get that and use it
                # everywhere
                value = self.__default_values[name]
                data_value = convert_to(value, data_type)
                data[name] = data_value

        # Pad to whole number of uint32s
        overflow = (n_items * self.numpy_dtype.itemsize) % BYTES_PER_WORD
        if overflow != 0:
            data = numpy.pad(
                data.view("uint8"), (0, BYTES_PER_WORD - overflow), "constant")

        return data.view(uint32)

    def __get_data_for_slice(
            self, data: NDArray, all_vals: AbstractList, name: str,
            data_type: DataType, vertex_slice: Slice):
        """
        Get the data for a single value from a vertex slice.
        """
        # If there is a list of values, convert it
        ids = vertex_slice.get_raster_ids()
        data_pos = 0
        for start, stop, value in all_vals.iter_ranges_by_ids(ids):
            # Get the values and convert to the correct data type
            n_values = stop - start
            if isinstance(value, RandomDistribution):
                r_vals = value.next(n_values)
                data[name][data_pos:data_pos + n_values] = [
                    convert_to(v, data_type) for v in r_vals]
            else:
                data[name][data_pos:data_pos + n_values] = convert_to(
                    value, data_type)

            data_pos += n_values

    def get_generator_data(
            self, values: RangeDictionary,
            vertex_slice: Optional[Slice] = None) -> NDArray[uint32]:
        """
        Get a numpy array of uint32 of data to generate the given values.

        :param ~dict-like values:
            The values to fill in the data with
        :param vertex_slice:
            The vertex slice or `None` for a structure with repeat_type global,
            or where a single value repeats for every neuron.  If this is not
            the case and vertex_slice is `None`, an error will be raised!
        :type vertex_slice: Slice or None
        :rtype: ~numpy.ndarray(dtype="uint32")
        """
        # Define n_repeats, which is either the total number of neurons
        # or a flag to indicate that the data repeats for each neuron
        if vertex_slice is None:
            if self.__repeat_type == StructRepeat.GLOBAL:
                n_repeats = 1
            else:
                n_repeats = REPEAT_PER_NEURON_FLAG
        else:
            if self.__repeat_type == StructRepeat.GLOBAL:
                raise ValueError(
                    "Global Structures cannot repeat more than once")
            n_repeats = vertex_slice.n_atoms

        # Start with bytes per repeat, n_repeats (from above),
        # total size of data written (0 as filled in later),
        # and number of fields in struct
        data = [self.numpy_dtype.itemsize, n_repeats, 0, len(self.__fields)]
        gen_data: List[NDArray[uint32]] = list()

        # Go through all values and add in generator data for each
        for data_type, name in self.__fields:
            # Store the writer type based on the data type
            data.append(get_generator_type(data_type))

            # We want the data generated "per neuron" regardless of how many -
            # there must be a single value for this to work
            if vertex_slice is None:
                self.__gen_data_one_for_all(data, gen_data, values, name)

            # If we know the array size, the values can vary per neuron
            else:
                self.__gen_data_for_slice(
                    data, gen_data, values, name, vertex_slice)

        # Update with size *before* adding generator parameters
        data[2] = len(data) * BYTES_PER_WORD

        # Add the generator parameters after the rest of the data
        all_data = [numpy.array(data, dtype=uint32)]
        all_data.extend(gen_data)

        # Make it one
        return numpy.concatenate(all_data)

    def __gen_data_one_for_all(
            self, data: List[int], gen_data: List[NDArray[uint32]],
            values: RangeDictionary, name: str):
        """
        Generate data with a single value for all neurons.
        """
        # How many sub-sets of repeats there are (1 in this case as
        # that one sub-set covers all neurons)
        data.append(1)

        # How many times to repeat the next bit (once for each neuron
        # which is determined at execution time)
        data.append(REPEAT_PER_NEURON_FLAG)

        # Get the value to write, of which there can only be one
        # (or else there will be an error here ;)
        value: Any
        if name in values:
            value = values[name]
            if not is_singleton(value):
                value = value.get_single_value_all()
        else:
            value = self.__default_values[name]

        # Write the id of the generator of the parameter
        data.append(param_generator_id(value))

        # Add any parameters required to generate the values
        gen_data.append(param_generator_params(value))

    def __gen_data_for_slice(
            self, data: List[int], gen_data: List[NDArray[uint32]],
            values: RangeDictionary, name: str, vertex_slice: Slice):
        """
        Generate data with different values for each neuron.
        """
        # If we have a range list for the value, generate for the range
        if name in values:
            vals = values[name]

            if is_singleton(vals):
                # If there is a single value, we can just use that
                # on all atoms
                data.append(1)
                data.append(vertex_slice.n_atoms)
                data.append(param_generator_id(vals))
                gen_data.append(param_generator_params(vals))
            else:
                # Store where to update with the number of items and
                # set to 0 to start
                n_items_index = len(data)
                data.append(0)
                n_items = 0

                # Go through and get the data for each value
                ids = vertex_slice.get_raster_ids()
                for start, stop, value in vals.iter_ranges_by_ids(ids):
                    n_items += 1
                    # This is the metadata
                    data.append(stop - start)
                    data.append(param_generator_id(value))
                    # This data goes after *all* the metadata
                    gen_data.append(param_generator_params(value))
                data[n_items_index] = n_items
        else:
            # Just a single value for all neurons from defaults
            value = self.__default_values[name]
            data.append(1)
            data.append(vertex_slice.n_atoms)
            data.append(param_generator_id(value))
            gen_data.append(param_generator_params(value))

    @property
    def is_generatable(self) -> bool:
        """
        Whether the data inside could be generated on machine.

        :rtype: bool
        """
        return all(type_has_generator(data_type)
                   for data_type, _name in self.__fields)

    def read_data(
            self, data: bytes, values: RangeDictionary, data_offset: int = 0,
            vertex_slice: Optional[Slice] = None):
        """
        Read a byte string of data and write to values.

        :param data: The data to be read
        :type data: bytes or bytearray
        :param ~spinn_utilities.ranged.RangeDictionary values:
            The values to update with the read data
        :param int data_offset:
            Index of the byte at the start of the valid data.
        :param int offset:
            The first index into values to write to.
        :param array_size:
            The number of structure copies to read, or `None` if this is a
            non-repeating structure.
        :type array_size: int or None
        """
        n_items = 1
        ids = numpy.zeros([0], dtype=integer)
        if vertex_slice is None:
            if self.__repeat_type != StructRepeat.GLOBAL:
                raise ValueError(
                    "Repeating structures must specify an array size")
        elif self.__repeat_type == StructRepeat.GLOBAL:
            raise ValueError("Global Structures do not have a slice")
        else:
            n_items = vertex_slice.n_atoms
            ids = vertex_slice.get_raster_ids()

        if not self.__fields:
            return

        # Read in the data values
        numpy_data = numpy.frombuffer(
            data, offset=data_offset, dtype=self.numpy_dtype, count=n_items)

        for data_type, name in self.fields:
            # Ignore fields that can't be set
            if name in values:
                # Get the data to set for this item
                value = data_type.decode_numpy_array(numpy_data[name])
                if self.__repeat_type == StructRepeat.GLOBAL:
                    values[name] = value[0]
                else:
                    values[name].set_value_by_ids(ids, value)
