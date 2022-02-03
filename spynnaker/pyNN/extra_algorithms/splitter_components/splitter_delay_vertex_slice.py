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
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    AbstractPartitionerConstraint)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.utilities import utility_calls
from pacman.utilities.algorithm_utilities.\
    partition_algorithm_utilities import (
        get_remaining_constraints)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, BYTES_PER_WORD)
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionVertex, DelayExtensionMachineVertex)


class SplitterDelayVertexSlice(AbstractSplitterCommon):
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

    NEED_EXACT_ERROR_MESSAGE = (
        "DelayExtensionsSplitters need exact incoming slices. Please fix "
        "and try again")

    DELAY_RECORDING_ERROR = (
        "The delay extensions does not record any variables. Therefore "
        "asking for them is deemed an error.")

    def __init__(self):
        """ splitter for delay extensions

        """
        super().__init__(self.SPLITTER_NAME)
        self._machine_vertex_by_slice = dict()

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return list(self._governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex, partition_id):
        # Only connect to the source that matches the slice
        return [
            (self._machine_vertex_by_slice[m_vertex.vertex_slice], [m_vertex])
            for m_vertex in source_vertex.splitter.get_out_going_vertices(
                partition_id)]

    def create_machine_vertices(self, chip_counter):
        # pylint: disable=arguments-differ
        source_app_vertex = self._governed_app_vertex.source_vertex
        slices = source_app_vertex.splitter.get_out_going_slices()
        constraints = get_remaining_constraints(self._governed_app_vertex)

        # create vertices correctly
        for vertex_slice in slices:
            vertex = self.create_machine_vertex(
                source_app_vertex, vertex_slice, constraints)
            self._governed_app_vertex.remember_machine_vertex(vertex)
            chip_counter.add_core(vertex.resources_required)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        other_splitter = self._governed_app_vertex.source_vertex.splitter
        return other_splitter.get_in_coming_slices()

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        other_splitter = self._governed_app_vertex.source_vertex.splitter
        return other_splitter.get_out_going_slices()

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, DelayExtensionVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    def create_machine_vertex(
            self, source_app_vertex, vertex_slice, remaining_constraints):
        """ creates a delay extension machine vertex and adds to the tracker.

        :param MachineVertex source_vertex: The source of the delay
        :param remaining_constraints: none partitioner constraints.
        :type remaining_constraints:
            iterable(~pacman.model.constraints.AbstractConstraint)
        :return: machine vertex
        :rtype: DelayExtensionMachineVertex
        """
        label = f"Delay extension for {source_app_vertex}"
        resources = self.get_resources_used_by_atoms(vertex_slice)

        machine_vertex = DelayExtensionMachineVertex(
            resources, label, vertex_slice, remaining_constraints,
            self._governed_app_vertex)

        self._machine_vertex_by_slice[vertex_slice] = machine_vertex
        return machine_vertex

    def get_resources_used_by_atoms(self, vertex_slice):
        """ ger res for a APV

        :param vertex_slice: the slice
        :rtype: ResourceContainer
        """
        constant_sdram = self.constant_sdram()

        # set resources required from this object
        container = ResourceContainer(
            sdram=constant_sdram,
            dtcm=self.dtcm_cost(vertex_slice),
            cpu_cycles=self.cpu_cost(vertex_slice))

        # return the total resources.
        return container

    def constant_sdram(self):
        """ returns the sdram used by the delay extension

        :param ApplicationGraph graph: app graph
        :param Slice vertex_slice: The slice to get the size of
        :rtype: ConstantSDRAM
        """
        return ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            self._governed_app_vertex.delay_params_size() +
            self._governed_app_vertex.tdma_sdram_size_in_bytes +
            DelayExtensionMachineVertex.get_provenance_data_size(
                DelayExtensionMachineVertex.N_EXTRA_PROVENANCE_DATA_ENTRIES))

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

    @overrides(AbstractSplitterCommon.check_supported_constraints)
    def check_supported_constraints(self):
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        raise PacmanInvalidParameterException(
            variable_to_record, variable_to_record, self.DELAY_RECORDING_ERROR)

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        self._machine_vertex_by_slice = dict()

    def get_machine_vertex(self, vertex_slice):
        """ Get a delay extension machine vertex for a given vertex slice

        :param Slice vertex_slice: The slice to get the data for
        :rtype: DelayExtensionMachineVertex
        """
        return self._machine_vertex_by_slice[vertex_slice]
