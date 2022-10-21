# Copyright (c) 2020-2021 The University of Manchester
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
from spinn_utilities.overrides import overrides
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import MultiRegionSDRAM
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
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
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_estimated_sdram_for_bit_field_region,
    get_estimated_sdram_for_key_region,
    exact_sdram_for_bit_field_builder_region)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.models.neuron.local_only import AbstractLocalOnly
from collections import defaultdict
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.exceptions import SynapticConfigurationException

# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14


class SplitterAbstractPopulationVertexFixed(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay):
    """ handles the splitting of the AbstractPopulationVertex using fixed
        slices
    """

    __slots__ = [
        # The pre-calculated ring buffer shifts
        "__ring_buffer_shifts",
        # The pre-calculated weight scales
        "__weight_scales",
        # The size of all the synapses on a core
        "__all_syn_block_sz",
        # The size of the structural plasticity data
        "__structural_sz",
        # The size of the synaptic expander data
        "__synapse_expander_sz",
        # The size of all the bitfield data
        "__bitfield_sz",
        # The next index to use for a synapse core
        "__next_index",
        # The pre-calculated slices of the vertex
        "__slices",
        # All the machine vertices
        "__vertices"
    ]

    """ The message to use when the Population is invalid """
    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopulationVertexFixed as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        super().__init__()
        self.__ring_buffer_shifts = None
        self.__weight_scales = None
        self.__all_syn_block_sz = dict()
        self.__structural_sz = dict()
        self.__synapse_expander_sz = None
        self.__bitfield_sz = None
        self.__next_index = 0
        self.__slices = None
        self.__vertices = list()

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self._governed_app_vertex

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

        self.__create_slices()
        for vertex_slice in self.__slices:
            sdram = self.get_sdram_used_by_atoms(vertex_slice)
            chip_counter.add_core(sdram)

            label = f"{app_vertex.label}{vertex_slice}"
            machine_vertex = self.create_machine_vertex(
                vertex_slice, sdram, label)
            self._governed_app_vertex.remember_machine_vertex(machine_vertex)
            self.__vertices.append(machine_vertex)

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
        return self.__vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return self.__vertices

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
        return self.__vertices

    def create_machine_vertex(
            self, vertex_slice, sdram, label):

        if self.__ring_buffer_shifts is None:
            app_vertex = self._governed_app_vertex
            if (hasattr(app_vertex, "rb_left_shifts") and
                    app_vertex.rb_left_shifts is not None):
                print("=" * 80)
                print("Using given values for RB left shifts.")
                self.__ring_buffer_shifts = app_vertex.rb_left_shifts
                print("RB left shifts for {:20}".format(app_vertex.label),
                      "=", self.__ring_buffer_shifts)
                print("-" * 80)
            else:
                print("=" * 80)
                print("Computing RB left shifts for", app_vertex.label)
                self.__ring_buffer_shifts = app_vertex.get_ring_buffer_shifts()
                print("RB left shifts for {:20}".format(app_vertex.label),
                      "=", self.__ring_buffer_shifts)
            self.__weight_scales = app_vertex.get_weight_scales(
                self.__ring_buffer_shifts)

        index = self.__next_index
        self.__next_index += 1

        # If using local-only create a local-only vertex
        s_dynamics = self._governed_app_vertex.synapse_dynamics
        if isinstance(s_dynamics, AbstractLocalOnly):
            return PopulationMachineLocalOnlyCombinedVertex(
                sdram, label, self._governed_app_vertex, vertex_slice, index,
                self.__ring_buffer_shifts, self.__weight_scales)

        # Otherwise create a normal vertex
        return PopulationMachineVertex(
            sdram, label, self._governed_app_vertex,
            vertex_slice, index, self.__ring_buffer_shifts,
            self.__weight_scales, self.__all_syn_block_size(vertex_slice),
            self.__structural_size(vertex_slice))

    def get_sdram_used_by_atoms(self, vertex_slice):
        """  Gets the resources of a slice of atoms
        :param int n_atoms
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        # pylint: disable=arguments-differ
        n_atoms = vertex_slice.n_atoms
        variable_sdram = self.__get_variable_sdram(n_atoms)
        constant_sdram = self.__get_constant_sdram(vertex_slice)
        sdram = MultiRegionSDRAM()
        sdram.nest(len(PopulationMachineVertex.REGIONS) + 1, variable_sdram)
        sdram.merge(constant_sdram)

        # return the total resources.
        return sdram

    def __get_variable_sdram(self, n_atoms):
        """ returns the variable sdram from the recorders
        :param int n_atoms: The number of atoms to account for
        :return: the variable sdram used by the neuron recorder
        :rtype: VariableSDRAM
        """
        s_dynamics = self._governed_app_vertex.synapse_dynamics
        if isinstance(s_dynamics, AbstractSynapseDynamicsStructural):
            max_rewires_per_ts = s_dynamics.get_max_rewires_per_ts()
            self._governed_app_vertex.synapse_recorder.set_max_rewires_per_ts(
                max_rewires_per_ts)

        return (
            self._governed_app_vertex.get_max_neuron_variable_sdram(n_atoms) +
            self._governed_app_vertex.get_max_synapse_variable_sdram(n_atoms))

    def __get_constant_sdram(self, vertex_slice):
        """ returns the constant sdram used by the vertex slice.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the atoms to get constant sdram of
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        s_dynamics = self._governed_app_vertex.synapse_dynamics
        n_record = (
            len(self._governed_app_vertex.neuron_recordables) +
            len(self._governed_app_vertex.synapse_recordables))

        n_provenance = NeuronProvenance.N_ITEMS + MainProvenance.N_ITEMS
        if isinstance(s_dynamics, AbstractLocalOnly):
            n_provenance += LocalOnlyProvenance.N_ITEMS
        else:
            n_provenance += (
                SynapseProvenance.N_ITEMS + SpikeProcessingProvenance.N_ITEMS)

        n_atoms = vertex_slice.n_atoms
        sdram = MultiRegionSDRAM()
        if isinstance(s_dynamics, AbstractLocalOnly):
            sdram.merge(self._governed_app_vertex.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineLocalOnlyCombinedVertex.COMMON_REGIONS))
            sdram.merge(self._governed_app_vertex.get_neuron_constant_sdram(
                n_atoms,
                PopulationMachineLocalOnlyCombinedVertex.NEURON_REGIONS))
            sdram.merge(self.__get_local_only_constant_sdram(n_atoms))
        else:
            sdram.merge(self._governed_app_vertex.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineVertex.COMMON_REGIONS))
            sdram.merge(self._governed_app_vertex.get_neuron_constant_sdram(
                n_atoms, PopulationMachineVertex.NEURON_REGIONS))
            sdram.merge(self.__get_synapse_constant_sdram(vertex_slice))
        return sdram

    def __get_local_only_constant_sdram(self, n_atoms):
        app_vertex = self._governed_app_vertex
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

    def __get_synapse_constant_sdram(self, vertex_slice):

        """ Get the amount of fixed SDRAM used by synapse parts
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        sdram = MultiRegionSDRAM()
        app_vertex = self._governed_app_vertex
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.synapse_params,
            app_vertex.get_synapse_params_size())
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.synapse_dynamics,
            app_vertex.get_synapse_dynamics_size(vertex_slice.n_atoms))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.structural_dynamics,
            self.__structural_size(vertex_slice))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.synaptic_matrix,
            self.__all_syn_block_size(vertex_slice))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.direct_matrix,
            app_vertex.direct_matrix_size)
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.pop_table,
            MasterPopTableAsBinarySearch.get_master_population_table_size(
                app_vertex.incoming_projections))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.connection_builder,
            self.__synapse_expander_size())
        sdram.merge(self.__bitfield_size())
        return sdram

    def __all_syn_block_size(self, vertex_slice):
        """ Work out how much SDRAM is needed for all the synapses

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :rtype: int
        """
        if vertex_slice in self.__all_syn_block_sz:
            return self.__all_syn_block_sz[vertex_slice]
        all_syn_block_sz = self._governed_app_vertex.get_synapses_size(
            vertex_slice.n_atoms)
        self.__all_syn_block_sz[vertex_slice] = all_syn_block_sz
        return all_syn_block_sz

    def __structural_size(self, vertex_slice):
        """ Work out how much SDRAM is needed by the structural plasticity data

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :rtype: int
        """
        if vertex_slice in self.__structural_sz:
            return self.__structural_sz[vertex_slice]
        structural_sz = self._governed_app_vertex.get_structural_dynamics_size(
            vertex_slice.n_atoms)
        self.__structural_sz[vertex_slice] = structural_sz
        return structural_sz

    def __synapse_expander_size(self):
        """ Work out how much SDRAM is needed for the synapse expander

        :rtype: int
        """
        if self.__synapse_expander_sz is None:
            self.__synapse_expander_sz = \
                self._governed_app_vertex.get_synapse_expander_size()
        return self.__synapse_expander_sz

    def __bitfield_size(self):
        """ Work out how much SDRAM is needed by the bit fields

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        if self.__bitfield_sz is None:
            sdram = MultiRegionSDRAM()
            sdram.add_cost(
                PopulationMachineVertex.SYNAPSE_REGIONS.bitfield_filter,
                get_estimated_sdram_for_bit_field_region(
                    self._governed_app_vertex.incoming_projections))
            sdram.add_cost(
                PopulationMachineVertex.SYNAPSE_REGIONS.bitfield_key_map,
                get_estimated_sdram_for_key_region(
                    self._governed_app_vertex.incoming_projections))
            sdram.add_cost(
                PopulationMachineVertex.SYNAPSE_REGIONS.bitfield_builder,
                exact_sdram_for_bit_field_builder_region())
            self.__bitfield_sz = sdram
        return self.__bitfield_sz

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        super(SplitterAbstractPopulationVertexFixed, self).reset_called()
        self.__ring_buffer_shifts = None
        self.__weight_scales = None
        self.__all_syn_block_sz = dict()
        self.__structural_sz = dict()
        self.__next_index = 0
        self.__slices = None
        self.__vertices = list()

    def __create_slices(self):
        """ Create slices if not already done
        """
        if self.__slices is not None:
            return
        self.__slices = get_multidimensional_slices(self._governed_app_vertex)
