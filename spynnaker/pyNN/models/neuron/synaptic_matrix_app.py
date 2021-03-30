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
import numpy

from pacman.model.graphs.common.slice import Slice
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spynnaker.pyNN.models.neuron.synaptic_matrix import SynapticMatrix
from spynnaker.pyNN.models.neuron.generator_data import (
    GeneratorData, SYN_REGION_UNUSED)


class SynapticMatrixApp(object):
    """ The synaptic matrix (and delay matrix if applicable) for an incoming
        app edge
    """

    __slots__ = [
        # The reader and writer of the synapses
        "__synapse_io",
        # The master population table
        "__poptable",
        # The synaptic info that these matrices are for
        "__synapse_info",
        # The application edge that these matrices are for
        "__app_edge",
        # The number of synapse types incoming
        "__n_synapse_types",
        # The maximum summed size of the "direct" or "single" matrices
        "__all_single_syn_sz",
        # The slice of the post vertex these matrices are for
        "__post_vertex_slice",
        # The ID of the synaptic matrix region
        "__synaptic_matrix_region",
        # The ID of the "direct" or "single" matrix region
        "__direct_matrix_region",
        # Any machine-level matrices for this application matrix
        "__matrices",
        # The maximum row length of delayed and undelayed matrices
        "__max_row_info",
        # The maximum summed size of the synaptic matrices
        "__all_syn_block_sz",
        # The application-level key information for the incoming edge
        "__app_key_info",
        # The application-level key information for the incoming delay edge
        "__delay_app_key_info",
        # All routing information
        "__routing_info",
        # The weight scaling used by each synapse type
        "__weight_scales",
        # The machine edges of the incoming application edges
        "__m_edges",
        # True if the application-level keys are safe to be used
        "__use_app_keys",
        # The expected size in bytes of a synaptic matrix
        "__matrix_size",
        # The expected size in bytes of a delayed synaptic matrix
        "__delay_matrix_size",
        # The number of atoms in the machine-level pre-vertices
        "__n_sub_atoms",
        # The number of machine edges expected for this application edge
        "__n_sub_edges",
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
        "__delay_received_block"
    ]

    def __init__(
            self, synapse_io, poptable, synapse_info, app_edge,
            n_synapse_types, all_single_syn_sz, post_vertex_slice,
            synaptic_matrix_region, direct_matrix_region):
        """

        :param SynapseIORowBased synapse_io: The reader and writer of synapses
        :param MasterPopTableAsBinarySearch poptable:
            The master population table
        :param SynapseInformation synapse_info:
            The projection synapse information
        :param ProjectionApplicationEdge app_edge:
            The projection application edge
        :param int n_synapse_types: The number of synapse types accepted
        :param int all_single_syn_sz:
            The space available for "direct" or "single" synapses
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post-vertex the matrix is for
        :param int synaptic_matrix_region:
            The region where synaptic matrices are stored
        :param int direct_matrix_region:
            The region where "direct" or "single" synapses are stored
        """
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
        n_delay_stages = 0
        if app_edge.delay_edge is not None:
            n_delay_stages = app_edge.delay_edge.pre_vertex.n_delay_stages
        self.__max_row_info = self.__synapse_io.get_max_row_info(
            synapse_info, self.__post_vertex_slice, n_delay_stages,
            self.__poptable,
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
        vertex = self.__app_edge.pre_vertex
        self.__n_sub_atoms = int(min(
            vertex.get_max_atoms_per_core(), vertex.n_atoms))
        self.__n_sub_edges = int(
            math.ceil(vertex.n_atoms / self.__n_sub_atoms))

        # These are computed during synaptic generation
        self.__syn_mat_offset = None
        self.__delay_syn_mat_offset = None
        self.__index = None
        self.__delay_index = None

        # These are stored when blocks are read
        self.__received_block = None
        self.__delay_received_block = None

    def __get_matrix(self, machine_edge):
        """ Get or create a matrix object

        :param ~pacman.model.graph.machine.MachineEdge machine_edge:
            The machine edge to get the matrix for
        :rtype: SynapticMatrix
        """
        if machine_edge in self.__matrices:
            return self.__matrices[machine_edge]

        r_info = self.__routing_info.get_routing_info_for_edge(machine_edge)
        delayed_r_info = None
        delayed_app_edge = machine_edge.app_edge.delay_edge
        if delayed_app_edge is not None:
            delayed_machine_edge = delayed_app_edge.get_machine_edge(
                machine_edge.pre_vertex, machine_edge.post_vertex)
            if delayed_machine_edge is not None:
                delayed_r_info = (
                    self.__routing_info.get_routing_info_for_edge(
                        delayed_machine_edge))
        matrix = SynapticMatrix(
            self.__synapse_io, self.__poptable, self.__synapse_info,
            machine_edge, self.__app_edge, self.__n_synapse_types,
            self.__max_row_info, r_info, delayed_r_info, self.__weight_scales,
            self.__all_syn_block_sz, self.__all_single_syn_sz)
        self.__matrices[machine_edge] = matrix
        return matrix

    def add_matrix_size(self, addr):
        """ Add the bytes required by the synaptic matrices

        :param int addr: The initial address
        :return: The final address after adding synapses
        :rtype: int
        """
        if self.__max_row_info.undelayed_max_n_synapses > 0:
            size = self.__n_sub_atoms * self.__max_row_info.undelayed_max_bytes
            for _ in range(self.__n_sub_edges):
                addr = self.__poptable.get_next_allowed_address(addr)
                addr += size
        return addr

    def add_delayed_matrix_size(self, addr):
        """ Add the bytes required by the delayed synaptic matrices

        :param int addr: The initial address
        :return: The final address after adding synapses
        :rtype: int
        """
        if self.__max_row_info.delayed_max_n_synapses > 0:
            size = (self.__n_sub_atoms *
                    self.__max_row_info.delayed_max_bytes *
                    self.__app_edge.n_delay_stages)
            for _ in range(self.__n_sub_edges):
                addr = self.__poptable.get_next_allowed_address(addr)
                addr += size
        return addr

    @property
    def generator_info_size(self):
        """ The number of bytes required by the generator information

        :rtype: int
        """
        if not self.__synapse_info.may_generate_on_machine():
            return 0

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
        return gen_size * self.__n_sub_edges

    def can_generate_on_machine(self, single_addr):
        """ Determine if an app edge can be generated on the machine

        :param int single_addr:
            The address for "direct" or "single" synapses so far
        :rtype: bool
        """
        return (
            self.__synapse_info.may_generate_on_machine() and
            not self.__is_app_edge_direct(single_addr))

    def __is_app_edge_direct(self, single_addr):
        """ Determine if an app edge can use the direct matrix for all of its\
            synapse information

        :param int single_addr:
            The address for "direct" or "single" synapses so far
        :rtype: bool
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
        """ Set extra information that isn't necessarily available when the
            class is created.

        :param int all_syn_block_sz:
            The space available for all synaptic matrices on the core
        :param _AppKeyInfo app_key_info:
            Application-level routing key information for undelayed vertices
        :param _AppKeyInfo delay_app_key_info:
            Application-level routing key information for delayed vertices
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            Routing key information for all incoming edges
        :param list(float) weight_scales:
            Weight scale for each synapse edge
        :param list(~pacman.model.graphs.machine.MachineEdge) m_edges:
            The machine edges incoming to this vertex
        """
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

    def write_matrix(
            self, spec, block_addr, single_addr, single_synapses,
            machine_time_step):
        """ Write a synaptic matrix from host

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param int single_addr:
            The address in the "direct" or "single" matrix to start at
        :param list(int) single_synapses:
            A list of "direct" or "single" synapses to write to
        :param float machine_time_step: the simulation machine time step
        :return: The updated block_addr and single_addr
        :rtype: tuple(int, int)
        """
        undelayed_matrix_data = list()
        delayed_matrix_data = list()
        for m_edge in self.__m_edges:

            # Get a synaptic matrix for each machine edge
            matrix = self.__get_matrix(m_edge)
            row_data, delay_row_data = matrix.get_row_data(machine_time_step)
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

        :param DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param matrix_data:
            The data for each machine edge to be combined into a single matrix
        :type matrix_data:
            list(~pacman.model.graphs.machine.MachineEdge, ~numpy.ndarray)
        :return: The updated block address
        :rtype: int
        """
        # If there is no routing info, don't write anything
        if self.__app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = self.__poptable.add_invalid_entry(
                self.__app_key_info.key_and_mask)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__index = self.__poptable.add_application_entry(
            block_addr,  self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons)
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

        :param DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param matrix_data:
            The data for each machine edge to be combined into a single matrix
        :type matrix_data:
            list(~pacman.model.graphs.machine.MachineEdge, ~numpy.ndarray)
        :return: The updated block address
        :rtype: int
        """
        # If there is no routing info, don't write anything
        if self.__delay_app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = self.__poptable.add_invalid_entry(
                self.__delay_app_key_info.key_and_mask)
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

        # Write all the row data for each machine vertex one after the other.
        # Implicit assumption that no machine-level row_data is ever empty;
        # this must be true in the current code, because the row length is
        # fixed for all synaptic matrices from the same source application
        # vertex
        for m_edge, row_data in matrix_data:
            size = (self.__max_row_info.delayed_max_bytes *
                    m_edge.pre_vertex.vertex_slice.n_atoms *
                    self.__app_edge.n_delay_stages)
            row_data_size = len(row_data) * BYTES_PER_WORD
            if size != row_data_size:
                raise Exception("Data incorrect size: {} instead of {}".format(
                    row_data_size, size))
            spec.write_array(row_data)
            block_addr = self.__next_addr(block_addr, size)

        return block_addr

    def write_on_chip_matrix_data(
            self, generator_data, block_addr, machine_time_step):
        """ Prepare to write a matrix using an on-chip generator

        :param list(GeneratorData) generator_data: List of data to add to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param float machine_time_step: the sim machine time step
        :return: The updated block address
        :rtype: int
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
            max_delay_per_stage = (
                m_edge.post_vertex.app_vertex.splitter.max_support_delay())

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
                syn_mat_offset, d_mat_offset, max_delay_per_stage,
                machine_time_step))
        return block_addr

    def __reserve_app_blocks(self, block_addr):
        """ Reserve blocks for a whole-application-vertex matrix if possible,
            and tell the master population table

        :param int block_addr:
            The address in the synaptic matrix region to start at
        :return: The updated block address, the synaptic matrix address,
            the delayed synaptic matrix address,
            the maximum synaptic matrix address,
            and the maximum delayed synaptic matrix address
        :rtype: int, int, int, int, int
        """
        if not self.__use_app_keys:
            return (block_addr, SYN_REGION_UNUSED, SYN_REGION_UNUSED, None,
                    None)

        block_addr, syn_block_addr, syn_max_addr = \
            self.__reserve_mpop_block(block_addr)
        block_addr, delay_block_addr, delay_max_addr = \
            self.__reserve_delay_mpop_block(block_addr)

        return (block_addr, syn_block_addr, delay_block_addr, syn_max_addr,
                delay_max_addr)

    def __reserve_mpop_block(self, block_addr):
        """ Reserve a block in the master population table for an undelayed\
            matrix

        :param int block_addr:
            The address in the synaptic matrix region to start at
        :return: The updated block address, the reserved address,
            and the maximum address
        :rtype: int, int, int
        """
        # If there is no routing information, don't reserve anything
        if self.__app_key_info is None:
            return block_addr, SYN_REGION_UNUSED, None

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = self.__poptable.add_invalid_entry(
                self.__app_key_info.key_and_mask)
            return block_addr, SYN_REGION_UNUSED, None

        block_addr = self.__poptable.get_next_allowed_address(block_addr)
        self.__index = self.__poptable.add_application_entry(
            block_addr, self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr, self.__syn_mat_offset, block_addr

    def __reserve_delay_mpop_block(self, block_addr):
        """ Reserve a block in the master population table for a delayed matrix

        :param int block_addr:
            The address in the synaptic matrix region to start at
        :return: The updated block address, the reserved address,
            and the maximum address
        :rtype: int, int, int
        """
        # If there is no routing information don't reserve anything
        if self.__delay_app_key_info is None:
            return block_addr, SYN_REGION_UNUSED, None

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = self.__poptable.add_invalid_entry(
                self.__delay_app_key_info.key_and_mask)
            return block_addr, SYN_REGION_UNUSED, None

        block_addr = self.__poptable.get_next_allowed_address(block_addr)
        self.__delay_index = self.__poptable.add_application_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info.key_and_mask,
            self.__delay_app_key_info.core_mask,
            self.__delay_app_key_info.core_shift,
            self.__delay_app_key_info.n_neurons)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr, self.__delay_syn_mat_offset, block_addr

    def __update_connection_holders(self, data, delayed_data, machine_edge):
        """ Fill in connections in the connection holders as they are created

        :param ~numpy.ndarray data: The row data created
        :param ~numpy.ndarray delayed_data: The delayed row data created
        :param ~pacman.model.graphs.machine.MachineEdge machine_edge:
            The machine edge the connections are for
        """
        for conn_holder in self.__synapse_info.pre_run_connection_holders:
            conn_holder.add_connections(
                self.__synapse_io.read_all_synapses(
                    data, delayed_data, self.__synapse_info,
                    self.__n_synapse_types, self.__weight_scales,
                    machine_edge, self.__max_row_info))

    def __next_addr(self, block_addr, size):
        """ Get the next address after a block, checking it is in range

        :param int block_addr: The address of the start of the block
        :param int size: The size of the block in bytes
        :return: The updated address
        :rtype: int
        :raises Exception: If the updated address is out of range
        """
        next_addr = block_addr + size
        if next_addr > self.__all_syn_block_sz:
            raise Exception(
                "Too much synaptic memory has been written: {} of {} "
                .format(next_addr, self.__all_syn_block_sz))
        return next_addr

    def __update_synapse_index(self, index):
        """ Update the index of a synapse, checking it matches against indices\
            for other synapse_info for the same edge

        :param index: The index to set
        :raises Exception: If the index doesn't match the currently set index
        """
        if self.__index is None:
            self.__index = index
        elif self.__index != index:
            # This should never happen as things should be aligned over all
            # machine vertices, but check just in case!
            raise Exception(
                "Index of " + self.__synapse_info + " has changed!")

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
        # This might happen if the matrix is never actually generated
        if self.__m_edges is None:
            return []
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
        """ Clear saved connections
        """
        self.__received_block = None
        self.__delay_received_block = None
        for matrix in self.__matrices.values():
            matrix.clear_connection_cache()

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
        pre_slice = Slice(0, self.__app_edge.pre_vertex.n_atoms + 1)
        machine_time_step = globals_variables.get_simulator().machine_time_step
        connections = list()

        if self.__syn_mat_offset is not None:
            block = self.__get_block(transceiver, placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(self.__synapse_io.convert_to_connections(
                self.__synapse_info, pre_slice, self.__post_vertex_slice,
                self.__max_row_info.undelayed_max_words,
                self.__n_synapse_types, self.__weight_scales, block,
                machine_time_step, False, splitter.max_support_delay()))

        if self.__delay_syn_mat_offset is not None:
            block = self.__get_delayed_block(
                transceiver, placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(self.__synapse_io.convert_to_connections(
                self.__synapse_info, pre_slice, self.__post_vertex_slice,
                self.__max_row_info.delayed_max_words, self.__n_synapse_types,
                self.__weight_scales, block, machine_time_step, True,
                splitter.max_support_delay()))

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

    def get_index(self, machine_edge):
        """ Get the index in the master population table of the matrix for a
            machine edge

        :param ~pacman.model.graph.machine.MachineEdge machine_edge:
            The edge to get the index for
        :rtype: int
        """
        # If there is an app-level index, it will be the same for all machine
        # edges
        if self.__index is not None:
            return self.__index
        matrix = self.__get_matrix(machine_edge)
        return matrix.index

    def get_delay_index(self, machine_edge):
        """ Get the index in the master population table of the delayed matrix
            for a machine edge

        :param ~pacman.model.graph.machine.MachineEdge machine_edge:
            The edge to get the index for
        :rtype: int
        """
        # If there is an app-level index, it will be the same for all machine
        # edges
        if self.__delay_index is not None:
            return self.__delay_index
        matrix = self.__get_matrix(machine_edge)
        return matrix.delay_index
