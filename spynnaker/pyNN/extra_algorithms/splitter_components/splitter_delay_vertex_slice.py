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

from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    AbstractPartitionerConstraint)
from pacman.model.graphs.machine import MachineEdge
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractDependentSplitter)
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities.\
    partition_algorithm_utilities import (
        get_remaining_constraints)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, BYTES_PER_WORD)
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.exceptions import SpynnakerSplitterConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neural_projections import DelayedApplicationEdge
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionVertex, DelayExtensionMachineVertex)
from spynnaker.pyNN.models.utility_models.delays.delay_generator_data import (
    DelayGeneratorData)


class SplitterDelayVertexSlice(AbstractDependentSplitter):
    """ handles the splitting of the DelayExtensionVertex via slice logic.
    """

    __slots__ = [
        "_machine_vertex_by_slice"]

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

    DELAY_EXTENSION_SLICE_LABEL = (
        "DelayExtensionsMachineVertex for {} with slice {}")

    NEED_EXACT_ERROR_MESSAGE = (
        "DelayExtensionsSplitters need exact incoming slices. Please fix "
        "and try again")

    DELAY_RECORDING_ERROR = (
        "The delay extensions does not record any variables. Therefore "
        "asking for them is deemed an error.")

    def __init__(self, other_splitter):
        """ splitter for delay extensions

        :param other_splitter: the other splitter to split slices via.
        """
        super().__init__(other_splitter, self.SPLITTER_NAME)
        self._machine_vertex_by_slice = dict()

    @overrides(AbstractDependentSplitter.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return self._get_map([MachineEdge])

    @property
    def source_of_delay_vertex(self):
        return self._other_splitter.governed_app_vertex

    @overrides(AbstractDependentSplitter.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):

        app_graph = SpynnakerDataView.get_runtime_graph()
        # pylint: disable=arguments-differ
        pre_slices, is_exact = self._other_splitter.get_out_going_slices()

        # check for exacts.
        if not is_exact:
            raise SpynnakerSplitterConfigurationException(
                self.NEED_EXACT_ERROR_MESSAGE)

        # create vertices correctly
        for index, vertex_slice in enumerate(pre_slices):
            vertex = self.create_machine_vertex(
                vertex_slice, index, resource_tracker,
                self.DELAY_EXTENSION_SLICE_LABEL.format(
                    self._other_splitter.governed_app_vertex, vertex_slice),
                get_remaining_constraints(self._governed_app_vertex),
                app_graph)
            machine_graph.add_vertex(vertex)

    @overrides(AbstractDependentSplitter.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self._other_splitter.get_in_coming_slices()

    @overrides(AbstractDependentSplitter.get_out_going_slices)
    def get_out_going_slices(self):
        return self._other_splitter.get_out_going_slices()

    @overrides(AbstractDependentSplitter.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        return {
            self._machine_vertex_by_slice[
                src_machine_vertex.vertex_slice]: [MachineEdge]}

    @overrides(AbstractDependentSplitter.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, DelayExtensionVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    def create_machine_vertex(
            self, vertex_slice, index, resource_tracker, label,
            remaining_constraints, graph):
        """ creates a delay extension machine vertex and adds to the tracker.

        :param Slice vertex_slice: vertex slice
        :param ResourceTracker resource_tracker: resources
        :param str label:  human readable label for machine vertex.
        :param remaining_constraints: none partitioner constraints.
        :type remaining_constraints:
            iterable(~pacman.model.constraints.AbstractConstraint)
        :param ApplicationGraph graph: the app graph
        :return: machine vertex
        :rtype: DelayExtensionMachineVertex
        """
        resources = self.get_resources_used_by_atoms(vertex_slice, graph)
        resource_tracker.allocate_constrained_resources(
            resources, self._governed_app_vertex.constraints)

        machine_vertex = DelayExtensionMachineVertex(
            resources, label, remaining_constraints,
            self._governed_app_vertex, vertex_slice, index)

        self._machine_vertex_by_slice[vertex_slice] = machine_vertex
        return machine_vertex

    def get_resources_used_by_atoms(self, vertex_slice, graph):
        """ ger res for a APV

        :param vertex_slice: the slice
        :param graph: app graph
        :rtype: ResourceContainer
        """
        constant_sdram = self.constant_sdram(graph, vertex_slice)

        # set resources required from this object
        container = ResourceContainer(
            sdram=constant_sdram,
            dtcm=self.dtcm_cost(vertex_slice),
            cpu_cycles=self.cpu_cost(vertex_slice))

        # return the total resources.
        return container

    def constant_sdram(self, graph, vertex_slice):
        """ returns the sdram used by the delay extension

        :param ApplicationGraph graph: app graph
        :param Slice vertex_slice: The slice to get the size of
        :rtype: ConstantSDRAM
        """
        out_edges = graph.get_edges_starting_at_vertex(self)
        return ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            self._governed_app_vertex.delay_params_size(vertex_slice) +
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
        synapse_gen = isinstance(dynamics, AbstractGenerateOnMachine)
        if connector_gen and synapse_gen:
            return sum((
                DelayGeneratorData.BASE_SIZE,
                connector.gen_delay_params_size_in_bytes(
                    synapse_info.delays),
                connector.gen_connector_params_size_in_bytes))
        return 0

    @overrides(AbstractDependentSplitter.check_supported_constraints)
    def check_supported_constraints(self):
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)

    @overrides(AbstractDependentSplitter.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        raise PacmanInvalidParameterException(
            variable_to_record, variable_to_record, self.DELAY_RECORDING_ERROR)

    @overrides(AbstractDependentSplitter.reset_called)
    def reset_called(self):
        self._machine_vertex_by_slice = dict()
