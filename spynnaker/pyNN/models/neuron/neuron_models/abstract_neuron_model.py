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
from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities.struct import Struct


class AbstractNeuronModel(
        AbstractStandardNeuronComponent, metaclass=AbstractBase):
    """ Represents a neuron model.
    """

    __slots__ = ["__global_struct"]

    def __init__(self, data_types, global_data_types=None):
        """
        :param list(~data_specification.enums.DataType) data_types:
            A list of data types in the neuron structure, in the order that
            they appear
        :param global_data_types:
            A list of data types in the neuron global structure, in the order
            that they appear
        :type global_data_types:
            list(~data_specification.enums.DataType) or None
        """
        super().__init__(data_types)
        if global_data_types is None:
            global_data_types = []
        self.__global_struct = Struct(global_data_types)

    @property
    def global_struct(self):
        """ Get the global parameters structure

        :rtype: ~spynnaker.pyNN.utilities.struct.Struct
        """
        return self.__global_struct

    @property
    def __global_size(self):
        """ size of the global data, in bytes
        """
        return self.__global_struct.get_size_in_whole_words() * BYTES_PER_WORD

    @overrides(AbstractStandardNeuronComponent.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        usage = super().get_sdram_usage_in_bytes(n_neurons)
        return usage + self.__global_size

    def get_global_values(self, ts):  # pylint: disable=unused-argument
        """ Get the global values to be written to the machine for this model

        :param float ts: The time to advance the model at each call
        :return: A list with the same length as self.global_struct.field_types
        :rtype: list(int or float) or ~numpy.ndarray
        """
        return numpy.zeros(0, dtype="uint32")

    @overrides(AbstractStandardNeuronComponent.get_data)
    def get_data(self, parameters, state_variables, vertex_slice, ts):
        super_data = super().get_data(
            parameters, state_variables, vertex_slice, ts)
        values = self.get_global_values(ts)
        global_data = self.__global_struct.get_data(values)
        return numpy.concatenate([global_data, super_data])

    @overrides(AbstractStandardNeuronComponent.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        # Assume that the global data doesn't change
        offset += self.__global_size
        return super().read_data(
            data, offset, vertex_slice, parameters, state_variables)
