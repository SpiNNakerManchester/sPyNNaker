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
from pacman.model.resources import (
    ResourceContainer, DTCMResource, CPUCyclesPerTickResource)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex)
from spynnaker.pyNN.models.neuron.population_machine_vertex import (
    NeuronProvenance, SynapseProvenance)
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from spynnaker.pyNN.models.neuron.population_neurons_machine_vertex import PopulationNeuronsMachineVertex
from pacman.model.graphs.common.slice import Slice
from spynnaker.pyNN.models.neuron.population_synapses_machine_vertex import PopulationSynapsesMachineVertex


class SplitterAbstractPopulationVertexNeuronsSynapses(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay):
    """ handles the splitting of the AbstractPopulationVertex via slice logic.
    """

    __slots__ = []

    SPLITTER_NAME = "SplitterAbstractPopulationVertexNeuronsSynapses"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopulationVertexSlice as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        AbstractSpynnakerSplitterDelay.__init__(self)

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        atoms_per_core = self._governed_app_vertex.get_max_atoms_per_core()
        n_atoms = self._govered_app_vertex.n_atoms
        label = self._governed_app_vertex.label
        for low in range(0, n_atoms, atoms_per_core):
            high = min(low + atoms_per_core - 1, n_atoms - 1)
            vertex_slice = Slice(low, high)
            neuron_resources = self.__get_neuron_resources(vertex_slice)
            synapse_resources = self.__get_synapse_resources(vertex_slice)
            resource_tracker.allocate_group_resources([
                neuron_resources, synapse_resources])
            resource_tracker.allocate_resources(neuron_resources)
            neuron_label = "{}_Neurons:{}-{}".format(label, low, high)
            neuron_vertex = PopulationNeuronsMachineVertex(
                neuron_resources, neuron_label, None,
                self._governed_app_vertex, vertex_slice)
            machine_graph.add_machine_vertex(neuron_vertex)
            synapse_label = "{}_Synapses:{}-{}".format(label, low, high)
            synapse_vertex = PopulationSynapsesMachineVertex(
                neuron_resources, synapse_label, None,
                self._governed_app_vertex, vertex_slice)
            machine_graph.add_machine_vertex(synapse_vertex)

        self._called = True
        return True

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        AbstractSplitterCommon.get_in_coming_slices(self)

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        AbstractSplitterCommon.get_out_going_slices(self)

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        pass

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        pass

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        pass

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        AbstractSplitterCommon.reset_called(self)

    def __get_neuron_resources(self, vertex_slice):
        """  Gets the resources of the neurons of a slice of atoms from a given
             app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        n_record = len(self._governed_app_vertex.neuron_recordables)
        variable_sdram = self._governed_app_vertex.get_neuron_variable_sdram(
            vertex_slice)
        constant_sdram = self._governed_app_vertex.get_common_constant_sdram(
            n_record, NeuronProvenance.N_ITEMS)
        constant_sdram += self._governed_app_vertex.get_neuron_constant_sdram(
            vertex_slice)
        dtcm = self._governed_app_vertex.get_common_dtcm()
        dtcm += self._governed_app_vertex.get_neuron_dtcm(vertex_slice)
        cpu_cycles = self._governed_app_vertex.get_common_cpu()
        cpu_cycles += self._governed_app_vertex.get_neuron_cpu(vertex_slice)

        # set resources required from this object
        container = ResourceContainer(
            sdram=variable_sdram + constant_sdram, dtcm=DTCMResource(dtcm),
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles))

        # return the total resources.
        return container

    def __get_synapse_resources(self, vertex_slice):
        """  Gets the resources of the synapses of a slice of atoms from a
             given app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        n_record = len(self._governed_app_vertex.synapse_recordables)
        variable_sdram = self._governed_app_vertex.get_synapse_variable_sdram(
            vertex_slice)
        constant_sdram = self._governed_app_vertex.get_common_constant_sdram(
            n_record, SynapseProvenance.N_ITEMS)
        constant_sdram += self._governed_app_vertex.get_synapse_constant_sdram(
            vertex_slice)
        dtcm = self._governed_app_vertex.get_common_dtcm()
        dtcm += self._governed_app_vertex.get_synapse_dtcm(vertex_slice)
        cpu_cycles = self._governed_app_vertex.get_common_cpu()
        cpu_cycles += self._governed_app_vertex.get_synapse_cpu(vertex_slice)

        # set resources required from this object
        container = ResourceContainer(
            sdram=variable_sdram + constant_sdram, dtcm=dtcm,
            cpu_cycles=cpu_cycles)

        # return the total resources.
        return container
