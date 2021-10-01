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

import decimal
import numpy
from data_specification.enums.data_type import DataType


class GeneratorData(object):
    """ Data for each connection of the synapse generator.
    """
    __slots__ = [
        "__delayed_synaptic_matrix_offset",
        "__machine_time_step",
        "__max_delayed_row_n_synapses",
        "__max_delayed_row_n_words",
        "__max_row_n_synapses",
        "__max_row_n_words",
        "__max_stage",
        "__post_slice_index",
        "__post_slices",
        "__post_vertex_slice",
        "__pre_slice_index",
        "__pre_slices",
        "__pre_vertex_slice",
        "__synapse_information",
        "__synaptic_matrix_offset"]

    BASE_SIZE = 17 * 4

    def __init__(
            self, synaptic_matrix_offset, delayed_synaptic_matrix_offset,
            max_row_n_words, max_delayed_row_n_words, max_row_n_synapses,
            max_delayed_row_n_synapses, pre_slices, pre_slice_index,
            post_slices, post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_information, max_stage, machine_time_step):
        self.__synaptic_matrix_offset = synaptic_matrix_offset
        self.__delayed_synaptic_matrix_offset = delayed_synaptic_matrix_offset
        self.__max_row_n_words = max_row_n_words
        self.__max_delayed_row_n_words = max_delayed_row_n_words
        self.__max_row_n_synapses = max_row_n_synapses
        self.__max_delayed_row_n_synapses = max_delayed_row_n_synapses
        self.__pre_slices = pre_slices
        self.__pre_slice_index = pre_slice_index
        self.__post_slices = post_slices
        self.__post_slice_index = post_slice_index
        self.__pre_vertex_slice = pre_vertex_slice
        self.__post_vertex_slice = post_vertex_slice
        self.__synapse_information = synapse_information
        self.__max_stage = max_stage
        self.__machine_time_step = machine_time_step

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
                        self.__synapse_information.weight),
                    connector.gen_delay_params_size_in_bytes(
                        self.__synapse_information.delay)))

    @property
    def gen_data(self):
        """ Get the data to be written for this connection
        :rtype: numpy array of uint32
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
            (decimal.Decimal(str(1000.0 / float(self.__machine_time_step))) *
             DataType.S1615.scale),
            self.__synapse_information.synapse_type,
            synapse_dynamics.gen_matrix_id,
            connector.gen_connector_id,
            connector.gen_weights_id(self.__synapse_information.weight),
            connector.gen_delays_id(self.__synapse_information.delay)],
            dtype="uint32"))
        items.append(synapse_dynamics.gen_matrix_params)
        items.append(connector.gen_connector_params(
            self.__pre_slices, self.__pre_slice_index, self.__post_slices,
            self.__post_slice_index, self.__pre_vertex_slice,
            self.__post_vertex_slice, self.__synapse_information.synapse_type))
        items.append(connector.gen_weights_params(
            self.__synapse_information.weight, self.__pre_vertex_slice,
            self.__post_vertex_slice))
        items.append(connector.gen_delay_params(
            self.__synapse_information.delay, self.__pre_vertex_slice,
            self.__post_vertex_slice))
        return numpy.concatenate(items)
