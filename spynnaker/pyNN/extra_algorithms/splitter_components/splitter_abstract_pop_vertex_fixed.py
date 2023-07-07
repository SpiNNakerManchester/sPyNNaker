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
from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import MultiRegionSDRAM
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.utilities.algorithm_utilities\
    .partition_algorithm_utilities import get_multidimensional_slices
from pacman.utilities.utility_calls import get_n_bits_for_fields
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, PopulationMachineVertex,
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
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay

# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14


class SplitterAbstractPopulationVertexFixed(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay):
    """
    Handles the splitting of the :py:class:`AbstractPopulationVertex`
    using fixed slices.
    """

    __slots__ = [
        # The pre-calculated slices of the vertex
        "__slices",
        "__max_delay",
        "__expect_delay_extension"
    ]

    def __init__(self):
        super().__init__()
        self.__slices = None
        self.__max_delay = None
        self.__expect_delay_extension = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                f"The vertex {app_vertex} cannot be supported by the "
                "SplitterAbstractPopulationVertexFixed as the only vertex "
                "supported by this splitter is a AbstractPopulationVertex. "
                "Please use the correct splitter for your vertex and try "
                "again.")

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self.governed_app_vertex

        # Do some checks to make sure everything is likely to fit
        field_sizes = [
            min(max_atoms, n) for max_atoms, n in zip(
                app_vertex.get_max_atoms_per_dimension_per_core(),
                app_vertex.atoms_shape)]
        n_atom_bits = get_n_bits_for_fields(field_sizes)
        n_synapse_types = app_vertex.neuron_impl.get_n_synapse_types()
        if (n_atom_bits + get_n_bits(n_synapse_types) +
                get_n_bits(self.max_support_delay())) > MAX_RING_BUFFER_BITS:
            raise SynapticConfigurationException(
                "The combination of the number of neurons per core ({}), "
                "the number of synapse types ({}), and the maximum delay per "
                "core ({}) will require too much DTCM.  Please reduce one or "
                "more of these values.".format(
                    field_sizes, n_synapse_types, self.max_support_delay()))

        app_vertex.synapse_recorder.add_region_offset(
            len(app_vertex.neuron_recorder.get_recordable_variables()))

        max_atoms_per_core = min(
            app_vertex.get_max_atoms_per_core(), app_vertex.n_atoms)

        # spinncer_update code, using user-defined left-shifts
        # with weight_scale, use user-defined or calculated min_weights

        # ring_buffer_shifts = None
        # app_vertex = self._governed_app_vertex
        # if (hasattr(app_vertex, "rb_left_shifts") and
        #         app_vertex.rb_left_shifts is not None):
        #     print("=" * 80)
        #     print("Using given values for RB left shifts.")
        #     ring_buffer_shifts = app_vertex.rb_left_shifts
        #     print("RB left shifts for {:20}".format(app_vertex.label),
        #           "=", ring_buffer_shifts)
        #     print("-" * 80)
        # else:
        #     print("=" * 80)
        #     print("Computing RB left shifts for", app_vertex.label)
        #     ring_buffer_shifts = app_vertex.get_ring_buffer_shifts()
        #     print("RB left shifts for {:20}".format(app_vertex.label),
        #           "=", ring_buffer_shifts)

        min_weights = app_vertex.get_min_weights()
        weight_scales = app_vertex.get_weight_scales(min_weights)
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

        self.__create_slices()

        for index, vertex_slice in enumerate(self.__slices):
            chip_counter.add_core(sdram)
            label = f"{app_vertex.label}{vertex_slice}"
            machine_vertex = self.create_machine_vertex(
                vertex_slice, sdram, label,
                structural_sz, min_weights, weight_scales,
                index, max_atoms_per_core, synaptic_matrices, neuron_data)
            self.governed_app_vertex.remember_machine_vertex(machine_vertex)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        self.__create_slices()
        return self.__slices

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        self.__create_slices()
        return self.__slices

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex, partition_id):
        # Determine the real pre-vertex
        pre_vertex = source_vertex
        if isinstance(source_vertex, DelayExtensionVertex):
            pre_vertex = source_vertex.source_vertex

        # Use the real pre-vertex to get the projections
        targets = defaultdict(OrderedSet)
        for proj in self.governed_app_vertex.get_incoming_projections_from(
                pre_vertex):
            # pylint: disable=protected-access
            s_info = proj._synapse_information
            # Use the original source vertex to get the connected vertices,
            # as the real source machine vertices must make it in to this array
            for (tgt, srcs) in s_info.synapse_dynamics.get_connected_vertices(
                    s_info, source_vertex, self.governed_app_vertex):
                targets[tgt].update(srcs)
        return [(m_vertex, tgts) for m_vertex, tgts in targets.items()]

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return self.governed_app_vertex.machine_vertices

    def create_machine_vertex(
            self, vertex_slice, sdram, label,
            structural_sz, min_weights, weight_scales, index,
            max_atoms_per_core, synaptic_matrices, neuron_data):
        # if self.__min_weights is None:
        #     app_vertex = self._governed_app_vertex
        #     self.__min_weights = app_vertex.get_min_weights()
        #     self.__weight_scales = app_vertex.get_weight_scales(
        #         self.__min_weights)

        # If using local-only create a local-only vertex
        s_dynamics = self.governed_app_vertex.synapse_dynamics
        if isinstance(s_dynamics, AbstractLocalOnly):
            return PopulationMachineLocalOnlyCombinedVertex(
                sdram, label, self.governed_app_vertex, vertex_slice, index,
                min_weights, weight_scales, neuron_data, max_atoms_per_core)

        # Otherwise create a normal vertex
        return PopulationMachineVertex(
            sdram, label, self._governed_app_vertex,
            vertex_slice, index, min_weights, weight_scales,
            structural_sz, max_atoms_per_core, synaptic_matrices, neuron_data)

    def get_sdram_used_by_atoms(
            self, n_atoms, all_syn_block_sz, structural_sz):
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

    def __get_variable_sdram(self, n_atoms):
        """
        Returns the variable SDRAM from the recorders.

        :param int n_atoms: The number of atoms to account for
        :return: the variable SDRAM used by the neuron recorder
        :rtype: VariableSDRAM
        """
        s_dynamics = self.governed_app_vertex.synapse_dynamics
        if isinstance(s_dynamics, AbstractSynapseDynamicsStructural):
            max_rewires_per_ts = s_dynamics.get_max_rewires_per_ts()
            self.governed_app_vertex.synapse_recorder.set_max_rewires_per_ts(
                max_rewires_per_ts)

        return (
            self.governed_app_vertex.get_max_neuron_variable_sdram(n_atoms) +
            self.governed_app_vertex.get_max_synapse_variable_sdram(n_atoms))

    def __get_constant_sdram(self, n_atoms, all_syn_block_sz, structural_sz):
        """
        Returns the constant SDRAM used by the atoms.

        :param int n_atoms: The number of atoms to account for
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        s_dynamics = self.governed_app_vertex.synapse_dynamics
        n_record = (
            len(self.governed_app_vertex.neuron_recordables) +
            len(self.governed_app_vertex.synapse_recordables))

        n_provenance = NeuronProvenance.N_ITEMS + MainProvenance.N_ITEMS
        if isinstance(s_dynamics, AbstractLocalOnly):
            n_provenance += LocalOnlyProvenance.N_ITEMS
        else:
            n_provenance += (
                SynapseProvenance.N_ITEMS + SpikeProcessingProvenance.N_ITEMS)

        sdram = MultiRegionSDRAM()
        if isinstance(s_dynamics, AbstractLocalOnly):
            sdram.merge(self.governed_app_vertex.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineLocalOnlyCombinedVertex.COMMON_REGIONS))
            sdram.merge(self.governed_app_vertex.get_neuron_constant_sdram(
                n_atoms,
                PopulationMachineLocalOnlyCombinedVertex.NEURON_REGIONS))
            sdram.merge(self.__get_local_only_constant_sdram(n_atoms))
        else:
            sdram.merge(self.governed_app_vertex.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineVertex.COMMON_REGIONS))
            sdram.merge(self.governed_app_vertex.get_neuron_constant_sdram(
                n_atoms, PopulationMachineVertex.NEURON_REGIONS))
            sdram.merge(self.__get_synapse_constant_sdram(
                n_atoms, all_syn_block_sz, structural_sz))
        return sdram

    def __get_local_only_constant_sdram(self, n_atoms):
        app_vertex = self.governed_app_vertex
        s_dynamics = app_vertex.synapse_dynamics
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            PopulationMachineLocalOnlyCombinedVertex.REGIONS.LOCAL_ONLY.value,
            PopulationMachineLocalOnlyCombinedVertex.LOCAL_ONLY_SIZE)
        sdram.add_cost(
            (PopulationMachineLocalOnlyCombinedVertex.
             REGIONS.LOCAL_ONLY_PARAMS.value),
            s_dynamics.get_parameters_usage_in_bytes(
                n_atoms, app_vertex.incoming_projections))
        return sdram

    def __get_synapse_constant_sdram(
            self, n_atoms, all_syn_block_sz, structural_sz):
        """
        Get the amount of fixed SDRAM used by synapse parts.

        :param int n_atoms: The number of atoms to account for

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self.governed_app_vertex
        regions = PopulationMachineVertex.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.add_cost(regions.synapse_params,
                       app_vertex.get_synapse_params_size())
        sdram.add_cost(regions.synapse_dynamics,
                       app_vertex.get_synapse_dynamics_size(n_atoms))
        sdram.add_cost(regions.structural_dynamics, structural_sz)
        sdram.add_cost(regions.synaptic_matrix, all_syn_block_sz)
        sdram.add_cost(
            regions.pop_table,
            MasterPopTableAsBinarySearch.get_master_population_table_size(
                app_vertex.incoming_projections))
        sdram.add_cost(regions.connection_builder,
                       app_vertex.get_synapse_expander_size())
        sdram.add_cost(regions.bitfield_filter,
                       get_sdram_for_bit_field_region(
                           app_vertex.incoming_projections))
        return sdram

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        super(SplitterAbstractPopulationVertexFixed, self).reset_called()
        self.__slices = None
        self.__max_delay = None
        self.__expect_delay_extension = None

    def __create_slices(self):
        """
        Create slices if not already done.
        """
        if self.__slices is not None:
            return
        self.__slices = get_multidimensional_slices(self.governed_app_vertex)

    def __update_max_delay(self):
        # Find the maximum delay from incoming synapses
        self.__max_delay, self.__expect_delay_extension = \
            self.governed_app_vertex.get_max_delay(MAX_RING_BUFFER_BITS)

    @overrides(AbstractSpynnakerSplitterDelay.max_support_delay)
    def max_support_delay(self):
        if self.__max_delay is None:
            self.__update_max_delay()
        return self.__max_delay

    @overrides(AbstractSpynnakerSplitterDelay.accepts_edges_from_delay_vertex)
    def accepts_edges_from_delay_vertex(self):
        if self.__expect_delay_extension is None:
            self.__update_max_delay()
        if self.__expect_delay_extension:
            return True
        raise NotImplementedError(
            "This call was unexpected as it was calculated that "
            "the max needed delay was less that the max possible")
