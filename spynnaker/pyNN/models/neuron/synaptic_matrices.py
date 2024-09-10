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
from dataclasses import dataclass
from typing import (
    Dict, List, NamedTuple, Optional, Sequence, Tuple, TYPE_CHECKING)

import numpy
from numpy import floating, uint32
from numpy.typing import NDArray

from pacman.model.graphs.common import Slice
from pacman.model.placements import Placement
from pacman.model.routing_info import (
    AppVertexRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import allocator_bits_needed
from pacman.model.graphs.application import ApplicationVirtualVertex
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationBase)

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_sdram_for_bit_field_region, get_bitfield_key_map_data,
    write_bitfield_init_data)
from spynnaker.pyNN.models.common import PopulationApplicationVertex

from .synaptic_matrix_app import SynapticMatrixApp

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.abstract_population_vertex import (
        AbstractPopulationVertex)
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)

# 1 for synaptic matrix region
# 1 for master pop region
# 1 for bitfield filter region
# 1 for structural region
# 1 for n_edges
# 1 for post_vertex_slice.lo_atom
# 1 for post_vertex_slice.n_atoms
# 1 for post index
# 1 for n_synapse_types
# 1 for timestep per delay
# 1 for padding
# 4 for Population RNG seed
# 4 for core RNG seed
SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES = (
    1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 + 4) * BYTES_PER_WORD

DIRECT_MATRIX_HEADER_COST_BYTES = 1 * BYTES_PER_WORD

# Value to use when there is no region
INVALID_REGION_ID = 0xFFFFFFFF


class SynapseRegions(NamedTuple):
    """
    Indices of regions of synapse-implementing binaries.
    """
    synapse_params: int
    pop_table: int
    synaptic_matrix: int
    synapse_dynamics: int
    structural_dynamics: int
    bitfield_filter: int
    connection_builder: int


class SynapseRegionReferences(NamedTuple):
    """
    Indices of regions of synapse-implementing binaries.
    """
    synapse_params: Optional[int] = None
    pop_table: Optional[int] = None
    synaptic_matrix: Optional[int] = None
    synapse_dynamics: Optional[int] = None
    structural_dynamics: Optional[int] = None
    bitfield_filter: Optional[int] = None
    connection_builder: Optional[int] = None


@dataclass(frozen=True)
class AppKeyInfo(object):
    """
    An object which holds an application key and mask along with the other
    details.
    """

    #: The application-level key
    app_key: int
    #: The application-level mask
    app_mask: int
    #: The mask to get the core from the key
    core_mask: int
    #: The shift to get the core from the key
    core_shift: int
    #: The neurons in each core (except possibly the last)
    n_neurons: int
    #: The number of colour bits sent
    n_colour_bits: int

    @property
    def key_and_mask(self) -> BaseKeyAndMask:
        """
        The key and mask as an object.
        """
        return BaseKeyAndMask(self.app_key, self.app_mask)


