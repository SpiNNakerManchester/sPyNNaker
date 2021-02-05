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

from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsStatic
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)

from .generator_data import GeneratorData, SYN_REGION_UNUSED


class SynapticMatrix(object):
    """ Synaptic matrix/matrices for an incoming machine edge
    """

    __slots__ = [
        # The reader and writer of synaptic matrices
        "__synapse_io",
        # The master population table
        "__poptable",
        # The synapse info used to generate the matrices
        "__synapse_info",
        # The machine edge these matrices are for
        "__machine_edge",
        # The app edge of the machine edge
        "__app_edge",
        # The number of synapse types
        "__n_synapse_types",
        # The maximum row lengths of the matrices
        "__max_row_info",
        # The routing information for the undelayed edge
        "__routing_info",
        # The routing information for the delayed edge
        "__delay_routing_info",
        # The scale of the weights of each synapse type
        "__weight_scales",
        # The maximum summed size of the synaptic matrices
        "__all_syn_block_sz",
        # The maximum summed size of the "direct" or "single" matrices
        "__all_single_syn_sz",
        # The expected size of a synaptic matrix
        "__matrix_size",
        # The expected size of a delayed synaptic matrix
        "__delay_matrix_size",
        # The expected size of a "direct" or "single" matrix
        "__single_matrix_size",
        # The index of the matrix in the master population table
        "__index",
        # The index of the delayed matrix in the master population table
        "__delay_index",
        # The offset of the matrix within the synaptic region
        "__syn_mat_offset",
        # The offset of the delayed matrix within the synaptic region
        "__delay_syn_mat_offset",
        # Indicates if the matrix is a "direct" or "single" matrix
        "__is_single",
        # A cached version of a received synaptic matrix
        "__received_block",
        # A cached version of a received delayed synaptic matrix
        "__delay_received_block"
    ]

    def __init__(self, synapse_io, poptable, synapse_info, machine_edge,
                 app_edge, n_synapse_types, max_row_info, routing_info,
                 delay_routing_info, weight_scales, all_syn_block_sz,
                 all_single_syn_sz):
        """
        :param SynapseIORowBased synapse_io: The reader and writer of synapses
        :param MasterPopTableAsBinarySearch poptable:
            The master population table
        :param SynapseInformation synapse_info:
            The projection synapse information
        :param ~pacman.model.graphs.machine.MachineEdge machine_edge:
            The projection machine edge
        :param ProjectionApplicationEdge app_edge:
            The projection application edge
        :param int n_synapse_types: The number of synapse types accepted
        :param MaxRowInfo max_row_info: Maximum row length information
        :param ~pacman.model.routing_info.PartitionRoutingInfo routing_info:
            Routing information for the edge
        :param ~pacman.model.routing_info.PartitionRoutingInfo \
                delay_routing_info:
            Routing information for the delay edge if any
        :param list(float) weight_scales: Weight scale for each synapse type
        :param all_syn_block_sz:
            The space available for all synaptic matrices
        :param int all_single_syn_sz:
            The space available for "direct" or "single" synapses
        """
        self.__synapse_io = synapse_io
        self.__poptable = poptable
        self.__synapse_info = synapse_info
        self.__machine_edge = machine_edge
        self.__app_edge = app_edge
        self.__n_synapse_types = n_synapse_types
        self.__max_row_info = max_row_info
        self.__routing_info = routing_info
        self.__delay_routing_info = delay_routing_info
        self.__weight_scales = weight_scales
        self.__all_syn_block_sz = all_syn_block_sz
        self.__all_single_syn_sz = all_single_syn_sz

        # The matrix size can be calculated up-front; use for checking later
        self.__matrix_size = (
            self.__max_row_info.undelayed_max_bytes *
            self.__machine_edge.pre_vertex.vertex_slice.n_atoms)
        self.__delay_matrix_size = (
            self.__max_row_info.delayed_max_bytes *
            self.__machine_edge.pre_vertex.vertex_slice.n_atoms *
            self.__app_edge.n_delay_stages)
        self.__single_matrix_size = (
            self.__machine_edge.pre_vertex.vertex_slice.n_atoms *
            BYTES_PER_WORD)

        self.__index = None
        self.__delay_index = None
        self.__syn_mat_offset = None
        self.__delay_syn_mat_offset = None
        self.__is_single = False
        self.__received_block = None
        self.__delay_received_block = None

    @property
    def is_delayed(self):
        """ Is there a delay matrix?

        :rtype: bool
        """
        return self.__app_edge.n_delay_stages > 0

    def is_direct(self, single_addr):
        """ Determine if the given connection can be done with a "direct"\
            synaptic matrix - this must have an exactly 1 entry per row

        :param int single_addr: The current offset of the direct matrix
        :return: A tuple of a boolean indicating if the matrix is direct and
            the next offset of the single matrix
        :rtype: (bool, int)
        """
        pre_vertex_slice = self.__machine_edge.pre_vertex.vertex_slice
        post_vertex_slice = self.__machine_edge.post_vertex.vertex_slice
        next_addr = single_addr + self.__single_matrix_size
        is_direct = (
            next_addr <= self.__all_single_syn_sz and
            not self.is_delayed and
            isinstance(self.__synapse_info.connector, OneToOneConnector) and
            isinstance(self.__synapse_info.synapse_dynamics,
                       SynapseDynamicsStatic) and
            (pre_vertex_slice.lo_atom == post_vertex_slice.lo_atom) and
            (pre_vertex_slice.hi_atom == post_vertex_slice.hi_atom) and
            not self.__synapse_info.prepop_is_view and
            not self.__synapse_info.postpop_is_view)
        return is_direct, next_addr

    def get_row_data(self, machine_time_step):
        """ Generate the row data for a synaptic matrix from the description

        :param float machine_time_step: the sim machine time step.
        :return: The data and the delayed data
        :rtype: tuple(~numpy.ndarray or None, ~numpy.ndarray or None)
        """

        # Get the row data; note that we use the availability of the routing
        # keys to decide if we should actually generate any data; this is
        # because a single edge might have been filtered
        (row_data, delayed_row_data, delayed_source_ids,
         delay_stages) = self.__synapse_io.get_synapses(
            self.__synapse_info, self.__app_edge.n_delay_stages,
            self.__n_synapse_types, self.__weight_scales,
            self.__machine_edge, self.__max_row_info,
            self.__routing_info is not None,
            self.__delay_routing_info is not None,
            machine_time_step, self.__app_edge)

        if self.__app_edge.delay_edge is not None:
            pre_vertex_slice = self.__machine_edge.pre_vertex.vertex_slice
            self.__app_edge.delay_edge.pre_vertex.add_delays(
                pre_vertex_slice, delayed_source_ids, delay_stages)
        elif delayed_source_ids.size != 0:
            raise Exception(
                "Found delayed source IDs but no delay "
                "edge for {}".format(self.__app_edge.label))

        return row_data, delayed_row_data

    def write_machine_matrix(
            self, spec, block_addr, single_synapses, single_addr, row_data):
        """ Write a matrix for the incoming machine vertex

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param int single_addr:
            The address in the "direct" or "single" matrix to start at
        :param list single_synapses:
            A list of "direct" or "single" synapses to write to
        :param ~numpy.ndarray row_data: The data to write
        :return: The updated block and single addresses
        :rtype: tuple(int, int)
        """
        # We can't write anything if there isn't a key
        if self.__routing_info is None:
            return block_addr, single_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = self.__poptable.add_invalid_entry(
                self.__routing_info.first_key_and_mask)
            return block_addr, single_addr

        size = len(row_data) * BYTES_PER_WORD
        if size != self.__matrix_size:
            raise Exception("Data is incorrect size: {} instead of {}".format(
                size, self.__matrix_size))

        is_direct, _ = self.is_direct(single_addr)
        if is_direct:
            single_addr = self.__write_single_machine_matrix(
                single_synapses, single_addr, row_data)
            return block_addr, single_addr

        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__index = self.__poptable.add_machine_entry(
            block_addr, self.__max_row_info.undelayed_max_words,
            self.__routing_info.first_key_and_mask)
        spec.write_array(row_data)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr, single_addr

    def write_delayed_machine_matrix(self, spec, block_addr, row_data):
        """ Write a delayed matrix for an incoming machine vertex

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int block_addr:
            The address in the synaptic matrix region to start writing at
        :param ~numpy.ndarray row_data: The data to write
        :return: The updated block address
        :rtype: int
        """
        # We can't write anything if there isn't a key
        if self.__delay_routing_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = self.__poptable.add_invalid_entry(
                self.__delay_routing_info.first_key_and_mask)
            return block_addr

        size = len(row_data) * BYTES_PER_WORD
        if size != self.__delay_matrix_size:
            raise Exception("Data is incorrect size: {} instead of {}".format(
                size, self.__delay_matrix_size))

        block_addr = self.__poptable.write_padding(spec, block_addr)
        self.__delay_index = self.__poptable.add_machine_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_routing_info.first_key_and_mask)
        spec.write_array(row_data)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr

    def __write_single_machine_matrix(
            self, single_synapses, single_addr, row_data):
        """ Write a direct (single synapse) matrix for an incoming machine\
            vertex

        :param list single_synapses: A list of single synapses to add to
        :param int single_addr: The initial address to write to
        :param ~numpy.ndarray row_data: The row data to write
        :return: The updated single address
        :rtype: int
        """
        single_rows = row_data.reshape(-1, 4)[:, 3]
        data_size = len(single_rows) * BYTES_PER_WORD
        if data_size != self.__single_matrix_size:
            raise Exception("Row data incorrect size: {} instead of {}".format(
                data_size, self.__single_matrix_size))
        self.__index = self.__poptable.add_machine_entry(
            single_addr, self.__max_row_info.undelayed_max_words,
            self.__routing_info.first_key_and_mask, is_single=True)
        single_synapses.append(single_rows)
        self.__syn_mat_offset = single_addr
        self.__is_single = True
        single_addr = single_addr + self.__single_matrix_size
        return single_addr

    def next_app_on_chip_address(self, app_block_addr, max_app_addr):
        """ Allocate a machine-level address of a matrix from within an\
            app-level allocation

        :param int app_block_addr:
            The current position in the application block
        :param int max_app_addr:
            The position of the end of the allocation
        :return: The address after the allocation and the allocated address
        :rtype: int, int
        """
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            return app_block_addr, SYN_REGION_UNUSED

        # Note: No master population table padding is needed here because
        # the allocation is at the application level
        addr = app_block_addr
        app_block_addr = self.__next_addr(
            app_block_addr, self.__matrix_size, max_app_addr)
        return app_block_addr, addr

    def next_app_delay_on_chip_address(self, app_block_addr, max_app_addr):
        """ Allocate a machine-level address of a delayed matrix from within\
            an app-level allocation

        :param int app_block_addr:
            The current position in the application block
        :param int max_app_addr:
            The position of the end of the allocation
        :return: The address after the allocation and the allocated address
        :rtype: int, int
        """
        if self.__max_row_info.delayed_max_n_synapses == 0:
            return app_block_addr, SYN_REGION_UNUSED

        # Note: No master population table padding is needed here because
        # the allocation is at the application level
        addr = app_block_addr
        app_block_addr = self.__next_addr(
            app_block_addr, self.__delay_matrix_size, max_app_addr)
        return app_block_addr, addr

    def next_on_chip_address(self, block_addr):
        """ Allocate an address for a machine matrix and add it to the\
            population table

        :param int block_addr:
            The address at which to start the allocation
        :return: The address after the allocation and the allocated address
        :rtype: int, int
        """
        # Can't reserve anything if there isn't a key
        if self.__routing_info is None:
            return block_addr, SYN_REGION_UNUSED

        # If we have routing info but no synapses, add an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = self.__poptable.add_invalid_entry(
                self.__routing_info.first_key_and_mask)
            return block_addr, SYN_REGION_UNUSED

        # Otherwise add a master population table entry for the incoming
        # machine vertex
        block_addr = self.__poptable.get_next_allowed_address(block_addr)
        self.__index = self.__poptable.add_machine_entry(
            block_addr, self.__max_row_info.undelayed_max_words,
            self.__routing_info.first_key_and_mask)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr, self.__syn_mat_offset

    def next_delay_on_chip_address(self, block_addr):
        """ Allocate an address for a delayed machine matrix and add it to \
            the population table

        :param int block_addr:
            The address at which to start the allocation
        :return: The address after the allocation and the allocated address
        :rtype: int, int
        """
        # Can't reserve anything if there isn't a key
        if self.__delay_routing_info is None:
            return block_addr, SYN_REGION_UNUSED

        # If we have routing info but no synapses, add an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            self.__delay_index = self.__poptable.add_invalid_entry(
                self.__delay_routing_info.first_key_and_mask)
            return block_addr, SYN_REGION_UNUSED

        # Otherwise add a master population table entry for the incoming
        # machine vertex
        block_addr = self.__poptable.get_next_allowed_address(block_addr)
        self.__delay_index = self.__poptable.add_machine_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_routing_info.first_key_and_mask)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr, self.__delay_syn_mat_offset

    def get_generator_data(
            self, syn_mat_offset, d_mat_offset, max_delay_per_stage,
            machine_time_step):
        """ Get the generator data for this matrix

        :param int syn_mat_offset:
            The synaptic matrix offset to write the data to
        :param float machine_time_step: the sim's machine time step.
        :param int d_mat_offset:
            The synaptic matrix offset to write the delayed data to
        :param int max_delay_per_stage: around of timer ticks each delay stage
            holds.
        :rtype: GeneratorData
        """
        self.__write_on_chip_delay_data(max_delay_per_stage, machine_time_step)
        return GeneratorData(
            syn_mat_offset, d_mat_offset,
            self.__max_row_info.undelayed_max_words,
            self.__max_row_info.delayed_max_words,
            self.__max_row_info.undelayed_max_n_synapses,
            self.__max_row_info.delayed_max_n_synapses,
            self.__app_edge.pre_vertex.vertex_slices,
            self.__app_edge.post_vertex.vertex_slices,
            self.__machine_edge.pre_vertex.vertex_slice,
            self.__machine_edge.post_vertex.vertex_slice,
            self.__synapse_info, self.__app_edge.n_delay_stages + 1,
            max_delay_per_stage, machine_time_step)

    def __write_on_chip_delay_data(
            self, max_delay_per_stage, machine_time_step):
        """ Write data for delayed on-chip generation

        :param machine_time_step: sim machine time step
        :param max_delay_per_stage: max delay supported by psot vertex
        """
        # If delay edge exists, tell this about the data too, so it can
        # generate its own data
        if (self.__max_row_info.delayed_max_n_synapses > 0 and
                self.__app_edge.delay_edge is not None):
            self.__app_edge.delay_edge.pre_vertex.add_generator_data(
                self.__max_row_info.undelayed_max_n_synapses,
                self.__max_row_info.delayed_max_n_synapses,
                self.__app_edge.pre_vertex.vertex_slices,
                self.__app_edge.post_vertex.vertex_slices,
                self.__machine_edge.pre_vertex.vertex_slice,
                self.__machine_edge.post_vertex.vertex_slice,
                self.__synapse_info, self.__app_edge.n_delay_stages + 1,
                max_delay_per_stage, machine_time_step)
        elif self.__max_row_info.delayed_max_n_synapses != 0:
            raise Exception(
                "Found delayed items but no delay machine edge for {}".format(
                    self.__app_edge.label))

    def __next_addr(self, block_addr, size, max_addr=None):
        """ Get the next block address and check it hasn't overflowed the\
            allocation

        :param int block_addr: The address of the allocation
        :param int size: The size of the allocation in bytes
        :param int max_addr: The optional maximum address to measure against;
            if not supplied, the global synaptic block limit will be used
        :raise Exception: If the allocation overflows
        """
        next_addr = block_addr + size
        if max_addr is None:
            max_addr = self.__all_syn_block_sz
        if next_addr > max_addr:
            raise Exception(
                "Too much synaptic memory has been used: {} of {}".format(
                    next_addr, max_addr))
        return next_addr

    @property
    def index(self):
        """ The index of the matrix within the master population table

        :rtype: int
        """
        return self.__index

    @property
    def delay_index(self):
        """ The index of the delayed matrix within the master population table

        :rtype: int
        """
        return self.__delay_index

    def read_connections(
            self, transceiver, placement, synapses_address, single_address):
        """ Read the connections from the machine

        :param ~spinnman.transciever.Transceiver transceiver:
            How to read the data from the machine
        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
        :param int synapses_address:
            The base address of the synaptic matrix region
        :param int single_address:
            The base address of the "direct" or "single" matrix region
        :return: A list of arrays of connections, each with dtype
            AbstractSynapseDynamics.NUMPY_CONNECTORS_DTYPE
        :rtype: ~numpy.ndarray
        """
        pre_slice = self.__machine_edge.pre_vertex.vertex_slice
        post_slice = self.__machine_edge.post_vertex.vertex_slice
        machine_time_step = globals_variables.get_simulator().machine_time_step
        connections = list()

        if self.__syn_mat_offset is not None:
            if self.__is_single:
                block = self.__get_single_block(
                    transceiver, placement, single_address)
            else:
                block = self.__get_block(
                    transceiver, placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(self.__synapse_io.convert_to_connections(
                self.__synapse_info, pre_slice, post_slice,
                self.__max_row_info.undelayed_max_words,
                self.__n_synapse_types, self.__weight_scales, block,
                machine_time_step, False, splitter.max_support_delay()))

        if self.__delay_syn_mat_offset is not None:
            block = self.__get_delayed_block(
                transceiver, placement, synapses_address)
            splitter = self.__app_edge.post_vertex.splitter
            connections.append(self.__synapse_io.convert_to_connections(
                self.__synapse_info, pre_slice, post_slice,
                self.__max_row_info.delayed_max_words, self.__n_synapse_types,
                self.__weight_scales, block,
                machine_time_step, True, splitter.max_support_delay()))

        return connections

    def clear_connection_cache(self):
        """ Clear the saved connections
        """
        self.__received_block = None
        self.__delay_received_block = None

    def __get_block(self, transceiver, placement, synapses_address):
        """ Get a block of data for undelayed synapses

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the data from the machine
        :param ~pacman.model.placements.Placement placement:
            Where the matrix is on the machine
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

    def __get_single_block(self, transceiver, placement, single_address):
        """ Get a block of data for "direct" or "single" synapses

        :param Transceiver transceiver: How to read the data from the machine
        :param Placement placement: Where the matrix is on the machine
        :param int single_address:
            The base address of the "direct" or "single" matrix region
        :rtype: bytearray
        """
        if self.__received_block is not None:
            return self.__received_block
        address = self.__syn_mat_offset + single_address
        block = transceiver.read_memory(
            placement.x, placement.y, address, self.__single_matrix_size)
        numpy_data = numpy.asarray(block, dtype="uint8").view("uint32")
        n_rows = len(numpy_data)
        numpy_block = numpy.zeros((n_rows, BYTES_PER_WORD), dtype="uint32")
        numpy_block[:, 3] = numpy_data
        numpy_block[:, 1] = 1
        self.__received_block = numpy_block
        return numpy_block.tobytes()
