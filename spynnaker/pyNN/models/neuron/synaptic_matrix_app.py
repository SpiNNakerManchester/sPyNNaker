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

from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spynnaker.pyNN.data import SpynnakerDataView
from .generator_data import GeneratorData
from .synapse_io import read_all_synapses, convert_to_connections, get_synapses
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)


class SynapticMatrixApp(object):
    """
    The synaptic matrix (and delay matrix if applicable) for an incoming
    app edge.
    """

    # pylint: disable=unused-private-member
    # https://github.com/SpiNNakerManchester/sPyNNaker/issues/1201
    __slots__ = [
        # The synaptic info that these matrices are for
        "__synapse_info",
        # The application edge that these matrices are for
        "__app_edge",
        # The number of synapse types incoming
        "__n_synapse_types",
        # The ID of the synaptic matrix region
        "__synaptic_matrix_region",
        # The maximum row length of delayed and undelayed matrices
        "__max_row_info",
        # The maximum summed size of the synaptic matrices
        "__all_syn_block_sz",
        # The application-level key information for the incoming edge
        "__app_key_info",
        # The application-level key information for the incoming delay edge
        "__delay_app_key_info",
        # The weight scaling used by each synapse type
        "__weight_scales",
        # The expected size in bytes of a synaptic matrix
        "__matrix_size",
        # The expected size in bytes of a delayed synaptic matrix
        "__delay_matrix_size",
        # The offset of the undelayed synaptic matrix in the region
        "__syn_mat_offset",
        # The offset of the delayed synaptic matrix in the region
        "__delay_syn_mat_offset",
        # The index of the synaptic matrix within the master population table
        "__index",
        # The index of the delayed synaptic matrix within the master population
        # table
        "__delay_index",
        # The number of bits to use for neuron IDs
        "__max_atoms_per_core"
    ]

    def __init__(
            self, synapse_info, app_edge, n_synapse_types,
            synaptic_matrix_region, max_atoms_per_core, all_syn_block_sz,
            app_key_info, delay_app_key_info, weight_scales):
        """
        :param SynapseInformation synapse_info:
            The projection synapse information
        :param ProjectionApplicationEdge app_edge:
            The projection application edge
        :param int n_synapse_types: The number of synapse types accepted
        :param int synaptic_matrix_region:
            The region where synaptic matrices are stored
        :param int all_syn_block_sz:
            The space available for all synaptic matrices on the core
        :param _AppKeyInfo app_key_info:
            Application-level routing key information for undelayed vertices
        :param _AppKeyInfo delay_app_key_info:
            Application-level routing key information for delayed vertices
        :param list(float) weight_scales:
            Weight scale for each synapse edge
        """
        self.__synapse_info = synapse_info
        self.__app_edge = app_edge
        self.__n_synapse_types = n_synapse_types
        self.__synaptic_matrix_region = synaptic_matrix_region
        self.__max_atoms_per_core = max_atoms_per_core

        # Calculate the max row info for this edge
        self.__max_row_info = self.__app_edge.post_vertex.get_max_row_info(
            synapse_info, max_atoms_per_core, app_edge)

        self.__all_syn_block_sz = all_syn_block_sz
        self.__app_key_info = app_key_info
        self.__delay_app_key_info = delay_app_key_info
        self.__weight_scales = weight_scales

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
        self.__delay_index = None

    @property
    def gen_size(self):
        max_row_length = max(
            self.__max_row_info.undelayed_max_bytes,
            self.__max_row_info.delayed_max_bytes)
        return (max_row_length * self.__app_edge.pre_vertex.n_atoms *
                (self.__app_edge.n_delay_stages + 1))

    def reserve_matrices(self, block_addr, poptable):
        """
        Allocate the master pop table entries for the blocks.

        :param int block_addr: Where the allocation can start from
        :param MasterPopTableAsBinarySearch poptable:
            The master population table
        :return: Where the next allocation can start from
        :rtype: int
        """
        block_addr = self.__reserve_app_matrix(block_addr, poptable)
        block_addr = self.__reserve_delay_app_matrix(block_addr, poptable)
        return block_addr

    def __reserve_app_matrix(self, block_addr, poptable):
        """
        Reserve space for the matrix in the master pop table.

        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param MasterPopTableAsBinarySearch poptable:
            The master population table
        :return: The updated block address
        :rtype: int
        """
        # If there is no routing info, don't write anything
        if self.__app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = poptable.add_invalid_application_entry(
                self.__app_key_info.key_and_mask,
                self.__app_key_info.core_mask, self.__app_key_info.core_shift,
                self.__app_key_info.n_neurons,
                self.__app_key_info.n_colour_bits)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = poptable.get_next_allowed_address(block_addr)
        self.__index = poptable.add_application_entry(
            block_addr,  self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons,
            self.__app_key_info.n_colour_bits)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr

    def __reserve_delay_app_matrix(self, block_addr, poptable):
        """
        Reserve space in the master pop table for a delayed matrix.

        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param MasterPopTableAsBinarySearch poptable:
            The master population table
        :return: The updated block address
        :rtype: int
        """
        # If there is no routing info, don't write anything
        if self.__delay_app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = poptable.add_invalid_application_entry(
                self.__delay_app_key_info.key_and_mask,
                self.__delay_app_key_info.core_mask,
                self.__delay_app_key_info.core_shift,
                self.__delay_app_key_info.n_neurons,
                self.__delay_app_key_info.n_colour_bits)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = poptable.get_next_allowed_address(block_addr)
        self.__delay_index = poptable.add_application_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info.key_and_mask,
            self.__delay_app_key_info.core_mask,
            self.__delay_app_key_info.core_shift,
            self.__delay_app_key_info.n_neurons,
            self.__delay_app_key_info.n_colour_bits)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr

    def __next_addr(self, block_addr, size):
        """
        Get the next address after a block, checking it is in range.

        :param int block_addr: The address of the start of the block
        :param int size: The size of the block in bytes
        :param int max_addr: The maximum allowed address
        :return: The updated address
        :rtype: int
        :raises Exception: If the updated address is out of range
        """
        next_addr = block_addr + size
        if next_addr > self.__all_syn_block_sz:
            raise ValueError(
                "Too much synaptic memory has been written: "
                f"{next_addr} of {self.__all_syn_block_sz} ")
        return next_addr

    def write_matrix(self, spec, post_vertex_slice):
        """
        Write a synaptic matrix from host.

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post-vertex the matrix is for
        """
        row_data, delay_row_data = self.__get_row_data(post_vertex_slice)
        self.__update_connection_holders(
            row_data, delay_row_data, post_vertex_slice)
        if self.__syn_mat_offset is not None:
            spec.set_write_pointer(self.__syn_mat_offset)
            spec.write_array(row_data)
        if self.__delay_syn_mat_offset is not None:
            spec.set_write_pointer(self.__delay_syn_mat_offset)
            spec.write_array(delay_row_data)

    def __get_row_data(self, post_vertex_slice):
        """
        Generate the row data for a synaptic matrix from the description.

        :return: The data and the delayed data
        :rtype: tuple(~numpy.ndarray or None, ~numpy.ndarray or None)
        """
        # Get the actual connections
        post_slices =\
            self.__app_edge.post_vertex.splitter.get_in_coming_slices()
        connections = self.__synapse_info.connector.create_synaptic_block(
            post_slices, post_vertex_slice,
            self.__synapse_info.synapse_type, self.__synapse_info)

        # Get the row data; note that we use the availability of the routing
        # keys to decide if we should actually generate any data; this is
        # because a single edge might have been filtered
        (row_data, delayed_row_data) = get_synapses(
            connections, self.__synapse_info, self.__app_edge.n_delay_stages,
            self.__n_synapse_types, self.__weight_scales, self.__app_edge,
            post_vertex_slice, self.__max_row_info,
            self.__app_key_info is not None,
            self.__delay_app_key_info is not None, self.__max_atoms_per_core)

        # Set connections for structural plasticity
        if isinstance(self.__synapse_info.synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            self.__synapse_info.synapse_dynamics.set_connections(
                connections, post_vertex_slice, self.__app_edge,
                self.__synapse_info)
        if self.__app_edge.delay_edge is None and len(delayed_row_data) != 0:
            raise ValueError(
                "Found delayed source IDs but no delay "
                f"edge for {self.__app_edge.label}")

        return row_data, delayed_row_data

    def __update_connection_holders(
            self, data, delayed_data, post_vertex_slice):
        """
        Fill in connections in the connection holders as they are created.

        :param ~numpy.ndarray data: The row data created
        :param ~numpy.ndarray delayed_data: The delayed row data created
        :param ~pacman.model.graphs.machine.MachineVertex m_vertex:
            The machine edge the connections are for
        """
        post_splitter = self.__app_edge.post_vertex.splitter
        post_vertex_max_delay_ticks = post_splitter.max_support_delay()
        for conn_holder in self.__synapse_info.pre_run_connection_holders:
            conn_holder.add_connections(
                read_all_synapses(
                    data, delayed_data, self.__synapse_info,
                    self.__n_synapse_types, self.__weight_scales,
                    post_vertex_slice, self.__app_edge.pre_vertex.n_atoms,
                    post_vertex_max_delay_ticks,
                    self.__max_row_info, self.__max_atoms_per_core))

    def get_generator_data(self):
        """
        Prepare to write a matrix using an on-chip generator.

        :return: The data to generate with
        :rtype: GeneratorData
        """
        pre_vertex = self.__app_edge.pre_vertex
        max_pre_atoms_per_core = min(pre_vertex.n_atoms,
                                     pre_vertex.get_max_atoms_per_core())
        return GeneratorData(
            self.__syn_mat_offset, self.__delay_syn_mat_offset,
            self.__app_edge, self.__synapse_info, self.__max_row_info,
            max_pre_atoms_per_core, self.__max_atoms_per_core)

    def get_connections(self, placement):
        """
        Get the connections for this matrix from the machine.

        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        :return: A list of arrays of connections, each with dtype
            :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
        :rtype: ~numpy.ndarray
        """
        synapses_address = locate_memory_region_for_placement(
            placement, self.__synaptic_matrix_region)
        return self.__read_connections(placement, synapses_address)

    def read_generated_connection_holders(self, placement):
        """
        Read any pre-run connection holders after data has been generated.

        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        """
        if self.__synapse_info.pre_run_connection_holders:
            connections = self.get_connections(placement)
            if connections:
                connections = numpy.concatenate(connections)
                for holder in self.__synapse_info.pre_run_connection_holders:
                    holder.add_connections(connections)

    def __read_connections(self, placement, synapses_address):
        """
        Read connections from an address on the machine.

        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :return: A list of arrays of connections, each with dtype
            :py:attr:`~.AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE`
        :rtype: ~numpy.ndarray
        """
        connections = list()

        if self.__syn_mat_offset is not None:
            block = self.__get_block(placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(convert_to_connections(
                self.__synapse_info, placement.vertex.vertex_slice,
                self.__app_edge.pre_vertex.n_atoms,
                self.__max_row_info.undelayed_max_words,
                self.__n_synapse_types, self.__weight_scales, block,
                False, splitter.max_support_delay(),
                self.__max_atoms_per_core))

        if self.__delay_syn_mat_offset is not None:
            block = self.__get_delayed_block(placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(convert_to_connections(
                self.__synapse_info, placement.vertex.vertex_slice,
                self.__app_edge.pre_vertex.n_atoms,
                self.__max_row_info.delayed_max_words, self.__n_synapse_types,
                self.__weight_scales, block, True,
                splitter.max_support_delay(), self.__max_atoms_per_core))

        return connections

    def __get_block(self, placement, synapses_address):
        """
        Get a block of data for undelayed synapses.

        :param Placement placement: Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :rtype: bytearray
        """
        address = self.__syn_mat_offset + synapses_address
        block = SpynnakerDataView.read_memory(
            placement.x, placement.y, address, self.__matrix_size)
        return block

    def __get_delayed_block(self, placement, synapses_address):
        """
        Get a block of data for delayed synapses.

        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :rtype: bytearray
        """
        address = self.__delay_syn_mat_offset + synapses_address
        block = SpynnakerDataView.read_memory(
            placement.x, placement.y, address, self.__delay_matrix_size)
        return block

    def get_index(self):
        """
        Get the index in the master population table of the matrix.

        :param ~pacman.model.graphs.machine.MachineVertex m_vertex:
            The source machine vertex
        :rtype: int
        """
        return self.__index