class SynapticMatrices(object):
    """
    Handler of synaptic matrices for a core of a population vertex.
    """

    __slots__ = (
        # The number of synapse types received
        "__n_synapse_types",
        # The region identifiers
        "__regions",
        # The sub-matrices for each incoming edge
        "__matrices",
        # The address within the synaptic matrix region after the last matrix
        # was written
        "__host_generated_block_addr",
        # The address within the synaptic matrix region after the last
        # generated matrix will be written
        "__on_chip_generated_block_addr",
        # Determine if any of the matrices can be generated on the machine
        "__gen_on_machine",
        # Number of bits to use for neuron IDs
        "__max_atoms_per_core",
        # The stored master population table data
        "__master_pop_data",
        # The stored generated data
        "__generated_data",
        # The size needed for generated data
        "__generated_data_size",
        # The matrices that need to be generated on host
        "__on_host_matrices",
        # The matrices that have been generated on machine
        "__on_machine_matrices",
        # The application vertex
        "__app_vertex",
        # The weight scales
        "__weight_scales",
        # The size of all synaptic blocks added together
        "__all_syn_block_sz",
        # Whether data generation has already happened
        "__data_generated",
        # The size of the bit field data to be allocated
        "__bit_field_size",
        # The bit field key map generated
        "__bit_field_key_map",
        # The maximum generated data, for calculating timeouts
        "__max_gen_data")

    def __init__(
            self, app_vertex: AbstractPopulationVertex,
            regions: SynapseRegions, max_atoms_per_core: int,
            weight_scales: NDArray[floating], all_syn_block_sz: int):
        """
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
        :param SynapseRegions regions: The synapse regions to use
        :param int max_atoms_per_core:
        :param list(float) weight_scales:
        :param int all_syn_block_sz:
        """
        self.__app_vertex = app_vertex
        self.__regions = regions
        self.__n_synapse_types = app_vertex.neuron_impl.get_n_synapse_types()
        self.__max_atoms_per_core = max_atoms_per_core
        self.__weight_scales = weight_scales
        self.__all_syn_block_sz = all_syn_block_sz

        # Map of (app_edge, synapse_info) to SynapticMatrixApp
        self.__matrices: Dict[
            Tuple[ProjectionApplicationEdge, SynapseInformation],
            SynapticMatrixApp] = dict()

        # Store locations of synaptic data and generated data
        self.__host_generated_block_addr = 0
        self.__on_chip_generated_block_addr = 0

        # Determine whether to generate on machine
        self.__gen_on_machine = False
        self.__data_generated = False
        self.__max_gen_data = 0
        self.__on_host_matrices: List[SynapticMatrixApp] = []
        self.__on_machine_matrices: List[SynapticMatrixApp] = []
        self.__generated_data: Optional[NDArray[uint32]] = None
        self.__generated_data_size = 0
        self.__master_pop_data: Optional[NDArray[uint32]] = None
        self.__bit_field_size = 0
        self.__bit_field_key_map: Optional[NDArray[uint32]] = None

    @property
    def max_gen_data(self) -> int:
        """
        The maximum amount of data to be generated for the synapses.

        :rtype: int
        """
        return self.__max_gen_data

    @property
    def bit_field_size(self) -> int:
        """
        The size of the bit field data.

        :rtype: int
        """
        return self.__bit_field_size

    @property
    def host_generated_block_addr(self) -> int:
        """
        The address within the synaptic region after the last block
        written by the on-host synaptic generation, i.e. the start of
        the space that can be overwritten provided the synapse expander
        is run again.

        :rtype: int
        """
        return self.__host_generated_block_addr

    @property
    def on_chip_generated_matrix_size(self) -> int:
        """
        The size of the space used by the generated matrix, i.e. the
        space that can be overwritten provided the synapse expander
        is run again.

        :rtype: int
        """
        return (self.__on_chip_generated_block_addr -
                self.__host_generated_block_addr)

    def generate_data(self) -> None:
        """
        Generates the data if it has not already been done.
        """
        # If the data has already been generated, stop
        if self.__data_generated:
            return
        self.__data_generated = True

        # If there are no synapses, there is nothing to do!
        if self.__all_syn_block_sz == 0:
            return

        # Track writes inside the synaptic matrix region:
        block_addr = 0

        # Set up the master population table
        poptable = MasterPopTableAsBinarySearch()
        poptable.initialise_table()

        # Set up other lists
        self.__on_host_matrices = list()
        self.__on_machine_matrices = list()
        generated_data: List[NDArray[uint32]] = list()

        # Keep on-machine generated blocks together at the end
        self.__generated_data_size = (
            SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES +
            (self.__n_synapse_types * DataType.U3232.size))

        # For each incoming machine vertex, reserve pop table space
        for proj in self.__app_vertex.incoming_projections:
            # pylint: disable=protected-access
            app_edge = proj._projection_edge
            synapse_info = proj._synapse_information
            app_key_info = self.__app_key_and_mask(app_edge)
            if app_key_info is None:
                continue
            d_app_key_info = self.__delay_app_key_and_mask(app_edge)
            app_matrix = SynapticMatrixApp(
                synapse_info, app_edge, self.__n_synapse_types,
                self.__regions.synaptic_matrix, self.__max_atoms_per_core,
                self.__all_syn_block_sz, app_key_info, d_app_key_info,
                self.__weight_scales)
            self.__matrices[app_edge, synapse_info] = app_matrix

            # If we can generate on machine, store until end
            if synapse_info.may_generate_on_machine():
                self.__on_machine_matrices.append(app_matrix)
            else:
                block_addr = app_matrix.reserve_matrices(block_addr, poptable)
                self.__on_host_matrices.append(app_matrix)

        self.__host_generated_block_addr = block_addr

        # Now add the blocks on machine to keep these all together
        self.__max_gen_data = 0
        for app_matrix in self.__on_machine_matrices:
            block_addr = app_matrix.reserve_matrices(block_addr, poptable)
            gen_data = app_matrix.get_generator_data()
            self.__generated_data_size += gen_data.size
            generated_data.extend(gen_data.gen_data)
            self.__max_gen_data += app_matrix.gen_size
        if generated_data:
            self.__gen_on_machine = True
            self.__generated_data = numpy.concatenate(generated_data)
        else:
            self.__gen_on_machine = True
            self.__generated_data = numpy.zeros(0, dtype=uint32)

        self.__on_chip_generated_block_addr = block_addr

        # Store the master pop table
        self.__master_pop_data = poptable.get_pop_table_data()

        # Store bit field data
        self.__bit_field_size = get_sdram_for_bit_field_region(
            self.__app_vertex.incoming_projections)
        self.__bit_field_key_map = get_bitfield_key_map_data(
            self.__app_vertex.incoming_projections)
        self.__generated_data_size += (
            len(self.__bit_field_key_map) * BYTES_PER_WORD)

    def __write_pop_table(self, spec: DataSpecificationBase,
                          poptable_ref: Optional[int] = None):
        assert self.__master_pop_data is not None
        master_pop_table_sz = len(self.__master_pop_data) * BYTES_PER_WORD
        spec.reserve_memory_region(
            region=self.__regions.pop_table, size=master_pop_table_sz,
            label='PopTable', reference=poptable_ref)
        spec.switch_write_focus(region=self.__regions.pop_table)
        spec.write_array(self.__master_pop_data)

    def write_synaptic_data(
            self, spec: DataSpecificationBase, post_vertex_slice: Slice,
            references: SynapseRegionReferences):
        """
        Write the synaptic data for all incoming projections.

        :param ~data_specification.DataSpecificationGenerator spec:
            The spec to write to
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post-vertex the matrix is for
        :param SynapseRegionReferences references:
            Regions which are referenced; each region which is not referenced
            can be `None`.
        """
        spec.comment(
            "\nWriting Synaptic Matrix and Master Population Table:\n")

        # Write the pop table
        self.__write_pop_table(spec, references.pop_table)

        # Get the on-host data to be written
        block_addr = 0
        data_to_write: List[NDArray[uint32]] = list()
        for matrix in self.__on_host_matrices:
            block_addr = matrix.append_matrix(
                post_vertex_slice, data_to_write, block_addr)

        # Write on-host data
        spec.reserve_memory_region(
            region=self.__regions.synaptic_matrix,
            size=self.__all_syn_block_sz, label='SynBlocks',
            reference=references.synaptic_matrix)
        if data_to_write:
            spec.switch_write_focus(self.__regions.synaptic_matrix)
            spec.write_array(numpy.concatenate(data_to_write))

        self.__write_synapse_expander_data_spec(
            spec, post_vertex_slice, references.connection_builder)

        write_bitfield_init_data(
            spec, self.__regions.bitfield_filter, self.__bit_field_size,
            references.bitfield_filter)

    def __write_synapse_expander_data_spec(
            self, spec: DataSpecificationBase, post_vertex_slice: Slice,
            connection_builder_ref: Optional[int] = None):
        """
        Write the data spec for the synapse expander.

        :param ~.DataSpecificationGenerator spec:
            The specification to write to
        :param list(GeneratorData) generator_data: The data to be written
        :param weight_scales: scaling of weights on each synapse
        :type weight_scales: list(int or float)
        """
        if self.__generated_data is None:
            if connection_builder_ref is not None:
                # If there is a reference, we still need a region to create
                spec.reserve_memory_region(
                    region=self.__regions.connection_builder,
                    size=4, label="ConnectorBuilderRegion",
                    reference=connection_builder_ref)
            return

        assert self.__bit_field_key_map is not None

        spec.reserve_memory_region(
            region=self.__regions.connection_builder,
            size=self.__generated_data_size, label="ConnectorBuilderRegion",
            reference=connection_builder_ref)
        spec.switch_write_focus(self.__regions.connection_builder)
        spec.write_value(self.__regions.synaptic_matrix)
        spec.write_value(self.__regions.pop_table)
        spec.write_value(self.__regions.bitfield_filter)
        if isinstance(self.__app_vertex.synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            spec.write_value(self.__regions.structural_dynamics)
        else:
            spec.write_value(INVALID_REGION_ID)
        spec.write_value(len(self.__on_machine_matrices))
        spec.write_value(post_vertex_slice.lo_atom)
        spec.write_value(post_vertex_slice.n_atoms)
        spec.write_value(0)  # TODO: The index if needed
        spec.write_value(self.__n_synapse_types)
        spec.write_value(DataType.S1615.encode_as_int(
            SpynnakerDataView.get_simulation_time_step_per_ms()))
        # Per-Population RNG
        spec.write_array(self.__app_vertex.pop_seed)
        # Per-Core RNG
        spec.write_array(self.__app_vertex.core_seed(post_vertex_slice))
        for w in self.__weight_scales:
            # if the weights are high enough and the population size large
            # enough, then weight_scales < 1 will result in a zero scale
            # if converted to an int, so we use U3232 here instead (as there
            # can be scales larger than U1616.max in conductance-based models)
            dtype = DataType.U3232
            spec.write_value(data=min(w, dtype.max), data_type=dtype)

        spec.write_array(self.__generated_data)
        spec.write_array(self.__bit_field_key_map)

    def __get_app_key_and_mask(
            self, r_info: AppVertexRoutingInfo, n_stages: int,
            pre_vertex: PopulationApplicationVertex):
        """
        Get a key and mask for an incoming application vertex as a whole.

        :param RoutingInfo r_info: The routing information for the vertex
        :param int n_stages: The number of delay stages
        :param PopulationApplicationVertex pre_vertex: The pre-vertex
        :rtype: AppKeyInfo
        """
        if isinstance(pre_vertex, ApplicationVirtualVertex):
            mask_size = 0
            core_mask = 0
            n_atoms = 0
        else:
            # Find the part that is just for the core
            mask_size = r_info.n_bits_atoms
            core_mask = (2 ** allocator_bits_needed(
                len(r_info.vertex.splitter.get_out_going_vertices(
                    SPIKE_PARTITION_ID)))) - 1
            n_atoms = min(pre_vertex.get_max_atoms_per_core(),
                          pre_vertex.n_atoms)

        return AppKeyInfo(
            app_key=r_info.key, app_mask=r_info.mask, core_mask=core_mask,
            core_shift=mask_size, n_neurons=n_atoms * n_stages,
            n_colour_bits=pre_vertex.n_colour_bits)

    def __app_key_and_mask(
            self, app_edge: ProjectionApplicationEdge) -> Optional[AppKeyInfo]:
        """
        Get a key and mask for an incoming application vertex as a whole.

        :param ProjectionApplicationEdge app_edge:
            The application edge to get the key and mask of
        """
        routing_info = SpynnakerDataView.get_routing_infos()
        r_info = routing_info.get_routing_info_from_pre_vertex(
            app_edge.pre_vertex, SPIKE_PARTITION_ID)
        if not isinstance(r_info, AppVertexRoutingInfo):
            return None
        return self.__get_app_key_and_mask(r_info, 1, app_edge.pre_vertex)

    def __delay_app_key_and_mask(
            self, app_edge: ProjectionApplicationEdge) -> Optional[AppKeyInfo]:
        """
        Get a key and mask for a whole incoming delayed application
        vertex, or return `None` if no delay edge exists.

        :param ProjectionApplicationEdge app_edge:
            The application edge to get the key and mask of
        """
        delay_edge = app_edge.delay_edge
        if delay_edge is None:
            return None
        routing_info = SpynnakerDataView.get_routing_infos()
        r_info = routing_info.get_routing_info_from_pre_vertex(
            delay_edge.pre_vertex, SPIKE_PARTITION_ID)
        if not isinstance(r_info, AppVertexRoutingInfo):
            return None

        # We use the app_edge pre-vertex max atoms here as the delay vertex
        # is split according to this
        return self.__get_app_key_and_mask(
            r_info, app_edge.n_delay_stages, app_edge.pre_vertex)

    def get_connections_from_machine(
            self, placement: Placement, app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> Sequence[NDArray]:
        """
        Get the synaptic connections from the machine.

        :param ~pacman.model.placements.Placement placement:
            Where the vertices are on the machine
        :param ProjectionApplicationEdge app_edge:
            The application edge of the projection
        :param SynapseInformation synapse_info:
            The synapse information of the projection
        :return: A list of arrays of connections, each with dtype
            :py:const:`~.NUMPY_CONNECTORS_DTYPE`
        :rtype: list(~numpy.ndarray)
        """
        matrix = self.__matrices[app_edge, synapse_info]
        return matrix.get_connections(placement)

    def read_generated_connection_holders(self, placement: Placement):
        """
        Fill in any pre-run connection holders for data which is generated
        on the machine, after it has been generated.

        :param ~pacman.model.placements.Placement placement:
            where the data is to be read from
        """
        for matrix in self.__on_machine_matrices:
            matrix.read_generated_connection_holders(placement)

    @property
    def gen_on_machine(self) -> bool:
        """
        Whether any matrices need to be generated on the machine.

        :rtype: bool
        """
        return self.__gen_on_machine

    def get_index(self, app_edge: ProjectionApplicationEdge,
                  synapse_info: SynapseInformation) -> int:
        """
        Get the index of an incoming projection in the population table.

        :param ProjectionApplicationEdge app_edge:
            The application edge of the projection
        :param SynapseInformation synapse_info:
            The synapse information of the projection
        """
        matrix = self.__matrices[app_edge, synapse_info]
        return matrix.get_index()

    def get_download_regions(
            self, placement: Placement,
            start_index: int) -> List[Tuple[int, int, int]]:
        """
        Get the regions that need to be downloaded.

        :param ~pacman.model.placements.Placement placement:
            The placement of the vertex
        :param int start_index:
            The first index to use in the region identifiers

        :return: The index, the start address and the size of the regions
        """
        regions = list()
        for matrix in self.__matrices.values():
            mat_regions = matrix.get_download_regions(placement, start_index)
            regions.extend(mat_regions)
            start_index += len(mat_regions)
        return regions
