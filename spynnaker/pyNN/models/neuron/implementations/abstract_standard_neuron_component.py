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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities.struct import Struct
from .ranged_dict_vertex_slice import RangedDictVertexSlice


class AbstractStandardNeuronComponent(object, metaclass=AbstractBase):
    """ Represents a component of a standard neural model.
    """

    __slots__ = ["__struct"]

    def __init__(self, data_types):
        """
        :param list(~data_specification.enums.DataType) data_types:
            A list of data types in the component structure, in the order that
            they appear
        """
        self.__struct = Struct(data_types)

    @property
    def struct(self):
        """ The structure of the component. This structure will have copies in\
            both SDRAM (the initialisation values) and DTCM (the working copy).

        :rtype: ~spynnaker.pyNN.utilities.struct.Struct
        """
        return self.__struct

    def get_sdram_usage_in_bytes(self, n_neurons):
        """ Get the SDRAM memory usage required

        :param int n_neurons: The number of neurons to get the usage for
        :rtype: int
        """
        return self.struct.get_size_in_whole_words(n_neurons) * BYTES_PER_WORD

    @abstractmethod
    def add_parameters(self, parameters):
        """ Add the initial values of the parameters to the parameter holder

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            A holder of the parameters
        """

    @abstractmethod
    def add_state_variables(self, state_variables):
        """ Add the initial values of the state variables to the state\
            variables holder

        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            A holder of the state variables
        """

    @abstractmethod
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """ Get the values to be written to the machine for this model

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            The holder of the parameters
        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            The holder of the state variables
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of variables being retrieved
        :param float ts:
            The time to be advanced in one call to the update of this component
        :return: A list with the same length as self.struct.field_types
        :rtype: list(int or float or list(int) or list(float) or
            ~spinn_utilities.ranged.RangedList)
        """

    def get_data(self, parameters, state_variables, vertex_slice, ts):
        """ Get the data *to be written to the machine* for this model.

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            The holder of the parameters
        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            The holder of the state variables
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to generate parameters for
        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        values = self.get_values(parameters, state_variables, vertex_slice, ts)
        return self.struct.get_data(
            values, vertex_slice.lo_atom, vertex_slice.n_atoms)

    @abstractmethod
    def update_values(self, values, parameters, state_variables):
        """ Update the parameters and state variables with the given struct\
            values that have been read from the machine

        :param list(list) values:
            The values read from the machine, one for each struct element
        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            The holder of the parameters to update
        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            The holder of the state variables to update
        """

    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        """ Read the parameters and state variables of the model\
            *from the given data* (read from the machine)

        :param data: The data to be read
        :type data: bytes or bytearray
        :param int offset: The offset where the data should be read from
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to read parameters for
        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            The holder of the parameters to update
        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            The holder of the state variables to update
        :return: The offset after reading the data
        :rtype: int
        """
        values = self.struct.read_data(data, offset, vertex_slice.n_atoms)
        offset += BYTES_PER_WORD * self.struct.get_size_in_whole_words(
            vertex_slice.n_atoms)
        params = RangedDictVertexSlice(parameters, vertex_slice)
        variables = RangedDictVertexSlice(state_variables, vertex_slice)
        self.update_values(values, params, variables)
        return offset

    @abstractmethod
    def has_variable(self, variable):
        """ Determine if this component has a variable by the given name

        :param str variable: The name of the variable
        :rtype: bool
        """

    @abstractmethod
    def get_units(self, variable):
        """ Get the units of the given variable

        :param str variable: The name of the variable
        """
