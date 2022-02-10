# Copyright (c) 2017-2020The University of Manchester
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
from collections import namedtuple

from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import abstractproperty

from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration,
    AbstractSupportsBitFieldRoutingCompression)

from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.utilities import bit_field_utilities
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, HasSynapses)

from .population_machine_synapses_provenance import (
    PopulationMachineSynapsesProvenance)

# Identifiers for synapse regions
SYNAPSE_FIELDS = [
    "synapse_params", "direct_matrix", "pop_table", "synaptic_matrix",
    "synapse_dynamics", "structural_dynamics", "bitfield_builder",
    "bitfield_key_map", "bitfield_filter", "connection_builder"]
SynapseRegions = namedtuple(
    "SynapseRegions", SYNAPSE_FIELDS)

SynapseReferences = namedtuple(
    "SynapseReferences",
    ["direct_matrix_ref", "pop_table_ref", "synaptic_matrix_ref",
     "bitfield_filter_ref"])


class PopulationMachineSynapses(
        PopulationMachineSynapsesProvenance,
        AbstractSupportsBitFieldGeneration,
        AbstractSupportsBitFieldRoutingCompression,
        AbstractSynapseExpandable,
        HasSynapses, allow_derivation=True):
    """ Mix-in for machine vertices that contain synapses
    """

    # This MUST stay empty to allow mixing with other things with slots
    __slots__ = []

    @abstractproperty
    def _app_vertex(self):
        """ The application vertex of the machine vertex.

        :note: This is likely to be available via the MachineVertex.

        :rtype: AbstractPopulationVertex
        """

    @abstractproperty
    def _vertex_slice(self):
        """ The slice of the application vertex atoms on this machine vertex.

        :note: This is likely to be available via the MachineVertex.

        :rtype: ~pacman.model.graphs.common.Slice
        """

    @abstractproperty
    def _synaptic_matrices(self):
        """ The object holding synaptic matrices

        :rtype: SynapticMatrices
        """

    @abstractproperty
    def _synapse_regions(self):
        """ The identifiers of synaptic regions

        :rtype: .SynapseRegions
        """

    @abstractproperty
    def _max_atoms_per_core(self):
        """ The maximum number of atoms on any core targetted by these synapses

        :rtype: int
        """

    @property
    def _synapse_references(self):
        """ The references to synapse regions.  Override to provide these.

        :rtype: .SynapseRegions
        """
        return SynapseRegions(*[None for _ in range(len(SYNAPSE_FIELDS))])

    @overrides(AbstractSupportsBitFieldGeneration.bit_field_base_address)
    def bit_field_base_address(self, transceiver, placement):
        return locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self._synapse_regions.bitfield_filter)

    @overrides(AbstractSupportsBitFieldRoutingCompression.
               key_to_atom_map_region_base_address)
    def key_to_atom_map_region_base_address(self, transceiver, placement):
        return locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self._synapse_regions.bitfield_key_map)

    @overrides(AbstractSupportsBitFieldGeneration.bit_field_builder_region)
    def bit_field_builder_region(self, transceiver, placement):
        return locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self._synapse_regions.bitfield_builder)

    @overrides(AbstractSupportsBitFieldRoutingCompression.
               regeneratable_sdram_blocks_and_sizes)
    def regeneratable_sdram_blocks_and_sizes(self, transceiver, placement):
        synaptic_matrix_base_address = locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self._synapse_regions.synaptic_matrix)
        return [(
            self._synaptic_matrices.host_generated_block_addr +
            synaptic_matrix_base_address,
            self._synaptic_matrices.on_chip_generated_matrix_size)]

    def _write_synapse_data_spec(
            self, spec, routing_info, ring_buffer_shifts, weight_scales,
            structural_sz):
        """ Write the data specification for the synapse data

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            The routing information to read the key from
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        :param list(int) weight_scales:
            The scaling to apply to weights to store them in the synapses
        :param int all_syn_block_sz: The maximum size of the synapses in bytes
        :param int structural_sz: The size of the structural data
        :param int n_neuron_bits: The number of bits to use for neuron ids
        """
        # Get incoming projections
        incoming = self._app_vertex.incoming_projections

        # Write the synapse parameters
        self._write_synapse_parameters(spec, ring_buffer_shifts)

        # Write the synaptic matrices
        self._synaptic_matrices.generate_data(routing_info)
        self._synaptic_matrices.write_synaptic_data(
            spec, self._vertex_slice, self._synapse_references.synaptic_matrix,
            self._synapse_references.direct_matrix,
            self._synapse_references.pop_table,
            self._synapse_references.connection_builder)

        # Write any synapse dynamics
        synapse_dynamics = self._app_vertex.synapse_dynamics
        synapse_dynamics_sz = self._app_vertex.get_synapse_dynamics_size(
            self._vertex_slice.n_atoms)
        if synapse_dynamics_sz > 0:
            spec.reserve_memory_region(
                region=self._synapse_regions.synapse_dynamics,
                size=synapse_dynamics_sz, label='synapseDynamicsParams',
                reference=self._synapse_references.synapse_dynamics)
            synapse_dynamics.write_parameters(
                spec, self._synapse_regions.synapse_dynamics,
                self._app_vertex.weight_scale, weight_scales)
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
                weight_scales, self._app_vertex, self._vertex_slice,
                routing_info, self._synaptic_matrices)
        elif self._synapse_references.structural_dynamics is not None:
            # If there is a reference for this region, we have to create it!
            spec.reserve_memory_region(
                region=self._synapse_regions.structural_dynamics,
                size=4, label='synapseDynamicsStructuralParams',
                reference=self._synapse_references.structural_dynamics)

        size = bit_field_utilities.get_estimated_sdram_for_bit_field_region(
            incoming)
        bit_field_header = bit_field_utilities.get_bitfield_builder_data(
            self._synapse_regions.pop_table,
            self._synapse_regions.synaptic_matrix,
            self._synapse_regions.direct_matrix,
            self._synapse_regions.bitfield_filter,
            self._synapse_regions.bitfield_key_map,
            self._synapse_regions.structural_dynamics,
            isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural))
        bit_field_key_map = bit_field_utilities.get_bitfield_key_map_data(
            incoming, routing_info)
        bit_field_utilities.write_bitfield_init_data(
            spec,  self._synapse_regions.bitfield_builder, bit_field_header,
            self._synapse_regions.bitfield_key_map, bit_field_key_map,
            self._synapse_regions.bitfield_filter, size,
            self._synapse_references.bitfield_builder,
            self._synapse_references.bitfield_key_map,
            self._synapse_references.bitfield_filter)

    def _write_synapse_parameters(self, spec, ring_buffer_shifts):
        """ Write the synapse parameters data region

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        # Reserve space
        spec.reserve_memory_region(
            region=self._synapse_regions.synapse_params,
            size=self._app_vertex.get_synapse_params_size(),
            label='SynapseParams',
            reference=self._synapse_references.synapse_params)

        # Get values
        n_neurons = self._vertex_slice.n_atoms
        # We only count neuron synapse types here, as this is related to
        # the ring buffers
        n_synapse_types = self._app_vertex.neuron_impl.get_n_synapse_types()
        max_delay = self._app_vertex.splitter.max_support_delay()

        # Write synapse parameters
        spec.switch_write_focus(self._synapse_regions.synapse_params)
        spec.write_value(n_neurons)
        spec.write_value(n_synapse_types)
        spec.write_value(get_n_bits(n_neurons))
        spec.write_value(get_n_bits(n_synapse_types))
        spec.write_value(get_n_bits(max_delay))
        spec.write_value(int(self._app_vertex.drop_late_spikes))
        spec.write_value(self._app_vertex.incoming_spike_buffer_size)
        spec.write_array(ring_buffer_shifts)

    @overrides(AbstractSynapseExpandable.gen_on_machine)
    def gen_on_machine(self):
        return self._synaptic_matrices.gen_on_machine

    @overrides(AbstractSynapseExpandable.read_generated_connection_holders)
    def read_generated_connection_holders(self, transceiver, placement):
        self._synaptic_matrices.read_generated_connection_holders(
            transceiver, placement, self._vertex_slice)

    @property
    @overrides(AbstractSynapseExpandable.connection_generator_region)
    def connection_generator_region(self):
        return self._synapse_regions.connection_builder

    def get_connections_from_machine(
            self, transceiver, placement, app_edge, synapse_info):
        """ Get the connections from the machine for this vertex.

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the connection data
        :param ~pacman.model.placement.Placement placements:
            Where the connection data is on the machine
        :param ProjectionApplicationEdge app_edge:
            The edge for which the data is being read
        :param SynapseInformation synapse_info:
            The specific projection within the edge
        """
        return self._synaptic_matrices.get_connections_from_machine(
            transceiver, placement, app_edge, synapse_info, self._vertex_slice)
