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
from __future__ import annotations
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy
from numpy import uint32
from numpy.typing import NDArray

from pacman.model.graphs.common import Slice
from pacman.model.placements import Placement

from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.interface.buffer_management import BufferManager

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnHost)
from spynnaker.pyNN.types import WeightScales

from .generator_data import GeneratorData
from .synapse_io import read_all_synapses, convert_to_connections, get_synapses

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synaptic_matrices import AppKeyInfo
    from .master_pop_table import MasterPopTableAsBinarySearch


class SynapticMatrixApp(object):
    """
    The synaptic matrix (and delay matrix if applicable) for an incoming
    application edge.
    """

    __slots__ = (
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
        # The number of bits to use for neuron IDs
        "__max_atoms_per_core",
        # The download index for the undelayed synaptic matrix
        "__download_index",
        # The download index for the delayed synaptic matrix
        "__download_delay_index")

    def __init__(
            self, synapse_info: SynapseInformation,
            app_edge: ProjectionApplicationEdge, n_synapse_types: int,
            synaptic_matrix_region: int, max_atoms_per_core: int,
            all_syn_block_sz: int, app_key_info: Optional[AppKeyInfo],
            delay_app_key_info: Optional[AppKeyInfo],
            weight_scales: WeightScales):
        """
        :param synapse_info:
            The projection synapse information
        :param app_edge:
            The projection application edge
        :param n_synapse_types: The number of synapse types accepted
        :param synaptic_matrix_region:
            The region where synaptic matrices are stored
        :param all_syn_block_sz:
            The space available for all synaptic matrices on the core
        :param app_key_info:
            Application-level routing key information for undelayed vertices
        :param delay_app_key_info:
            Application-level routing key information for delayed vertices
        :param weight_scales:
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
        self.__syn_mat_offset: Optional[int] = None
        self.__delay_syn_mat_offset: Optional[int] = None
        self.__index: Optional[int] = None

        self.__download_index: Optional[int] = None
        self.__download_delay_index: Optional[int] = None

    @property
    def gen_size(self) -> int:
        """
        Size of a block.
        """
        max_row_length = max(
            self.__max_row_info.undelayed_max_bytes,
            self.__max_row_info.delayed_max_bytes)
        return (max_row_length * self.__app_edge.pre_vertex.n_atoms *
                (self.__app_edge.n_delay_stages + 1))

    def reserve_matrices(
            self, block_addr: int,
            pop_table: MasterPopTableAsBinarySearch) -> int:
        """
        Allocate the master pop table entries for the blocks.

        :param block_addr: Where the allocation can start from
        :param pop_table: The master population table
        :return: Where the next allocation can start from
        """
        block_addr = self.__reserve_app_matrix(block_addr, pop_table)
        block_addr = self.__reserve_delay_app_matrix(block_addr, pop_table)
        return block_addr

    def __reserve_app_matrix(
            self, block_addr: int,
            pop_table: MasterPopTableAsBinarySearch) -> int:
        """
        Reserve space for the matrix in the master pop table.

        :param block_addr:
            The address in the synaptic matrix region to start writing at
        :param pop_table:
            The master population table
        :return: The updated block address
        """
        # If there is no routing info, don't write anything
        if self.__app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.undelayed_max_n_synapses == 0:
            self.__index = pop_table.add_invalid_application_entry(
                self.__app_key_info.key_and_mask,
                self.__app_key_info.core_mask, self.__app_key_info.core_shift,
                self.__app_key_info.n_neurons,
                self.__app_key_info.n_colour_bits)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = pop_table.get_next_allowed_address(block_addr)
        self.__index = pop_table.add_application_entry(
            block_addr,  self.__max_row_info.undelayed_max_words,
            self.__app_key_info.key_and_mask, self.__app_key_info.core_mask,
            self.__app_key_info.core_shift, self.__app_key_info.n_neurons,
            self.__app_key_info.n_colour_bits)
        self.__syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__matrix_size)
        return block_addr

    def __reserve_delay_app_matrix(
            self, block_addr: int,
            pop_table: MasterPopTableAsBinarySearch) -> int:
        """
        Reserve space in the master pop table for a delayed matrix.

        :param block_addr:
            The address in the synaptic matrix region to start writing at
        :param pop_table:
            The master population table
        :return: The updated block address
        """
        # If there is no routing info, don't write anything
        if self.__delay_app_key_info is None:
            return block_addr

        # If we have routing info but no synapses, write an invalid entry
        if self.__max_row_info.delayed_max_n_synapses == 0:
            pop_table.add_invalid_application_entry(
                self.__delay_app_key_info.key_and_mask,
                self.__delay_app_key_info.core_mask,
                self.__delay_app_key_info.core_shift,
                self.__delay_app_key_info.n_neurons,
                self.__delay_app_key_info.n_colour_bits)
            return block_addr

        # Write a matrix for the whole application vertex
        block_addr = pop_table.get_next_allowed_address(block_addr)
        pop_table.add_application_entry(
            block_addr, self.__max_row_info.delayed_max_words,
            self.__delay_app_key_info.key_and_mask,
            self.__delay_app_key_info.core_mask,
            self.__delay_app_key_info.core_shift,
            self.__delay_app_key_info.n_neurons,
            self.__delay_app_key_info.n_colour_bits)
        self.__delay_syn_mat_offset = block_addr
        block_addr = self.__next_addr(block_addr, self.__delay_matrix_size)
        return block_addr

    def __next_addr(self, block_addr: int, size: int) -> int:
        """
        Get the next address after a block, checking it is in range.

        :param block_addr: The address of the start of the block
        :param size: The size of the block in bytes
        :return: The updated address
        :raises ValueError: If the updated address is out of range
        """
        next_addr = block_addr + size
        if next_addr > self.__all_syn_block_sz:
            raise ValueError(
                "Too much synaptic memory has been written: "
                f"{next_addr} of {self.__all_syn_block_sz} ")
        return next_addr

    def append_matrix(
            self, post_vertex_slice: Slice,
            data_to_write: List[NDArray[uint32]],
            block_addr: int) -> int:
        """
        Append a synaptic matrix from be written from host.

        :param post_vertex_slice:
            The slice of the post-vertex the matrix is for
        :param data_to_write: List to append the data to write to
        :param block_addr: The amount of data written so far
        :return: The amount of data written after this data has been written
        """
        row_data, delay_row_data = self.__get_row_data(post_vertex_slice)
        self.__update_connection_holders(
            row_data, delay_row_data, post_vertex_slice)
        if self.__syn_mat_offset is not None:
            block_addr = self.__get_padding(
                data_to_write, self.__syn_mat_offset, block_addr)
            data_to_write.append(row_data)
            block_addr += self.__matrix_size
        if self.__delay_syn_mat_offset is not None:
            block_addr = self.__get_padding(
                data_to_write, self.__delay_syn_mat_offset, block_addr)
            data_to_write.append(delay_row_data)
            block_addr += self.__delay_matrix_size
        return block_addr

    def __get_padding(
            self, data_to_write: List[NDArray[uint32]],
            expected_offset: int, block_addr: int) -> int:
        if expected_offset < block_addr:
            raise ValueError(
                "The block address is already beyond where is expected!:"
                f" {expected_offset} expected, {block_addr} found.")
        if expected_offset > block_addr:
            padding = (expected_offset - block_addr) // BYTES_PER_WORD
            data_to_write.append(numpy.zeros(padding, dtype=uint32))
            return block_addr + (padding * BYTES_PER_WORD)
        return block_addr

    def __get_row_data(
            self, post_vertex_slice: Slice) -> Tuple[NDArray, NDArray]:
        """
        Generate the row data for a synaptic matrix from the description.

        :return: The data and the delayed data
        """
        # Get the actual connections
        post_slices =\
            self.__app_edge.post_vertex.splitter.get_in_coming_slices()
        connector = self.__synapse_info.connector
        assert isinstance(connector, AbstractGenerateConnectorOnHost)
        connections = connector.create_synaptic_block(
            post_slices, post_vertex_slice,
            self.__synapse_info.synapse_type, self.__synapse_info)

        # Get the row data; note that we use the availability of the routing
        # keys to decide if we should actually generate any data; this is
        # because a single edge might have been filtered
        (row_data, delayed_row_data) = get_synapses(
            connections, self.__synapse_info, self.__app_edge.n_delay_stages,
            self.__n_synapse_types, self.__weight_scales, self.__app_edge,
            self.__max_row_info, self.__app_key_info is not None,
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
            self, data: NDArray[uint32], delayed_data: NDArray[uint32],
            post_vertex_slice: Slice) -> None:
        """
        Fill in connections in the connection holders as they are created.

        :param data: The row data created
        :param delayed_data: The delayed row data created
        """
        post_splitter = self.__app_edge.post_vertex.splitter
        post_vertex_max_delay_ticks = post_splitter.max_support_delay()
        for conn_holder in self.__synapse_info.pre_run_connection_holders:
            conn_holder.add_connections(read_all_synapses(
                data, delayed_data, self.__synapse_info,
                self.__n_synapse_types, self.__weight_scales,
                post_vertex_slice, self.__app_edge.pre_vertex.n_atoms,
                post_vertex_max_delay_ticks,
                self.__max_row_info, self.__max_atoms_per_core))

    def get_generator_data(self) -> GeneratorData:
        """
        Prepare to write a matrix using an on-chip generator.

        :return: The data to generate with
        """
        max_pre_atoms_per_core = min(
            self.__app_edge.pre_vertex.n_atoms,
            self.__app_edge.pre_vertex.get_max_atoms_per_core())
        return GeneratorData(
            self.__syn_mat_offset, self.__delay_syn_mat_offset,
            self.__app_edge, self.__synapse_info, self.__max_row_info,
            max_pre_atoms_per_core, self.__max_atoms_per_core)

    def read_generated_connection_holders(self, placement: Placement) -> None:
        """
        Read any pre-run connection holders after data has been generated.

        :param placement:
            Where the matrix is on the machine
        """
        if self.__synapse_info.pre_run_connection_holders:
            connections = self.get_connections(placement)
            if connections:
                conns = numpy.concatenate(connections)
                for holder in self.__synapse_info.pre_run_connection_holders:
                    holder.add_connections(conns)

    def get_connections(self, placement: Placement) -> List[NDArray]:
        """
        Read connections from an address on the machine.

        :param placement:
            Where the matrix is on the machine
        :return: A list of arrays of connections, each with dtype
            :py:const:`~.NUMPY_CONNECTORS_DTYPE`
        """
        connections = list()

        synapses_address: Optional[int] = None
        buffers: Optional[BufferManager] = None
        if (self.__download_index is None and
                self.__download_delay_index is None):
            synapses_address = locate_memory_region_for_placement(
                placement, self.__synaptic_matrix_region)
        else:
            buffers = SpynnakerDataView().get_buffer_manager()

        splitter = self.__app_edge.post_vertex.splitter
        vertex_slice = placement.vertex.vertex_slice
        if self.__syn_mat_offset is not None:
            if self.__download_index is not None:
                assert buffers is not None
                block, _ = buffers.get_download(
                    placement, self.__download_index)
            else:
                assert synapses_address is not None
                block = self.__get_block(placement, synapses_address)
            connections.append(convert_to_connections(
                self.__synapse_info, vertex_slice,
                self.__app_edge.pre_vertex.n_atoms,
                self.__max_row_info.undelayed_max_words,
                self.__n_synapse_types, self.__weight_scales, block, False,
                splitter.max_support_delay(), self.__max_atoms_per_core))
        if self.__delay_syn_mat_offset is not None:
            if self.__download_delay_index is not None:
                assert buffers is not None
                block, _ = buffers.get_download(
                    placement, self.__download_delay_index)
            else:
                assert synapses_address is not None
                block = self.__get_delayed_block(placement, synapses_address)
            connections.append(convert_to_connections(
                self.__synapse_info, vertex_slice,
                self.__app_edge.pre_vertex.n_atoms,
                self.__max_row_info.delayed_max_words,
                self.__n_synapse_types, self.__weight_scales, block, True,
                splitter.max_support_delay(), self.__max_atoms_per_core))

        return connections

    def __get_block(
            self, placement: Placement, synapses_address: int) -> bytes:
        """
        Get a block of data for undelayed synapses.

        :param placement: Where the matrix is on the machine
        :param synapses_address:
            The base address of the synaptic matrix region
        :return: The raw data from the synaptic matrix
        """
        assert self.__syn_mat_offset is not None
        address = self.__syn_mat_offset + synapses_address
        return SpynnakerDataView.read_memory(
            placement.x, placement.y, address, self.__matrix_size)

    def __get_delayed_block(
            self, placement: Placement, synapses_address: int) -> bytes:
        """
        Get a block of data for delayed synapses.

        :param placement:
            Where the matrix is on the machine
        :param synapses_address:
            The base address of the synaptic matrix region
        :return: The raw data from the delayed synaptic matrix
        """
        assert self.__delay_syn_mat_offset is not None
        address = self.__delay_syn_mat_offset + synapses_address
        return SpynnakerDataView.read_memory(
            placement.x, placement.y, address, self.__delay_matrix_size)

    def get_index(self) -> int:
        """
        Get the index in the master population table of the matrix.
        """
        if self.__index is None:
            raise RuntimeError("master pop table space not yet reserved")
        return self.__index

    def get_download_regions(
            self, placement: Placement,
            start_index: int) -> List[Tuple[int, int, int]]:
        """
        Get the data regions that should be downloaded when the simulation
        pauses.

        :param placement:
            The placement of the vertex
        :param start_index:
            The index to use for the first region to download

        :return: A list of tuples of (index, address, size) to download
        """
        if not self.__synapse_info.download_on_pause:
            return []
        synapses_address = locate_memory_region_for_placement(
            placement, self.__synaptic_matrix_region)
        regions = list()
        if self.__syn_mat_offset is not None:
            regions.append((start_index,
                            synapses_address + self.__syn_mat_offset,
                            self.__matrix_size))
            self.__download_index = start_index
            start_index += 1
        if self.__delay_syn_mat_offset is not None:
            regions.append((start_index,
                            synapses_address + self.__delay_syn_mat_offset,
                            self.__delay_matrix_size))
            self.__download_delay_index = start_index
        return regions
