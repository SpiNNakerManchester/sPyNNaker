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

import math
from six import itervalues

from pacman.model.graphs.common.slice import Slice

from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)

from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine, AbstractSynapseDynamicsStructural)

from .synaptic_matrix import SynapticMatrix
from .generator_data import GeneratorData


# Address to indicate that the synaptic region is unused
_SYN_REGION_UNUSED = 0xFFFFFFFF


class SynapticMatrixApp(object):
    """ The synaptic matrix/matrices for an incoming app vertex
    """

    __slots__ = [
        "__synapse_io",
        "__poptable",
        "__synapse_info",
        "__app_edge",
        "__n_synapse_types",
        "__all_single_syn_sz",
        "__post_vertex_slice",
        "__synaptic_matrix_region",
        "__direct_matrix_region",
        "__matrices",
        "__max_row_info",
        "__all_syn_block_sz",
        "__app_key_info",
        "__delay_app_key_info",
        "__routing_info",
        "__weight_scales",
        "__m_edges",
        "__use_app_keys",
        "__matrix_size",
        "__delay_matrix_size",
        "__syn_mat_offset",
        "__delay_syn_mat_offset",
        "__index",
        "__received_block",
        "__delay_received_block"
    ]

    def __init__(
            self, synapse_io, poptable, synapse_info, app_edge,
            n_synapse_types, all_single_syn_sz, post_vertex_slice,
            synaptic_matrix_region, direct_matrix_region):
        self.__synapse_io = synapse_io
        self.__poptable = poptable
        self.__synapse_info = synapse_info
        self.__app_edge = app_edge
        self.__n_synapse_types = n_synapse_types
        self.__all_single_syn_sz = all_single_syn_sz
        self.__post_vertex_slice = post_vertex_slice
        self.__synaptic_matrix_region = synaptic_matrix_region
        self.__direct_matrix_region = direct_matrix_region

        # Map of machine_edge to .SynapticMatrix
        self.__matrices = dict()

        # Calculate the max row info for this edge
        self.__max_row_info = self.__synapse_io.get_max_row_info(
            synapse_info, self.__post_vertex_slice,
            app_edge.n_delay_stages, self.__poptable,
            globals_variables.get_simulator().machine_time_step, app_edge)

        # These are set directly later
        self.__all_syn_block_sz = None
        self.__app_key_info = None
        self.__delay_app_key_info = None
        self.__routing_info = None
        self.__weight_scales = None
        self.__m_edges = None
        self.__use_app_keys = None

        self.__matrix_size = (
            self.__app_edge.pre_vertex.n_atoms *
            self.__max_row_info.undelayed_max_bytes)
        self.__delay_matrix_size = (
            self.__app_edge.pre_vertex.n_atoms *
            self.__app_edge.n_delay_stages *
            self.__max_row_info.delayed_max_bytes)

        # These are computed during synaptic generation
        self.__syn_mat_offset = None
        self.__delay_syn_mat_offset = None
        self.__index = None

        # These are stored when blocks are read
        self.__received_block = None
        self.__delay_received_block = None

    def __get_matrix(self, machine_edge):
        """ Get or create a matrix object

        :param ~pacman.model.graph.machine.machine_edge.MachineEdge
            machine_edge: The machine edge to get the matrix for
        :rtype: SynapticMatrix
        """
        if machine_edge in self.__matrices:
            return self.__matrices[machine_edge]

        r_info = self.__routing_info.get_routing_info_for_edge(machine_edge)
        delayed_r_info = None
        delayed_edge = machine_edge.delay_edge
        if delayed_edge is not None:
            delayed_r_info = self.__routing_info.get_routing_info_for_edge(
                delayed_edge)
        matrix = SynapticMatrix(
            self.__synapse_io, self.__poptable, self.__synapse_info,
            machine_edge, self.__app_edge, self.__n_synapse_types,
            self.__max_row_info, r_info, delayed_r_info, self.__weight_scales,
            self.__all_syn_block_sz, self.__all_single_syn_sz)
        self.__matrices[machine_edge] = matrix
        return matrix

    @property
    def size(self):
        """ The number of bytes required by the synaptic matrices

        :rtype: int
        """
        return self.__matrix_size

    @property
    def delayed_size(self):
        """ The number of bytes required by the delayed synaptic matrices

        :rtype: int
        """
        return self.__delay_matrix_size

    @property
    def generator_info_size(self):
        """ The number of bytes required by the generator information
        """
        if not self.__synapse_info.may_generate_on_machine():
            return 0

        # Get the number of likely machine vertices
        max_atoms = self.__app_edge.pre_vertex.get_max_atoms_per_core()
        if self.__app_edge.pre_vertex.n_atoms < max_atoms:
            max_atoms = self.__app_edge.pre_vertex.n_atoms
        n_edge_vertices = int(math.ceil(
            float(self.__app_edge.pre_vertex.n_atoms) / float(max_atoms)))

        connector = self.__synapse_info.connector
        dynamics = self.__synapse_info.synapse_dynamics
        gen_size = sum((
            GeneratorData.BASE_SIZE,
            connector.gen_delay_params_size_in_bytes(
                self.__synapse_info.delays),
            connector.gen_weight_params_size_in_bytes(
                self.__synapse_info.weights),
            connector.gen_connector_params_size_in_bytes,
            dynamics.gen_matrix_params_size_in_bytes
        ))
        return gen_size * n_edge_vertices

    def can_generate_on_machine(self, single_addr):
        """ Determine if an app edge can be generated on the machine

        :param int single_addr:
        :rtype: bool
        """
        connector = self.__synapse_info.connector
        dynamics = self.__synapse_info.synapse_dynamics

        # If the whole app edge can be done with direct synapses, or there are
        # structural connections, don't generate on the machine
        if (self.__is_app_edge_direct(single_addr) or
                isinstance(dynamics, AbstractSynapseDynamicsStructural)):
            return False

        return (
            isinstance(connector, AbstractGenerateConnectorOnMachine) and
            connector.generate_on_machine(
                self.__synapse_info.weights, self.__synapse_info.delays) and
            isinstance(dynamics, AbstractGenerateOnMachine) and
            dynamics.generate_on_machine
        )

    def __is_app_edge_direct(self, single_addr):
        """ Determine if an app edge can use the direct matrix for all of its\
            synapse information
        """
        next_single_addr = single_addr
        for m_edge in self.__m_edges:
            matrix = self.__get_matrix(m_edge)
            is_direct, next_single_addr = matrix.is_direct(next_single_addr)
            if not is_direct:
                return False
        return True

    def set_info(self, all_syn_block_sz, app_key_info, delay_app_key_info,
                 routing_info, weight_scales, m_edges):
        self.__all_syn_block_sz = all_syn_block_sz
        self.__app_key_info = app_key_info
        self.__delay_app_key_info = delay_app_key_info
        self.__routing_info = routing_info
        self.__weight_scales = weight_scales
        self.__m_edges = m_edges

        # If there are delay and undelayed parts to this vertex, to use app
        # keys both parts must be able to use them to keep the indices
        # straight; also enforce that the number of machine edges is > 1 as
        # if there is only one, one-to-one connections might be possible, and
        # if not, there is no difference anyway.
        is_undelayed = bool(self.__max_row_info.undelayed_max_n_synapses)
        is_delayed = bool(self.__max_row_info.delayed_max_n_synapses)
        is_app_key = not is_undelayed or app_key_info is not None
        is_delay_app_key = not is_delayed or delay_app_key_info is not None
        self.__use_app_keys = (
            is_app_key and is_delay_app_key and len(m_edges) > 1)

    def write_matrix(self, spec, block_addr, single_addr, single_synapses):
        """ Write a synaptic matrix from host
        """
        undelayed_matrix_data = list()
        delayed_matrix_data = list()
        for m_edge in self.__m_edges:

            # Get a synaptic matrix for each machine edge
            matrix = self.__get_matrix(m_edge)
            row_data, delay_row_data = matrix.get_row_data()
            self.__update_connection_holders(row_data, delay_row_data, m_edge)

            if self.__use_app_keys:
                # If there is an app_key, save the data to be written later
                undelayed_matrix_data.append((m_edge, row_data))
                delayed_matrix_data.append((m_edge, delay_row_data))
            else:
                # If no app keys, write the data as normal
                block_addr, single_addr = matrix.write_machine_matrix(
                    spec, block_addr, single_synapses, single_addr,
                    row_data)
                block_addr = matrix.write_delayed_machine_matrix(
                    spec, block_addr, delay_row_data)

        # If there is an app key, add a single matrix
        if self.__use_app_keys:
            block_addr = self.__write_app_matrix(
                spec, block_addr, undelayed_matrix_data)
            block_addr = self.__write_delay_app_matrix(
                spec, block_addr, delayed_matrix_data)

        return block_addr, single_addr

    def __write_app_matrix(self, spec, block_addr, matrix_data):
        """ Write a matrix for a whole incoming application vertex as one
        """

        # If there are no synapses, just write an invalid pop table entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__add_invalid_entry(self.__app_key_info)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__update_master_pop_table(
            block_addr, self.__max_row_info.undelayed_max_words,
            self.__app_key_info)
        self.__syn_mat_offset = block_addr

        # Write all the row data for each machine vertex one after the other.
        # Implicit assumption that no machine-level row_data is ever empty;
        # this must be true in the current code, because the row length is
        # fixed for all synaptic matrices from the same source application
        # vertex
        for m_edge, row_data in matrix_data:
            size = (self.__max_row_info.undelayed_max_bytes *
                    m_edge.pre_vertex.vertex_slice.n_atoms)
            row_data_size = len(row_data) * BYTES_PER_WORD
            if row_data_size != size:
                raise Exception("Data incorrect size: {} instead of {}".format(
                    row_data_size, size))
            spec.write_array(row_data)
            block_addr = self.__next_addr(block_addr, size)

        return block_addr

    def __write_delay_app_matrix(self, spec, block_addr, matrix_data):
        """ Write a delay matrix for a whole incoming application vertex as one
        """

        # If there are no synapses, just write an invalid pop table entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__add_invalid_entry(self.__delay_app_key_info)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__update_master_pop_table(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info)
        self.__delay_syn_mat_offset = block_addr

        # Write all the row data for each machine vertex one after the other.
        # Implicit assumption that no machine-level row_data is ever empty;
        # this must be true in the current code, because the row length is
        # fixed for all synaptic matrices from the same source application
        # vertex
        for _, pre_slice, row_data in matrix_data:
            n_rows = pre_slice.n_atoms * self.__app_edge.n_delay_stages
            size = self.__max_row_info.delayed_max_bytes * n_rows
            row_data_size = len(row_data) * BYTES_PER_WORD
            if size != row_data_size:
                raise Exception("Data incorrect size: {} instead of {}".format(
                    row_data_size, size))
            spec.write_array(row_data)
            block_addr = self.__next_addr(block_addr, size)

        return block_addr

    def write_on_chip_matrix_data(self, generator_data, block_addr):
        """ Prepare to write a matrix using an on-chip generator
        """

        # Reserve the space in the matrix for an application-level key,
        # and tell the pop table
        (block_addr, syn_addr, del_addr, syn_max_addr,
         del_max_addr) = self.__reserve_app_blocks(block_addr)

        # Go through the edges of the application edge and write data for the
        # generator; this has to be done on a machine-edge basis to avoid
        # overloading the generator, even if an application matrix is generated
        for m_edge in self.__m_edges:
            matrix = self.__get_matrix(m_edge)

            if self.__use_app_keys:
                syn_addr, syn_mat_offset = matrix.next_app_on_chip_address(
                    syn_addr, syn_max_addr)
                del_addr, d_mat_offset = matrix.next_app_delay_on_chip_address(
                    del_addr, del_max_addr)
            else:
                block_addr, syn_mat_offset = matrix.next_on_chip_address(
                    block_addr)
                block_addr, d_mat_offset = matrix.next_delay_on_chip_address(
                    block_addr)

            # Create the generator data and note it exists for this post vertex
            # Note generator data is written per machine-edge even when a whole
            # application vertex matrix exists, because these are just appended
            # to each other in the latter case; this makes it easier to
            # generate since it is still doing it in chunks, so less local
            # memory is needed.
            generator_data.append(matrix.get_generator_data(
                syn_mat_offset, d_mat_offset))
        return block_addr

    def __reserve_app_blocks(self, block_addr):
        """ Reserve blocks for a whole-application-vertex matrix if possible,\
            and tell the master population table
        """
        if not self.__use_app_keys:
            return (block_addr, _SYN_REGION_UNUSED, _SYN_REGION_UNUSED, None,
                    None)

        is_undelayed = bool(self.__max_row_info.undelayed_max_n_synapses)
        is_delayed = bool(self.__max_row_info.delayed_max_n_synapses)

        syn_block_addr = _SYN_REGION_UNUSED
        syn_max_addr = None
        if is_undelayed:
            syn_block_addr = block_addr
            block_addr = self.__reserve_mpop_block(block_addr)
            syn_max_addr = block_addr
        else:
            self.__add_invalid_entry(self.__app_key_info)

        delay_block_addr = _SYN_REGION_UNUSED
        delay_max_addr = None
        if is_delayed:
            delay_block_addr = block_addr
            block_addr = self.__reserve_delay_mpop_block(block_addr)
            delay_max_addr = block_addr
        else:
            self.__add_invalid_entry(self.__delay_app_key_info)

        return (block_addr, syn_block_addr, delay_block_addr, syn_max_addr,
                delay_max_addr)

    def __reserve_mpop_block(self, block_addr):
        """ Reserve a block in the master population table and check it hasn't\
            overrun the allocation
        """
        block_addr = self.__poptable.get_next_allowed_address(
            block_addr)
        index = self.__poptable.update_master_population_table(
            block_addr, self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons)
        self.__update_synapse_index(index)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr

    def __reserve_delay_mpop_block(self, block_addr):
        """ Reserve a block in the master population table and check it hasn't\
            overrun the allocation
        """
        block_addr = self.__poptable.get_next_allowed_address(
            block_addr)
        index = self.__poptable.update_master_population_table(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info.key_and_mask,
            self.__delay_app_key_info.core_mask,
            self.__delay_app_key_info.core_shift,
            self.__delay_app_key_info.n_neurons)
        self.__update_synapse_index(index)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr

    def __update_connection_holders(self, data, delayed_data, machine_edge):
        for conn_holder in self.__synapse_info.pre_run_connection_holders:
            conn_holder.add_connections(
                self.__synapse_io.read_all_synapses(
                    data, delayed_data, self.__synapse_info,
                    self.__n_synapse_types, self.__weight_scales,
                    machine_edge, self.__max_row_info))

    def __update_master_pop_table(self, block_addr, max_words, key_info):
        index = self.__poptable.update_master_population_table(
            block_addr, max_words, key_info.key_and_mask, key_info.core_mask,
            key_info.core_shift, key_info.n_neurons)
        self.__update_synapse_index(index)

    def __add_invalid_entry(self, key_info):
        index = self.__poptable.add_invalid_entry(
            key_info.key_and_mask, key_info.core_mask, key_info.core_shift,
            key_info.n_neurons)
        self.__update_synapse_index(index)

    def __next_addr(self, block_addr, size):
        next_addr = block_addr + size
        if next_addr > self.__all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} "
                .format(next_addr, self.__all_syn_block_sz))
        return next_addr

    def __update_synapse_index(self, index):
        """ Update the index of a synapse, checking it matches against indices\
            for other synapse_info for the same edge
        """
        if self.__index is None:
            self.__index = index
        elif self.__index != index:
            # This should never happen as things should be aligned over all
            # machine vertices, but check just in case!
            raise Exception(
                "Index of " + self.__synapse_info + " has changed!")

    def get_connections(self, transceiver, placement):
        synapses_address = locate_memory_region_for_placement(
            placement, self.__synaptic_matrix_region, transceiver)
        single_address = (locate_memory_region_for_placement(
            placement, self.__direct_matrix_region, transceiver) +
            BYTES_PER_WORD)
        if self.__use_app_keys:
            return self.__read_connections(
                transceiver, placement, synapses_address)

        connections = list()
        for m_edge in self.__m_edges:
            matrix = self.__get_matrix(m_edge)
            connections.extend(matrix.read_connections(
                transceiver, placement, synapses_address, single_address))
        return connections

    def clear_connection_cache(self):
        self.__received_block = None
        self.__delay_received_block = None
        for matrix in itervalues(self.__matrices):
            matrix.clear_connection_cache()

    def read_generated_connection_holders(self, transceiver, placement):
        if self.__synapse_info.pre_run_connection_holders:
            connections = self.get_connections(transceiver, placement)
            for holder in self.__synapse_info.pre_run_connection_holders:
                holder.add_connections(connections)

    def __read_connections(self, transceiver, placement, synapses_address):
        pre_slice = Slice(0, self.__app_edge.pre_vertex.n_atoms + 1)
        machine_time_step = globals_variables.get_simulator().machine_time_step
        connections = list()

        if self.__syn_mat_offset is not None:
            block = self.__get_block(transceiver, placement, synapses_address)
            connections.append(self.__synapse_io.read_some_synapses(
                self.__synapse_info, pre_slice, self.__post_vertex_slice,
                self.__max_row_info.undelayed_max_words,
                self.__n_synapse_types, self.__weight_scales[placement], block,
                machine_time_step, delayed=False))

        if self.__delay_syn_mat_offset is not None:
            block = self.__get_delay_block(
                transceiver, placement, synapses_address)
            connections.append(self.__synapse_io.read_some_synapses(
                self.__synapse_info, pre_slice, self.__post_vertex_slice,
                self.__max_row_info.delayed_max_words, self.__n_synapse_types,
                self.__weight_scales[placement], block,
                machine_time_step, delayed=True))

        return connections

    def __get_block(self, transceiver, placement, synapses_address):
        if self.__received_block is not None:
            return self.__received_block
        address = self.__syn_mat_offset + synapses_address
        block = transceiver.read_memory(
            placement.x, placement.y, address, self.__matrix_size)
        self.__received_block = block
        return block

    def __get_delayed_block(self, transceiver, placement, synapses_address):
        if self.__delay_received_block is not None:
            return self.__delay_received_block
        address = self.__delay_syn_mat_offset + synapses_address
        block = transceiver.read_memory(
            placement.x, placement.y, address, self.__delay_matrix_size)
        self.__received_block = block
        return block

    def get_index(self, machine_edge):
        if self.__index is not None:
            return self.__index
        matrix = self.__get_matrix(machine_edge)
        return matrix.index
