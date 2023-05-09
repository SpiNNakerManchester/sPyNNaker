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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

# Address to indicate that the synaptic region is unused
SYN_REGION_UNUSED = 0xFFFFFFFF


class GeneratorData(object):
    """
    Data for each connection of the synapse generator.
    """
    __slots__ = [
        "__data"
    ]

    BASE_SIZE = 11 * BYTES_PER_WORD

    def __init__(
            self, synaptic_matrix_offset, delayed_synaptic_matrix_offset,
            app_edge, synapse_information, max_row_info,
            max_pre_atoms_per_core, max_post_atoms_per_core):
        # Offsets are used in words in the generator, but only
        # if the values are valid
        if synaptic_matrix_offset is not None:
            synaptic_matrix_offset //= BYTES_PER_WORD
        else:
            synaptic_matrix_offset = SYN_REGION_UNUSED
        if delayed_synaptic_matrix_offset is not None:
            delayed_synaptic_matrix_offset //= BYTES_PER_WORD
        else:
            delayed_synaptic_matrix_offset = SYN_REGION_UNUSED

        # Take care of Population views
        pre_lo = 0
        pre_hi = synapse_information.n_pre_neurons - 1
        if synapse_information.prepop_is_view:
            indexes = synapse_information.pre_population._indexes
            pre_lo = indexes[0]
            pre_hi = indexes[-1]
        post_lo = 0
        post_hi = synapse_information.n_post_neurons - 1
        if synapse_information.postpop_is_view:
            indexes = synapse_information.post_population._indexes
            post_lo = indexes[0]
            post_hi = indexes[-1]

        # Get objects needed for the next bit
        connector = synapse_information.connector
        synapse_dynamics = synapse_information.synapse_dynamics

        # Create the data needed
        self.__data = list()
        self.__data.append(numpy.array([
            pre_lo, pre_hi, post_lo, post_hi,
            synapse_information.synapse_type,
            synapse_dynamics.gen_matrix_id,
            connector.gen_connector_id,
            connector.gen_weights_id(synapse_information.weights),
            connector.gen_delays_id(synapse_information.delays)
            ], dtype=numpy.uint32))
        self.__data.append(synapse_dynamics.gen_matrix_params(
            synaptic_matrix_offset, delayed_synaptic_matrix_offset, app_edge,
            synapse_information, max_row_info, max_pre_atoms_per_core,
            max_post_atoms_per_core))
        self.__data.append(connector.gen_connector_params())
        self.__data.append(connector.gen_weights_params(
            synapse_information.weights))
        self.__data.append(connector.gen_delay_params(
            synapse_information.delays))

    @property
    def size(self):
        """
        The size of the generated data, in bytes.

        :rtype: int
        """
        return sum(len(i) for i in self.__data) * BYTES_PER_WORD

    @property
    def gen_data(self):
        """
        The data to be written for this connection.

        :rtype: list(~numpy.ndarray(~numpy.uint32))
        """
        return self.__data
