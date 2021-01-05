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
from collections import defaultdict
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine import (
    MachineEdge, SourceSegmentedSDRAMMachinePartition, SDRAMMachineEdge)
from spynnaker.pyNN.models.neuron import (
    PopulationNeuronsMachineVertex, PopulationSynapsesMachineVertex,
    NeuronProvenance, SynapseProvenance, AbstractPopulationVertex)
from spynnaker.pyNN.utilities.constants import SYNAPSE_SDRAM_PARTITION_ID
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay


class SplitterAbstractPopulationVertexNeuronsSynapses(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay):
    """ handles the splitting of the AbstractPopulationVertex via slice logic.
    """

    __slots__ = [
        "__neuron_vertices",
        "__synapse_vertices",
        "__synapse_verts_by_neuron",
        "__n_synapse_vertices",
        "__index"]

    SPLITTER_NAME = "SplitterAbstractPopulationVertexNeuronsSynapses"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopulationVertexSlice as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self, n_synapse_vertices=1):
        super(SplitterAbstractPopulationVertexNeuronsSynapses, self).__init__(
            self.SPLITTER_NAME)
        AbstractSpynnakerSplitterDelay.__init__(self)
        self.__n_synapse_vertices = n_synapse_vertices

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        self.__neuron_vertices = list()
        self.__synapse_vertices = list()
        self.__synapse_verts_by_neuron = defaultdict(list)
        self.__index = 0
        label = self._governed_app_vertex.label
        for vertex_slice in self.__get_fixed_slices():

            # Create the neuron an synapse vertices
            neuron_resources = self.__get_neuron_resources(vertex_slice)
            synapse_resources = self.__get_synapse_resources(vertex_slice)
            neuron_label = "{}_Neurons:{}-{}".format(
                label, vertex_slice.lo_atom, vertex_slice.hi_atom)
            neuron_vertex = PopulationNeuronsMachineVertex(
                neuron_resources, neuron_label, None,
                self._governed_app_vertex, vertex_slice)
            machine_graph.add_vertex(neuron_vertex)
            self.__neuron_vertices.append(neuron_vertex)
            synapse_vertices = list()
            self.__synapse_verts_by_neuron[neuron_vertex] = synapse_vertices
            for i in range(self.__n_synapse_vertices):
                synapse_label = "{}_Synapses:{}-{}({})".format(
                    label, vertex_slice.lo_atom, vertex_slice.hi_atom, i)
                synapse_vertex = PopulationSynapsesMachineVertex(
                    synapse_resources, synapse_label, None,
                    self._governed_app_vertex, vertex_slice)
                machine_graph.add_vertex(synapse_vertex)
                self.__synapse_vertices.append(synapse_vertex)
                synapse_vertices.append(synapse_vertex)

            # Create the SDRAM edge between the parts
            sdram_label = "SDRAM {}-->{}".format(synapse_label, neuron_label)
            sdram_partition = SourceSegmentedSDRAMMachinePartition(
                SYNAPSE_SDRAM_PARTITION_ID, sdram_label, synapse_vertices)
            machine_graph.add_outgoing_edge_partition(sdram_partition)
            neuron_vertex.set_sdram_partition(sdram_partition)
            for synapse_vertex in synapse_vertices:
                machine_graph.add_edge(
                    SDRAMMachineEdge(
                        synapse_vertex, neuron_vertex, sdram_label),
                    SYNAPSE_SDRAM_PARTITION_ID)
                synapse_vertex.set_sdram_partition(sdram_partition)

            # Allocate all the resources to ensure they all fit
            sdram_resources = ResourceContainer(sdram=ConstantSDRAM(
                sdram_partition.total_sdram_requirements()))
            resource_tracker.allocate_group_resources(
                [neuron_resources, synapse_resources, sdram_resources])

        return True

    def __get_fixed_slices(self):
        atoms_per_core = self._governed_app_vertex.get_max_atoms_per_core()
        n_atoms = self._governed_app_vertex.n_atoms
        return [Slice(low, min(low + atoms_per_core - 1, n_atoms - 1))
                for low in range(0, n_atoms, atoms_per_core)]

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self.__get_fixed_slices(), True

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self.__get_fixed_slices(), True

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return {v: [MachineEdge] for v in self.__neuron_vertices}

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        self.__index = (self.__index + 1) % self.__n_synapse_vertices
        return {v[self.__index]: [MachineEdge]
                for v in self.__synapse_verts_by_neuron.values()}

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        if self._governed_app_vertex.neuron_recorder.is_recordable(
                variable_to_record):
            return self.__neuron_vertices
        return self.__synapse_vertices

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        self.__neuron_vertices = None
        self.__synapse_vertices = None
        self.__synapse_verts_by_neuron = None

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
            sdram=variable_sdram + ConstantSDRAM(constant_sdram),
            dtcm=DTCMResource(dtcm),
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
            sdram=variable_sdram + ConstantSDRAM(constant_sdram),
            dtcm=DTCMResource(dtcm),
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles))

        # return the total resources.
        return container
