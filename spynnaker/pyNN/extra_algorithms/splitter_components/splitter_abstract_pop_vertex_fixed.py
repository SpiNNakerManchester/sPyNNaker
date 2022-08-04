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
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import MultiRegionSDRAM
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.utilities.algorithm_utilities\
    .partition_algorithm_utilities import get_remaining_constraints
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, PopulationMachineVertex)
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
from pacman.model.graphs.common.slice import Slice


class SplitterAbstractPopulationVertexFixed(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay):
    """ handles the splitting of the AbstractPopulationVertex using fixed
        slices
    """

    __slots__ = [
        # The pre-calculated slices of the vertex
        "__slices"
    ]

    """ The name of the splitter """
    SPLITTER_NAME = "SplitterAbstractPopulationVertexFixed"

    """ The message to use when the Population is invalid """
    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopulationVertexFixed as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        super().__init__(self.SPLITTER_NAME)
        self.__slices = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self._governed_app_vertex
        app_vertex.synapse_recorder.add_region_offset(
            len(app_vertex.neuron_recorder.get_recordable_variables()))

        max_atoms_per_core = min(
            app_vertex.get_max_atoms_per_core(), app_vertex.n_atoms)

        projections = app_vertex.incoming_projections
        constraints = get_remaining_constraints(app_vertex)
        ring_buffer_shifts = app_vertex.get_ring_buffer_shifts(projections)
        weight_scales = app_vertex.get_weight_scales(ring_buffer_shifts)
        all_syn_block_sz = app_vertex.get_synapses_size(
            max_atoms_per_core, projections)
        structural_sz = app_vertex.get_structural_dynamics_size(
            max_atoms_per_core, projections)
        sdram = self.get_sdram_used_by_atoms(
            max_atoms_per_core, all_syn_block_sz, structural_sz)

        self.__create_slices()

        for index, vertex_slice in enumerate(self.__slices):
            chip_counter.add_core(sdram)
            label = f"Slice {vertex_slice} of {app_vertex.label}"
            machine_vertex = self.create_machine_vertex(
                vertex_slice, sdram, label, constraints, all_syn_block_sz,
                structural_sz, ring_buffer_shifts, weight_scales, index)
            self._governed_app_vertex.remember_machine_vertex(machine_vertex)

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
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        return self._governed_app_vertex.machine_vertices

    def create_machine_vertex(
            self, vertex_slice, sdram, label, remaining_constraints,
            all_syn_block_sz, structural_sz, ring_buffer_shifts,
            weight_scales, index):

        # Otherwise create a normal vertex
        return PopulationMachineVertex(
            sdram, label, remaining_constraints,
            self._governed_app_vertex, vertex_slice, index, ring_buffer_shifts,
            weight_scales, all_syn_block_sz, structural_sz)

    def get_sdram_used_by_atoms(
            self, n_atoms, all_syn_block_sz, structural_sz):
        """  Gets the resources of a slice of atoms

        :param int n_atoms
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

    def __get_constant_sdram(self, n_atoms, all_syn_block_sz, structural_sz):
        """ returns the constant sdram used by the atoms

        :param int n_atoms: The number of atoms to account for
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        n_record = (
            len(self._governed_app_vertex.neuron_recordables) +
            len(self._governed_app_vertex.synapse_recordables))

        n_provenance = NeuronProvenance.N_ITEMS + MainProvenance.N_ITEMS
        n_provenance += (
            SynapseProvenance.N_ITEMS + SpikeProcessingProvenance.N_ITEMS)

        sdram = MultiRegionSDRAM()
        sdram.merge(self._governed_app_vertex.get_common_constant_sdram(
            n_record, n_provenance,
            PopulationMachineVertex.COMMON_REGIONS))
        sdram.merge(self._governed_app_vertex.get_neuron_constant_sdram(
            n_atoms, PopulationMachineVertex.NEURON_REGIONS))
        sdram.merge(self.__get_synapse_constant_sdram(
            n_atoms, all_syn_block_sz, structural_sz))
        return sdram

    def __get_synapse_constant_sdram(
            self, n_atoms, all_syn_block_sz, structural_sz):

        """ Get the amount of fixed SDRAM used by synapse parts

        :param int n_atoms: The number of atoms to account for

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self._governed_app_vertex
        projections = self._governed_app_vertex.incoming_projections
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.synapse_params,
            app_vertex.get_synapse_params_size())
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.synapse_dynamics,
            app_vertex.get_synapse_dynamics_size(n_atoms))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.structural_dynamics,
            structural_sz)
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.synaptic_matrix,
            all_syn_block_sz)
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.direct_matrix,
            app_vertex.all_single_syn_size)
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.pop_table,
            MasterPopTableAsBinarySearch.get_master_population_table_size(
                projections))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.connection_builder,
            app_vertex.get_synapse_expander_size(projections))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.bitfield_filter,
            get_estimated_sdram_for_bit_field_region(projections))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.bitfield_key_map,
            get_estimated_sdram_for_key_region(projections))
        sdram.add_cost(
            PopulationMachineVertex.SYNAPSE_REGIONS.bitfield_builder,
            exact_sdram_for_bit_field_builder_region())
        return sdram

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        super(SplitterAbstractPopulationVertexFixed, self).reset_called()
        self.__slices = None

    def __create_slices(self):
        """ Create slices if not already done
        """
        if self.__slices is not None:
            return
        n_atoms = self._governed_app_vertex.n_atoms
        per_core = self._governed_app_vertex.get_max_atoms_per_core()
        self.__slices = [Slice(i, min(i + per_core - 1, n_atoms - 1))
                         for i in range(0, n_atoms, per_core)]

    @property
    def n_synapse_vertices(self):
        """ Return the number of synapse vertices per neuron vertex

        :rtype: int
        """
        return 1
