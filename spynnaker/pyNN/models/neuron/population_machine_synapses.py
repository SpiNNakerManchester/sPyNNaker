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
import numpy
from numpy import floating
from numpy.typing import NDArray
from typing import List, Sequence, Tuple, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import abstractmethod

from pacman.model.graphs.common import Slice
from pacman.model.placements import Placement

from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldRoutingCompression)
from spinn_front_end_common.interface.ds import DataSpecificationBase

from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural, AbstractSDRAMSynapseDynamics)
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, HasSynapses)

from .abstract_population_vertex import AbstractPopulationVertex
from .population_machine_synapses_provenance import (
    PopulationMachineSynapsesProvenance)
from .synaptic_matrices import SynapseRegions, SynapseRegionReferences
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)


class PopulationMachineSynapses(
        PopulationMachineSynapsesProvenance,
        AbstractSupportsBitFieldRoutingCompression,
        AbstractSynapseExpandable,
        HasSynapses, allow_derivation=True):
    """
    Mix-in for machine vertices that contain synapses.
    """

    # This MUST stay empty to allow mixing with other things with slots
    __slots__ = ()

    @property
    @abstractmethod
    def _pop_vertex(self) -> AbstractPopulationVertex:
        """
        The application vertex of the machine vertex.

        .. note::
            This is likely to be available via the MachineVertex.

        :rtype: AbstractPopulationVertex
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _vertex_slice(self) -> Slice:
        """
        The slice of the application vertex atoms on this machine vertex.

        .. note::
            This is likely to be available via the MachineVertex.

        :rtype: ~pacman.model.graphs.common.Slice
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _synaptic_matrices(self) -> SynapticMatrices:
        """
        The object holding synaptic matrices.

        :rtype: SynapticMatrices
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _synapse_regions(self) -> SynapseRegions:
        """
        The identifiers of synaptic regions.

        :rtype: .SynapseRegions
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _max_atoms_per_core(self) -> int:
        """
        The maximum number of atoms on any core targeted by these synapses.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def set_do_synapse_regeneration(self) -> None:
        """
        Indicates that synaptic data regeneration is required.
        """
        raise NotImplementedError

    @property
    def _synapse_references(self) -> SynapseRegionReferences:
        """
        The references to synapse regions.  Override to provide these.

        :rtype: .SynapseRegionReferences
        """
        return SynapseRegionReferences()

    @overrides(AbstractSupportsBitFieldRoutingCompression.
               bit_field_base_address)
    def bit_field_base_address(self, placement: Placement) -> int:
        return locate_memory_region_for_placement(
            placement=placement, region=self._synapse_regions.bitfield_filter)

    @overrides(AbstractSupportsBitFieldRoutingCompression.
               regeneratable_sdram_blocks_and_sizes)
    def regeneratable_sdram_blocks_and_sizes(
            self, placement: Placement) -> List[Tuple[int, int]]:
        synaptic_matrix_base_address = locate_memory_region_for_placement(
            placement=placement, region=self._synapse_regions.synaptic_matrix)
        return [(
            self._synaptic_matrices.host_generated_block_addr +
            synaptic_matrix_base_address,
            self._synaptic_matrices.on_chip_generated_matrix_size)]

    def _write_synapse_data_spec(
            self, spec: DataSpecificationBase,
            ring_buffer_shifts: Sequence[int],
            weight_scales: NDArray[floating], structural_sz: int):
        """
        Write the data specification for the synapse data.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        :param list(int) weight_scales:
            The scaling to apply to weights to store them in the synapses
        :param int structural_sz: The size of the structural data
        """
        # Write the synapse parameters
        self._write_synapse_parameters(spec, ring_buffer_shifts)

        # Write the synaptic matrices
        self._synaptic_matrices.generate_data()
        self._synaptic_matrices.write_synaptic_data(
            spec, self._vertex_slice, self._synapse_references)

        # Write any synapse dynamics
        synapse_dynamics = self._pop_vertex.synapse_dynamics
        synapse_dynamics_sz = self._pop_vertex.get_synapse_dynamics_size(
            self._vertex_slice.n_atoms)
        if synapse_dynamics_sz > 0:
            assert isinstance(synapse_dynamics, AbstractSDRAMSynapseDynamics)
            spec.reserve_memory_region(
                region=self._synapse_regions.synapse_dynamics,
                size=synapse_dynamics_sz, label='synapseDynamicsParams',
                reference=self._synapse_references.synapse_dynamics)
            synapse_dynamics.write_parameters(
                spec, self._synapse_regions.synapse_dynamics,
                self._pop_vertex.weight_scale, weight_scales)
        elif self._synapse_references.synapse_dynamics is not None:
            # If there is a reference for this region, we have to create it!
            spec.reserve_memory_region(
                region=self._synapse_regions.synapse_dynamics,
                size=4, label='synapseDynamicsParams',
                reference=self._synapse_references.synapse_dynamics)
        if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            spec.reserve_memory_region(
                region=self._synapse_regions.structural_dynamics,
                size=structural_sz, label='synapseDynamicsStructuralParams',
                reference=self._synapse_references.structural_dynamics)
            synapse_dynamics.write_structural_parameters(
                spec, self._synapse_regions.structural_dynamics,
                weight_scales, self._pop_vertex, self._vertex_slice,
                self._synaptic_matrices)
        elif self._synapse_references.structural_dynamics is not None:
            # If there is a reference for this region, we have to create it!
            spec.reserve_memory_region(
                region=self._synapse_regions.structural_dynamics,
                size=4, label='synapseDynamicsStructuralParams',
                reference=self._synapse_references.structural_dynamics)

    def _write_synapse_parameters(
            self, spec: DataSpecificationBase,
            ring_buffer_shifts: Sequence[int]):
        """
        Write the synapse parameters data region.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        # Reserve space
        spec.reserve_memory_region(
            region=self._synapse_regions.synapse_params,
            size=self._pop_vertex.get_synapse_params_size(),
            label='SynapseParams',
            reference=self._synapse_references.synapse_params)

        # Get values
        n_neurons = self._max_atoms_per_core
        # We only count neuron synapse types here, as this is related to
        # the ring buffers
        n_synapse_types = self._pop_vertex.neuron_impl.get_n_synapse_types()
        max_delay = self._pop_vertex.splitter.max_support_delay()

        # Write synapse parameters
        spec.switch_write_focus(self._synapse_regions.synapse_params)
        spec.write_value(n_neurons)
        spec.write_value(n_synapse_types)
        spec.write_value(get_n_bits(n_neurons))
        spec.write_value(get_n_bits(n_synapse_types))
        spec.write_value(get_n_bits(max_delay))
        spec.write_value(int(self._pop_vertex.drop_late_spikes))
        spec.write_value(self._pop_vertex.incoming_spike_buffer_size)
        spec.write_array(ring_buffer_shifts)

    @overrides(AbstractSynapseExpandable.gen_on_machine)
    def gen_on_machine(self) -> bool:
        return self._synaptic_matrices.gen_on_machine

    @overrides(AbstractSynapseExpandable.read_generated_connection_holders)
    def read_generated_connection_holders(self, placement: Placement):
        self._synaptic_matrices.read_generated_connection_holders(placement)

    @property
    @overrides(AbstractSynapseExpandable.connection_generator_region)
    def connection_generator_region(self) -> int:
        return self._synapse_regions.connection_builder

    def get_connections_from_machine(
            self, placement: Placement, app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> Sequence[NDArray]:
        """
        Get the connections from the machine for this vertex.

        :param ~pacman.model.placements.Placement placements:
            Where the connection data is on the machine
        :param ProjectionApplicationEdge app_edge:
            The edge for which the data is being read
        :param SynapseInformation synapse_info:
            The specific projection within the edge
        :rtype: list(~numpy.ndarray)
        """
        return self._synaptic_matrices.get_connections_from_machine(
            placement, app_edge, synapse_info)

    @property
    @overrides(AbstractSynapseExpandable.max_gen_data)
    def max_gen_data(self) -> int:
        return self._synaptic_matrices.max_gen_data

    @property
    @overrides(AbstractSynapseExpandable.bit_field_size)
    def bit_field_size(self) -> int:
        return self._synaptic_matrices.bit_field_size
