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
import math
from pacman.executor.injection_decorator import inject_items
from pacman.model.partitioner_interfaces import AbstractSplitterCommon
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.model.partitioner_splitters.abstract_splitters.\
    abstract_splitter_slice import AbstractSplitterSlice
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, BYTES_PER_WORD)
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.exceptions import SpynnakerSplitterConfigurationException
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    AbstractSpynnakerSplitterDelay)
from spynnaker.pyNN.models.neural_projections import (
    DelayedApplicationEdge, DelayAfferentMachineEdge, DelayedMachineEdge)
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionVertex, DelayExtensionMachineVertex)
from spynnaker.pyNN.models.utility_models.delays.delay_generator_data import (
    DelayGeneratorData)


class SplitterDelayVertexSlice(AbstractSplitterSlice):
    """ handles the splitting of the DelayExtensionVertex via slice logic.
    """

    __slots__ = ["_machine_vertex_by_slice"]

    ESTIMATED_CPU_CYCLES = 128
    WORDS_PER_ATOM = 11 + 16
    _EXPANDER_BASE_PARAMS_SIZE = 3 * BYTES_PER_WORD

    SPLITTER_NAME = "SplitterDelayVertexSlice"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterDelayVertexSlice as"
        " the only vertex supported by this splitter is a "
        "DelayExtensionVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        AbstractSplitterSlice.__init__(self, self.SPLITTER_NAME)
        AbstractSpynnakerSplitterDelay.__init__(self)
        self._machine_vertex_by_slice = dict()

    @overrides(AbstractSplitterCommon.get_pre_vertices)
    def get_pre_vertices(self, edge, outgoing_edge_partition):
        return self._get_map([DelayedMachineEdge])

    @overrides(AbstractSplitterCommon.get_post_vertices)
    def get_post_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        return {
            self._machine_vertex_by_slice[
                src_machine_vertex.vertex_slice]: [DelayAfferentMachineEdge]}

    @overrides(AbstractSplitterSlice.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterSlice.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, DelayExtensionVertex):
            raise SpynnakerSplitterConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterSlice.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources, label, remaining_constraints):
        machine_vertex = DelayExtensionMachineVertex(
            resources, label, remaining_constraints,
            self._governed_app_vertex, vertex_slice)
        self._machine_vertex_by_slice[vertex_slice] = machine_vertex
        return machine_vertex

    @inject_items({
        "graph": "MemoryApplicationGraph",
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(AbstractSplitterSlice.get_resources_used_by_atoms,
               additional_arguments={"graph", "machine_time_step"})
    def get_resources_used_by_atoms(
            self, vertex_slice, graph, machine_time_step):
        """ ger res for a APV

        :param vertex_slice: the slice
        :param graph: app graph
        :param machine_time_step: machine time step
        :rtype: ResourceContainer
        """
        constant_sdram = self.constant_sdram(graph)

        # set resources required from this object
        container = ResourceContainer(
            sdram=constant_sdram,
            dtcm=self.dtcm_cost(vertex_slice),
            cpu_cycles=self.cpu_cost(vertex_slice))

        # return the total resources.
        return container

    def constant_sdram(self, graph):
        """ returns the sdram used by the delay extension

        :param ApplicationGraph graph: app graph
        :rtype: ConstantSDRAM
        """
        out_edges = graph.get_edges_starting_at_vertex(self)
        return ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            self._governed_app_vertex.tdma_sdram_size_in_bytes +
            DelayExtensionMachineVertex.get_provenance_data_size(
                DelayExtensionMachineVertex.N_EXTRA_PROVENANCE_DATA_ENTRIES) +
            self._get_size_of_generator_information(out_edges))

    def dtcm_cost(self, vertex_slice):
        """ returns the dtcm used by the delay extension slice.

        :param Slice vertex_slice: vertex slice
        :rtype: DTCMResource
        """
        return DTCMResource(
            self.WORDS_PER_ATOM * BYTES_PER_WORD * vertex_slice.n_atoms)

    def cpu_cost(self, vertex_slice):
        """ returns the cpu cost of the delay extension for a slice of atoms

        :param Slice vertex_slice: slice of atoms
        :rtype: CPUCyclesPerTickResource
        """
        return CPUCyclesPerTickResource(
            self.ESTIMATED_CPU_CYCLES * vertex_slice.n_atoms)

    def _get_size_of_generator_information(self, out_edges):
        """ Get the size of the generator data for all edges

        :param list(.ApplicationEdge) out_edges:
        :rtype: int
        """
        gen_on_machine = False
        size = 0
        for out_edge in out_edges:
            if isinstance(out_edge, DelayedApplicationEdge):
                for synapse_info in out_edge.synapse_information:

                    # Get the number of likely vertices
                    max_atoms = out_edge.post_vertex.get_max_atoms_per_core()
                    if out_edge.post_vertex.n_atoms < max_atoms:
                        max_atoms = out_edge.post_vertex.n_atoms
                    n_edge_vertices = int(math.ceil(
                        out_edge.post_vertex.n_atoms / float(max_atoms)))

                    # Get the size
                    gen_size = self._get_edge_generator_size(synapse_info)
                    if gen_size > 0:
                        gen_on_machine = True
                        size += gen_size * n_edge_vertices
        if gen_on_machine:
            size += self._EXPANDER_BASE_PARAMS_SIZE
        return size

    @staticmethod
    def _get_edge_generator_size(synapse_info):
        """ Get the size of the generator data for a given synapse info object

        :param SynapseInformation synapse_info: the synapse info
        """
        connector = synapse_info.connector
        dynamics = synapse_info.synapse_dynamics
        connector_gen = (isinstance(
            connector, AbstractGenerateConnectorOnMachine) and
            connector.generate_on_machine(
                synapse_info.weights, synapse_info.delays))
        synapse_gen = isinstance(
            dynamics, AbstractGenerateOnMachine)
        if connector_gen and synapse_gen:
            return sum((
                DelayGeneratorData.BASE_SIZE,
                connector.gen_delay_params_size_in_bytes(
                    synapse_info.delays),
                connector.gen_connector_params_size_in_bytes))
        return 0
