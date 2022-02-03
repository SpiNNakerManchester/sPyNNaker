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

from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from .generator_data import GeneratorData, SYN_REGION_UNUSED
from .synapse_io import read_all_synapses, convert_to_connections, get_synapses
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)


class SynapticMatrixApp(object):
    """ The synaptic matrix (and delay matrix if applicable) for an incoming
        app edge
    """

    __slots__ = [
        # The master population table
        "__poptable",
        # The synaptic info that these matrices are for
        "__synapse_info",
        # The application edge that these matrices are for
        "__app_edge",
        # The number of synapse types incoming
        "__n_synapse_types",
        # The slice of the post vertex these matrices are for
        "__post_vertex_slice",
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
        # A cache of the received synaptic matrix
        "__received_block",
        # A cache of the received delayed synaptic matrix
        "__delay_received_block",
        # The number of bits to use for neuron IDs
        "__max_atoms_per_core"
    ]

    def __init__(
            self, poptable, synapse_info, app_edge, n_synapse_types,
            post_vertex_slice, synaptic_matrix_region, max_atoms_per_core):
        """

        :param MasterPopTableAsBinarySearch poptable:
            The master population table
        :param SynapseInformation synapse_info:
            The projection synapse information
        :param ProjectionApplicationEdge app_edge:
            The projection application edge
        :param int n_synapse_types: The number of synapse types accepted
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post-vertex the matrix is for
        :param int synaptic_matrix_region:
            The region where synaptic matrices are stored
        """
        self.__poptable = poptable
        self.__synapse_info = synapse_info
        self.__app_edge = app_edge
        self.__n_synapse_types = n_synapse_types
        self.__post_vertex_slice = post_vertex_slice
        self.__synaptic_matrix_region = synaptic_matrix_region
        self.__max_atoms_per_core = max_atoms_per_core

        # Calculate the max row info for this edge
        self.__max_row_info = self.__app_edge.post_vertex.get_max_row_info(
            synapse_info, max_atoms_per_core, app_edge)

        # These are set directly later
        self.__all_syn_block_sz = None
        self.__app_key_info = None
        self.__delay_app_key_info = None
        self.__weight_scales = None

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

        # These are stored when blocks are read
        self.__received_block = None
        self.__delay_received_block = None

    def set_info(self, all_syn_block_sz, app_key_info, delay_app_key_info,
                 weight_scales):
        """ Set extra information that isn't necessarily available when the
            class is created.

        :param int all_syn_block_sz:
            The space available for all synaptic matrices on the core
        :param _AppKeyInfo app_key_info:
            Application-level routing key information for undelayed vertices
        :param _AppKeyInfo delay_app_key_info:
            Application-level routing key information for delayed vertices
        :param list(float) weight_scales:
            Weight scale for each synapse edge
        """
        self.__all_syn_block_sz = all_syn_block_sz
        self.__app_key_info = app_key_info
        self.__delay_app_key_info = delay_app_key_info
        self.__weight_scales = weight_scales

    def __get_row_data(self):
        """ Generate the row data for a synaptic matrix from the description

        :return: The data and the delayed data
        :rtype: tuple(~numpy.ndarray or None, ~numpy.ndarray or None)
        """

        # Get the actual connections
        post_slices =\
            self.__app_edge.post_vertex.splitter.get_in_coming_slices()
        connections = self.__synapse_info.connector.create_synaptic_block(
            post_slices, self.__post_vertex_slice,
            self.__synapse_info.synapse_type, self.__synapse_info)

        # Get the row data; note that we use the availability of the routing
        # keys to decide if we should actually generate any data; this is
        # because a single edge might have been filtered
        (row_data, delayed_row_data) = get_synapses(
            connections, self.__synapse_info, self.__app_edge.n_delay_stages,
            self.__n_synapse_types, self.__weight_scales, self.__app_edge,
            self.__post_vertex_slice, self.__max_row_info,
            self.__app_key_info is not None,
            self.__delay_app_key_info is not None, self.__max_atoms_per_core)

        # Set connections for structural plasticity
        if isinstance(self.__synapse_info.synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            self.__synapse_info.synapse_dynamics.set_connections(
                connections, self.__post_vertex_slice, self.__app_edge,
                self.__synapse_info)
        if self.__app_edge.delay_edge is None and len(delayed_row_data) != 0:
            raise Exception(
                "Found delayed source IDs but no delay "
                "edge for {}".format(self.__app_edge.label))

        return row_data, delayed_row_data

    def write_matrix(self, spec, block_addr):
        """ Write a synaptic matrix from host

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :return: The updated block_addr
        :rtype: int
        """
        row_data, delay_row_data = self.__get_row_data()
        self.__update_connection_holders(row_data, delay_row_data)
        block_addr = self.__write_app_matrix(spec, block_addr, row_data)
        block_addr = self.__write_delay_app_matrix(spec, block_addr,
                                                   delay_row_data)
        return block_addr

    def __write_app_matrix(self, spec, block_addr, row_data):
        """ Write a matrix for a whole incoming application vertex as one

        :param DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param ~numpy.ndarray row_data:
            The data for the source application vertex
        :return: The updated block address
        :rtype: int
        """
        # If there is no routing info, don't write anything
        if self.__app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = self.__poptable.add_invalid_application_entry(
                self.__app_key_info.key_and_mask,
                self.__app_key_info.core_mask, self.__app_key_info.core_shift,
                self.__app_key_info.n_neurons)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__index = self.__poptable.add_application_entry(
            block_addr,  self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons)
        self.__syn_mat_offset = block_addr

        # Write the data
        spec.write_array(row_data)

        return block_addr

    def __write_delay_app_matrix(self, spec, block_addr, delay_row_data):
        """ Write a delay matrix for a whole incoming application vertex as one

        :param DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param ~numpy.ndarray delay_row_data:
            The data for the source application vertex
        :return: The updated block address
        :rtype: int
        """
        # If there is no routing info, don't write anything
        if self.__delay_app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = self.__poptable.add_invalid_application_entry(
                self.__delay_app_key_info.key_and_mask,
                self.__delay_app_key_info.core_mask,
                self.__delay_app_key_info.core_shift,
                self.__delay_app_key_info.n_neurons)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__delay_index = self.__poptable.add_application_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info.key_and_mask,
            self.__delay_app_key_info.core_mask,
            self.__delay_app_key_info.core_shift,
            self.__delay_app_key_info.n_neurons)
        self.__delay_syn_mat_offset = block_addr

        # Write the data
        spec.write_array(delay_row_data)

        return block_addr

    def write_on_chip_matrix_data(self, generator_data, block_addr):
        """ Prepare to write a matrix using an on-chip generator

        :param list(GeneratorData) generator_data: List of data to add to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :return: The updated block address
        :rtype: int
        """
        # Reserve the space in the matrix for an application-level key,
        # and tell the pop table

        block_addr, syn_block_addr = self.__reserve_mpop_block(block_addr)
        block_addr, d_block_addr = self.__reserve_delay_mpop_block(block_addr)
        generator_data.append(GeneratorData(
            syn_block_addr, d_block_addr, self.__app_edge, self.__synapse_info,
            self.__max_row_info, self.__max_atoms_per_core))
        return block_addr

    def __reserve_mpop_block(self, block_addr):
        """ Reserve a block in the master population table for an undelayed
            matrix

        :param int block_addr:
            The address in the synaptic matrix region to start at
        :return: The updated block address and the reserved address
        :rtype: int, int
        """
        # If there is no routing information, don't reserve anything
        if self.__app_key_info is None:
            return block_addr, SYN_REGION_UNUSED, None

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = self.__poptable.add_invalid_application_entry(
                self.__app_key_info.key_and_mask,
                self.__app_key_info.core_mask, self.__app_key_info.core_shift,
                self.__app_key_info.n_neurons)
            return block_addr, SYN_REGION_UNUSED

        block_addr = self.__poptable.get_next_allowed_address(block_addr)
        self.__index = self.__poptable.add_application_entry(
            block_addr, self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr, self.__syn_mat_offset

    def __reserve_delay_mpop_block(self, block_addr):
        """ Reserve a block in the master population table for a delayed matrix

        :param int block_addr:
            The address in the synaptic matrix region to start at
        :return: The updated block address and the reserved address
        :rtype: int, int
        """
        # If there is no routing information don't reserve anything
        if self.__delay_app_key_info is None:
            return block_addr, SYN_REGION_UNUSED

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = self.__poptable.add_invalid_application_entry(
                self.__delay_app_key_info.key_and_mask,
                self.__delay_app_key_info.core_mask,
                self.__delay_app_key_info.core_shift,
                self.__delay_app_key_info.n_neurons)
            return block_addr, SYN_REGION_UNUSED

        block_addr = self.__poptable.get_next_allowed_address(block_addr)
        self.__delay_index = self.__poptable.add_application_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info.key_and_mask,
            self.__delay_app_key_info.core_mask,
            self.__delay_app_key_info.core_shift,
            self.__delay_app_key_info.n_neurons)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr, self.__delay_syn_mat_offset

    def __update_connection_holders(self, data, delayed_data):
        """ Fill in connections in the connection holders as they are created

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
                    self.__app_edge.pre_vertex.n_atoms,
                    self.__post_vertex_slice, post_vertex_max_delay_ticks,
                    self.__max_row_info, self.__max_atoms_per_core))

    def __next_addr(self, block_addr, size, max_addr=None):
        """ Get the next address after a block, checking it is in range

        :param int block_addr: The address of the start of the block
        :param int size: The size of the block in bytes
        :param int max_addr: The maximum allowed address
        :return: The updated address
        :rtype: int
        :raises Exception: If the updated address is out of range
        """
        if not max_addr:
            max_addr = self.__all_syn_block_sz
        next_addr = block_addr + size
        if next_addr > max_addr:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} "
                .format(next_addr, max_addr))
        return next_addr

    def get_connections(self, transceiver, placement):
        """ Get the connections for this matrix from the machine

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the data from the machine
        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        :return: A list of arrays of connections, each with dtype
            AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE
        :rtype: ~numpy.ndarray
        """
        synapses_address = locate_memory_region_for_placement(
            placement, self.__synaptic_matrix_region, transceiver)
        return self.__read_connections(
            transceiver, placement, synapses_address)

    def clear_connection_cache(self):
        """ Clear saved connections
        """
        self.__received_block = None
        self.__delay_received_block = None

    def read_generated_connection_holders(self, transceiver, placement):
        """ Read any pre-run connection holders after data has been generated

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the data from the machine
        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        """
        if self.__synapse_info.pre_run_connection_holders:
            connections = self.get_connections(transceiver, placement)
            if connections:
                connections = numpy.concatenate(connections)
                for holder in self.__synapse_info.pre_run_connection_holders:
                    holder.add_connections(connections)
            self.clear_connection_cache()

    def __read_connections(self, transceiver, placement, synapses_address):
        """ Read connections from an address on the machine

        :param Transceiver transceiver: How to read the data from the machine
        :param Placement placement: Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :return: A list of arrays of connections, each with dtype
            AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE
        :rtype: ~numpy.ndarray
        """
        connections = list()

        if self.__syn_mat_offset is not None:
            block = self.__get_block(transceiver, placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(convert_to_connections(
                self.__synapse_info, self.__post_vertex_slice,
                self.__app_edge.pre_vertex.n_atoms,
                self.__max_row_info.undelayed_max_words,
                self.__n_synapse_types, self.__weight_scales, block,
                False, splitter.max_support_delay(),
                self.__max_atoms_per_core))

        if self.__delay_syn_mat_offset is not None:
            block = self.__get_delayed_block(
                transceiver, placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(convert_to_connections(
                self.__synapse_info, self.__post_vertex_slice,
                self.__app_edge.pre_vertex.n_atoms,
                self.__max_row_info.delayed_max_words, self.__n_synapse_types,
                self.__weight_scales, block, True,
                splitter.max_support_delay(), self.__max_atoms_per_core))

        return connections

    def __get_block(self, transceiver, placement, synapses_address):
        """ Get a block of data for undelayed synapses

        :param Transceiver transceiver: How to read the data from the machine
        :param Placement placement: Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :rtype: bytearray
        """
        if self.__received_block is not None:
            return self.__received_block
        address = self.__syn_mat_offset + synapses_address
        block = transceiver.read_memory(
            placement.x, placement.y, address, self.__matrix_size)
        self.__received_block = block
        return block

    def __get_delayed_block(self, transceiver, placement, synapses_address):
        """ Get a block of data for delayed synapses

        :param Transceiver transceiver: How to read the data from the machine
        :param Placement placement: Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :rtype: bytearray
        """
        if self.__delay_received_block is not None:
            return self.__delay_received_block
        address = self.__delay_syn_mat_offset + synapses_address
        block = transceiver.read_memory(
            placement.x, placement.y, address, self.__delay_matrix_size)
        self.__delay_received_block = block
        return block

    def get_index(self):
        """ Get the index in the master population table of the matrix

        :param ~pacman.model.graph.machine.MachineVertex m_vertex:
            The source machine vertex
        :rtype: int
        """
        return self.__index
