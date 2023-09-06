# Copyright (c) 2020 The University of Manchester
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
from collections import defaultdict
from numpy import floating
from numpy.typing import NDArray
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, cast
from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM, MultiRegionSDRAM
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.utilities.utility_objs import ChipCounter
from spynnaker.pyNN.models.neuron import (
    PopulationMachineVertex,
    PopulationMachineLocalOnlyCombinedVertex, LocalOnlyProvenance)
from spynnaker.pyNN.models.neuron.population_machine_vertex import (
    NeuronProvenance, SynapseProvenance, MainProvenance,
    SpikeProcessingProvenance)
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_sdram_for_bit_field_region)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.models.neuron.local_only import AbstractLocalOnly
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
from spynnaker.pyNN.models.neuron.neuron_data import NeuronData
from spynnaker.pyNN.models.neuron.population_machine_common import (
    PopulationMachineCommon)
from .splitter_abstract_pop_vertex import SplitterAbstractPopulationVertex
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from spynnaker.pyNN.models.common.population_application_vertex import (
    PopulationApplicationVertex)

# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14


class SplitterAbstractPopulationVertexFixed(SplitterAbstractPopulationVertex):
    """
    Handles the splitting of the :py:class:`AbstractPopulationVertex`
    using fixed slices.
    """

    __slots__ = ("__expect_delay_extension", )

    def __init__(self) -> None:
        super().__init__(None)
        self.__expect_delay_extension: Optional[bool] = None

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter):
        app_vertex = self._apv
        app_vertex.synapse_recorder.add_region_offset(
            len(app_vertex.neuron_recorder.get_recordable_variables()))

        max_atoms_per_core = min(
            app_vertex.get_max_atoms_per_core(), app_vertex.n_atoms)

        ring_buffer_shifts = app_vertex.get_ring_buffer_shifts()
        weight_scales = app_vertex.get_weight_scales(ring_buffer_shifts)
        all_syn_block_sz = app_vertex.get_synapses_size(
            max_atoms_per_core)
        structural_sz = app_vertex.get_structural_dynamics_size(
            max_atoms_per_core)
        sdram = self.get_sdram_used_by_atoms(
            max_atoms_per_core, all_syn_block_sz, structural_sz)
        synapse_regions = PopulationMachineVertex.SYNAPSE_REGIONS
        synaptic_matrices = SynapticMatrices(
            app_vertex, synapse_regions, max_atoms_per_core, weight_scales,
            all_syn_block_sz)
        neuron_data = NeuronData(app_vertex)

        for index, vertex_slice in enumerate(self._get_fixed_slices()):
            chip_counter.add_core(sdram)
            label = f"{app_vertex.label}{vertex_slice}"
            machine_vertex = self.create_machine_vertex(
                vertex_slice, sdram, label,
                structural_sz, ring_buffer_shifts, weight_scales,
                index, max_atoms_per_core, synaptic_matrices, neuron_data)
            app_vertex.remember_machine_vertex(machine_vertex)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> List[Slice]:
        return self._get_fixed_slices()

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> List[Slice]:
        return self._get_fixed_slices()

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id) -> List[MachineVertex]:
        return list(self._apv.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id) -> List[MachineVertex]:
        return list(self._apv.machine_vertices)

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex, partition_id) -> List[
                Tuple[MachineVertex, Sequence[MachineVertex]]]:
        # Determine the real pre-vertex
        pre_vertex = source_vertex
        if isinstance(source_vertex, DelayExtensionVertex):
            pre_vertex = source_vertex.source_vertex
        if not isinstance(pre_vertex, PopulationApplicationVertex):
            return []

        # Use the real pre-vertex to get the projections
        targets: Dict[MachineVertex, OrderedSet[
            MachineVertex]] = defaultdict(OrderedSet)
        for proj in self._apv.get_incoming_projections_from(pre_vertex):
            # pylint: disable=protected-access
            s_info = proj._synapse_information
            # Use the original source vertex to get the connected vertices,
            # as the real source machine vertices must make it in to this array
            for (tgt, srcs) in s_info.synapse_dynamics.get_connected_vertices(
                    s_info, source_vertex, self.governed_app_vertex):
                targets[tgt].update(srcs)
        return [(tgt, tuple(srcs)) for tgt, srcs in targets.items()]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record) -> Iterable[MachineVertex]:
        return self._apv.machine_vertices

    def create_machine_vertex(
            self, vertex_slice: Slice, sdram: AbstractSDRAM, label: str,
            structural_sz: int, ring_buffer_shifts: Sequence[int],
            weight_scales: NDArray[floating], index: int,
            max_atoms_per_core: int, synaptic_matrices: SynapticMatrices,
            neuron_data: NeuronData) -> PopulationMachineCommon:
        # If using local-only create a local-only vertex
        s_dynamics = self._apv.synapse_dynamics
        if isinstance(s_dynamics, AbstractLocalOnly):
            return PopulationMachineLocalOnlyCombinedVertex(
                sdram, label, self._apv, vertex_slice, index,
                ring_buffer_shifts, weight_scales, neuron_data,
                max_atoms_per_core)

        # Otherwise create a normal vertex
        return PopulationMachineVertex(
            sdram, label, self._apv, vertex_slice, index, ring_buffer_shifts,
            weight_scales, structural_sz, max_atoms_per_core,
            synaptic_matrices, neuron_data)

    def get_sdram_used_by_atoms(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int) -> AbstractSDRAM:
        """
        Gets the resources of a slice of atoms.

        :param int n_atoms:
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        # pylint: disable=arguments-differ
        variable_sdram = self.__get_variable_sdram(n_atoms)
        constant_sdram = self.__get_constant_sdram(
            n_atoms, all_syn_block_sz, structural_sz)
        sdram = MultiRegionSDRAM()
        sdram.nest(len(PopulationMachineVertex.REGIONS) + 1, variable_sdram)
        sdram.merge(constant_sdram)

        # return the total resources.
        return sdram

    def __get_variable_sdram(self, n_atoms: int) -> AbstractSDRAM:
        """
        Returns the variable SDRAM from the recorders.

        :param int n_atoms: The number of atoms to account for
        :return: the variable SDRAM used by the neuron recorder
        :rtype: VariableSDRAM
        """
        s_dynamics = self._apv.synapse_dynamics
        if isinstance(s_dynamics, AbstractSynapseDynamicsStructural):
            max_rewires_per_ts = s_dynamics.get_max_rewires_per_ts()
            self._apv.synapse_recorder.set_max_rewires_per_ts(
                max_rewires_per_ts)

        return (
            self._apv.get_max_neuron_variable_sdram(n_atoms) +
            self._apv.get_max_synapse_variable_sdram(n_atoms))

    def __get_constant_sdram(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int) -> MultiRegionSDRAM:
        """
        Returns the constant SDRAM used by the atoms.

        :param int n_atoms: The number of atoms to account for
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        s_dynamics = self._apv.synapse_dynamics
        n_record = (
            len(self._apv.neuron_recordables) +
            len(self._apv.synapse_recordables))

        n_provenance = NeuronProvenance.N_ITEMS + MainProvenance.N_ITEMS
        if isinstance(s_dynamics, AbstractLocalOnly):
            n_provenance += LocalOnlyProvenance.N_ITEMS
        else:
            n_provenance += (
                SynapseProvenance.N_ITEMS + SpikeProcessingProvenance.N_ITEMS)

        sdram = MultiRegionSDRAM()
        if isinstance(s_dynamics, AbstractLocalOnly):
            sdram.merge(self._apv.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineLocalOnlyCombinedVertex.COMMON_REGIONS))
            sdram.merge(self._apv.get_neuron_constant_sdram(
                n_atoms,
                PopulationMachineLocalOnlyCombinedVertex.NEURON_REGIONS))
            sdram.merge(self.__get_local_only_constant_sdram(n_atoms))
        else:
            sdram.merge(self._apv.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineVertex.COMMON_REGIONS))
            sdram.merge(self._apv.get_neuron_constant_sdram(
                n_atoms, PopulationMachineVertex.NEURON_REGIONS))
            sdram.merge(self.__get_synapse_constant_sdram(
                n_atoms, all_syn_block_sz, structural_sz))
        return sdram

    def __get_local_only_constant_sdram(
            self, n_atoms: int) -> MultiRegionSDRAM:
        s_dynamics = cast(AbstractLocalOnly, self._apv.synapse_dynamics)
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            PopulationMachineLocalOnlyCombinedVertex.REGIONS.LOCAL_ONLY,
            PopulationMachineLocalOnlyCombinedVertex.LOCAL_ONLY_SIZE)
        sdram.add_cost(
            PopulationMachineLocalOnlyCombinedVertex.REGIONS.LOCAL_ONLY_PARAMS,
            s_dynamics.get_parameters_usage_in_bytes(
                n_atoms, self._apv.incoming_projections))
        return sdram

    def __get_synapse_constant_sdram(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int) -> MultiRegionSDRAM:
        """
        Get the amount of fixed SDRAM used by synapse parts.

        :param int n_atoms: The number of atoms to account for

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        regions = PopulationMachineVertex.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.add_cost(regions.synapse_params,
                       self._apv.get_synapse_params_size())
        sdram.add_cost(regions.synapse_dynamics,
                       self._apv.get_synapse_dynamics_size(n_atoms))
        sdram.add_cost(regions.structural_dynamics, structural_sz)
        sdram.add_cost(regions.synaptic_matrix, all_syn_block_sz)
        sdram.add_cost(
            regions.pop_table,
            MasterPopTableAsBinarySearch.get_master_population_table_size(
                self._apv.incoming_projections))
        sdram.add_cost(regions.connection_builder,
                       self._apv.get_synapse_expander_size())
        sdram.add_cost(regions.bitfield_filter,
                       get_sdram_for_bit_field_region(
                           self._apv.incoming_projections))
        return sdram

    @overrides(SplitterAbstractPopulationVertex.
               reset_called)  # type: ignore[has-type]
    def reset_called(self) -> None:
        super().reset_called()
        self.__expect_delay_extension = None

    @overrides(SplitterAbstractPopulationVertex._update_max_delay)
    def _update_max_delay(self) -> None:
        # Find the maximum delay from incoming synapses
        self._max_delay, self.__expect_delay_extension = \
            self._apv.get_max_delay(MAX_RING_BUFFER_BITS)

    @overrides(AbstractSpynnakerSplitterDelay.accepts_edges_from_delay_vertex)
    def accepts_edges_from_delay_vertex(self) -> bool:
        if self.__expect_delay_extension is None:
            self._update_max_delay()
        if self.__expect_delay_extension:
            return True
        raise NotImplementedError(
            "This call was unexpected as it was calculated that "
            "the max needed delay was less that the max possible")
