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
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    AbstractPartitionerConstraint)
from pacman.model.graphs.machine import MachineEdge
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterSlice)
from pacman.utilities import utility_calls
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, PopulationMachineVertex)
from spynnaker.pyNN.models.neuron.population_machine_vertex import (
    NeuronProvenance, SynapseProvenance)
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay


class SplitterAbstractPopulationVertexSlice(
        AbstractSplitterSlice, AbstractSpynnakerSplitterDelay):
    """ handles the splitting of the AbstractPopulationVertex via slice logic.
    """

    __slots__ = []

    SPLITTER_NAME = "SplitterAbstractPopulationVertexSlice"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopulationVertexSlice as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        AbstractSplitterSlice.__init__(self, self.SPLITTER_NAME)
        AbstractSpynnakerSplitterDelay.__init__(self)

    @overrides(AbstractSplitterSlice.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterSlice.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterSlice.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return self._get_map([MachineEdge])

    @overrides(AbstractSplitterSlice.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        return self._get_map([MachineEdge])

    @overrides(AbstractSplitterSlice.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources, label, remaining_constraints):
        return PopulationMachineVertex(
            resources, label, remaining_constraints, self._governed_app_vertex,
            vertex_slice)

    @overrides(AbstractSplitterSlice.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        """  Gets the resources of a slice of atoms from a given app vertex.

        :param Slice vertex_slice: the slice
        :param MachineGraph graph: app graph
        :rtype: ResourceContainer
        """
        variable_sdram = self.__get_variable_sdram(vertex_slice)
        constant_sdram = self.__get_constant_sdram(vertex_slice)

        # set resources required from this object
        container = ResourceContainer(
            sdram=variable_sdram + constant_sdram,
            dtcm=self.__get_dtcm_cost(vertex_slice),
            cpu_cycles=self.__get_cpu_cost(vertex_slice))

        # return the total resources.
        return container

    def __get_variable_sdram(self, vertex_slice):
        """ returns the variable sdram from the recorder.

        :param Slice vertex_slice: the atom slice for recording sdram
        :return: the variable sdram used by the neuron recorder
        :rtype: VariableSDRAM
        """

        return (
            self._governed_app_vertex.get_neuron_variable_sdram(vertex_slice) +
            self._governed_app_vertex.get_synapse_variable_sdram(vertex_slice))

    def __get_constant_sdram(self, vertex_slice):
        """ returns the constant sdram used by the vertex slice.

        :param Slice vertex_slice: the atoms to get constant sdram of
        :rtype: ConstantSDRAM
        """
        n_record = (
            len(self._governed_app_vertex.neuron_recordables) +
            len(self._governed_app_vertex.synapse_recordables))
        n_provenance = NeuronProvenance.N_ITEMS + SynapseProvenance.N_ITEMS
        return ConstantSDRAM(
            self._governed_app_vertex.get_common_constant_sdram(
                n_record, n_provenance) +
            self._governed_app_vertex.get_neuron_constant_sdram(vertex_slice) +
            self._governed_app_vertex.get_synapse_constant_sdram(vertex_slice))

    def __get_dtcm_cost(self, vertex_slice):
        """ get the dtcm cost for the slice of atoms

        :param Slice vertex_slice: atom slice for dtcm calc.
        :rtype: DTCMResource
        """
        return DTCMResource(
            self._governed_app_vertex.get_common_dtcm() +
            self._governed_app_vertex.get_neuron_dtcm(vertex_slice) +
            self._governed_app_vertex.get_synapse_dtcm(vertex_slice))

    def __get_cpu_cost(self, vertex_slice):
        """ get cpu cost for a slice of atoms

        :param Slice vertex_slice: slice of atoms
        :rtype: CPUCyclesPerTickResourcer
        """
        return CPUCyclesPerTickResource(
            self._governed_app_vertex.get_common_cpu() +
            self._governed_app_vertex.get_neuron_cpu(vertex_slice) +
            self._governed_app_vertex.get_synapse_cpu(vertex_slice))

    @overrides(AbstractSplitterSlice.check_supported_constraints)
    def check_supported_constraints(self):
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)
