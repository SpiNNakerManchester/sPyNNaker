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
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView

# Address to indicate that the synaptic region is unused
SYN_REGION_UNUSED = 0xFFFFFFFF


class GeneratorData(object):
    """ Data for each connection of the synapse generator.
    """
    __slots__ = [
        "__delayed_synaptic_matrix_offset",
        "__max_delayed_row_n_synapses",
        "__max_delayed_row_n_words",
        "__max_row_n_synapses",
        "__max_row_n_words",
        "__max_stage",
        "__max_delay_per_stage",
        "__post_slices",
        "__post_vertex_slice",
        "__pre_slices",
        "__pre_vertex_slice",
        "__synapse_information",
        "__synaptic_matrix_offset"]

    BASE_SIZE = 17 * BYTES_PER_WORD

    def __init__(
            self, synaptic_matrix_offset, delayed_synaptic_matrix_offset,
            max_row_n_words, max_delayed_row_n_words, max_row_n_synapses,
            max_delayed_row_n_synapses, pre_slices, post_slices,
            pre_vertex_slice, post_vertex_slice, synapse_information,
            max_stage,  max_delay_per_stage):
        self.__synaptic_matrix_offset = synaptic_matrix_offset
        self.__delayed_synaptic_matrix_offset = delayed_synaptic_matrix_offset
        self.__max_row_n_words = max_row_n_words
        self.__max_delayed_row_n_words = max_delayed_row_n_words
        self.__max_row_n_synapses = max_row_n_synapses
        self.__max_delayed_row_n_synapses = max_delayed_row_n_synapses
        self.__pre_slices = pre_slices
        self.__post_slices = post_slices
        self.__pre_vertex_slice = pre_vertex_slice
        self.__post_vertex_slice = post_vertex_slice
        self.__synapse_information = synapse_information
        self.__max_stage = max_stage
        self.__max_delay_per_stage = max_delay_per_stage

        # Offsets are used in words in the generator, but only
        # if the values are valid
        if self.__synaptic_matrix_offset != SYN_REGION_UNUSED:
            self.__synaptic_matrix_offset //= BYTES_PER_WORD
        if self.__delayed_synaptic_matrix_offset != SYN_REGION_UNUSED:
            self.__delayed_synaptic_matrix_offset //= BYTES_PER_WORD

    @property
    def size(self):
        """ The size of the generated data in bytes

        :rtype: int
        """
        connector = self.__synapse_information.connector
        dynamics = self.__synapse_information.synapse_dynamics

        return sum((self.BASE_SIZE,
                    dynamics.gen_matrix_params_size_in_bytes,
                    connector.gen_connector_params_size_in_bytes,
                    connector.gen_weight_params_size_in_bytes(
                        self.__synapse_information.weights),
                    connector.gen_delay_params_size_in_bytes(
                        self.__synapse_information.delays)))

    @property
    def gen_data(self):
        """ The data to be written for this connection

        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        connector = self.__synapse_information.connector
        synapse_dynamics = self.__synapse_information.synapse_dynamics
        items = list()
        items.append(numpy.array([
            self.__synaptic_matrix_offset,
            self.__delayed_synaptic_matrix_offset,
            self.__max_row_n_words,
            self.__max_delayed_row_n_words,
            self.__max_row_n_synapses,
            self.__max_delayed_row_n_synapses,
            self.__pre_vertex_slice.lo_atom,
            self.__pre_vertex_slice.n_atoms,
            self.__max_stage,
            self.__max_delay_per_stage,
            DataType.S1615.encode_as_int(
                SpynnakerDataView().simulation_time_step_per_ms),
            self.__synapse_information.synapse_type,
            synapse_dynamics.gen_matrix_id,
            connector.gen_connector_id,
            connector.gen_weights_id(self.__synapse_information.weights),
            connector.gen_delays_id(self.__synapse_information.delays)],
            dtype=numpy.uint32))
        items.append(synapse_dynamics.gen_matrix_params)
        items.append(connector.gen_connector_params(
            self.__pre_slices, self.__post_slices, self.__pre_vertex_slice,
            self.__post_vertex_slice, self.__synapse_information.synapse_type,
            self.__synapse_information))
        items.append(connector.gen_weights_params(
            self.__synapse_information.weights, self.__pre_vertex_slice,
            self.__post_vertex_slice))
        items.append(connector.gen_delay_params(
            self.__synapse_information.delays, self.__pre_vertex_slice,
            self.__post_vertex_slice))
        return items
