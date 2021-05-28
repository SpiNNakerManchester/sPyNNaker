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
import os

from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    AbstractPartitionerConstraint)
from pacman.model.graphs.machine import MachineEdge
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterSlice)
from pacman.utilities import utility_calls
from spinn_front_end_common.interface.profiling import profile_utils
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT)
from spinn_front_end_common.utilities.globals_variables import get_simulator
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, PopulationMachineVertex)
from spynnaker.pyNN.utilities import bit_field_utilities
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)


class SplitterAbstractPopulationVertexSlice(
        AbstractSplitterSlice, AbstractSpynnakerSplitterDelay):
    """ handles the splitting of the AbstractPopulationVertex via slice logic.
    """

    __slots__ = []

    _NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
    _NEURON_BASE_N_CPU_CYCLES = 10
    _C_MAIN_BASE_N_CPU_CYCLES = 0

    SPLITTER_NAME = "SplitterAbstractPopulationVertexSlice"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopulationVertexSlice as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self):
        super().__init__(self.SPLITTER_NAME)

    @overrides(AbstractSplitterSlice.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        super().set_governed_app_vertex(app_vertex)
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
            resources,
            self._governed_app_vertex.neuron_recorder.recorded_ids_by_slice(
                vertex_slice),
            label, remaining_constraints, self._governed_app_vertex,
            vertex_slice,
            self._governed_app_vertex.synapse_manager.drop_late_spikes,
            self.__get_binary_file_name())

    @inject_items({"graph": "MemoryApplicationGraph"})
    @overrides(
        AbstractSplitterSlice.get_resources_used_by_atoms,
        additional_arguments=["graph"])
    def get_resources_used_by_atoms(self, vertex_slice, graph):
        """  Gets the resources of a slice of atoms from a given app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :param ~pacman.model.graphs.machine.MachineGraph graph: app graph
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        # pylint: disable=arguments-differ
        variable_sdram = self.get_variable_sdram(vertex_slice)
        constant_sdram = self.constant_sdram(vertex_slice, graph)

        # set resources required from this object
        container = ResourceContainer(
            sdram=variable_sdram + constant_sdram,
            dtcm=self.dtcm_cost(vertex_slice),
            cpu_cycles=self.cpu_cost(vertex_slice))

        # return the total resources.
        return container

    def get_variable_sdram(self, vertex_slice):
        """ returns the variable sdram from the recorder.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the atom slice for recording sdram
        :return: the variable sdram used by the neuron recorder
        :rtype: VariableSDRAM
        """
        s_dynamics = self._governed_app_vertex.synapse_manager.synapse_dynamics
        if isinstance(s_dynamics, AbstractSynapseDynamicsStructural):
            max_rewires_per_ts = s_dynamics.get_max_rewires_per_ts()
            self._governed_app_vertex.neuron_recorder.set_max_rewires_per_ts(
                max_rewires_per_ts)

        return self._governed_app_vertex.neuron_recorder.\
            get_variable_sdram_usage(vertex_slice)

    def constant_sdram(self, vertex_slice,  graph):
        """ returns the constant sdram used by the vertex slice.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the atoms to get constant sdram of
        :param ~pacman.model.graphs.application.ApplicationGraph graph:
            app graph
        :rtype: ConstantSDRAM
        """
        sdram_requirement = (
            SYSTEM_BYTES_REQUIREMENT +
            self._governed_app_vertex.get_sdram_usage_for_neuron_params(
                vertex_slice) +
            self._governed_app_vertex.neuron_recorder.get_static_sdram_usage(
                vertex_slice) +
            PopulationMachineVertex.get_provenance_data_size(
                len(PopulationMachineVertex.EXTRA_PROVENANCE_DATA_ENTRIES)) +
            self._governed_app_vertex.synapse_manager.get_sdram_usage_in_bytes(
                vertex_slice, graph, self._governed_app_vertex) +
            profile_utils.get_profile_region_size(
                self._governed_app_vertex.n_profile_samples) +
            bit_field_utilities.get_estimated_sdram_for_bit_field_region(
                graph, self._governed_app_vertex) +
            bit_field_utilities.get_estimated_sdram_for_key_region(
                graph, self._governed_app_vertex) +
            bit_field_utilities.exact_sdram_for_bit_field_builder_region())
        return ConstantSDRAM(sdram_requirement)

    def dtcm_cost(self, vertex_slice):
        """ get the dtcm cost for the slice of atoms

        :param Slice vertex_slice: atom slice for dtcm calc.
        :rtype: DTCMResource
        """
        return DTCMResource(
            self._governed_app_vertex.neuron_impl.get_dtcm_usage_in_bytes(
                vertex_slice.n_atoms) +
            self._governed_app_vertex.neuron_recorder.get_dtcm_usage_in_bytes(
                vertex_slice) +
            self._governed_app_vertex.synapse_manager.
            get_dtcm_usage_in_bytes())

    def cpu_cost(self, vertex_slice):
        """ get cpu cost for a slice of atoms

        :param Slice vertex_slice: slice of atoms
        :rtype: CPUCyclesPerTickResourcer
        """
        return CPUCyclesPerTickResource(
            self._NEURON_BASE_N_CPU_CYCLES + self._C_MAIN_BASE_N_CPU_CYCLES +
            (self._NEURON_BASE_N_CPU_CYCLES_PER_NEURON *
             vertex_slice.n_atoms) +
            self._governed_app_vertex.neuron_recorder.get_n_cpu_cycles(
                vertex_slice.n_atoms) +
            self._governed_app_vertex.neuron_impl.get_n_cpu_cycles(
                vertex_slice.n_atoms) +
            self._governed_app_vertex.synapse_manager.get_n_cpu_cycles())

    def __get_binary_file_name(self):
        """ returns the binary name for the machine vertices.

        :rtype: str
        """

        # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(
            self._governed_app_vertex.neuron_impl.binary_name)

        # Reunite title and extension and return
        return (
            binary_title +
            self._governed_app_vertex.synapse_manager.
            vertex_executable_suffix + binary_extension)

    @overrides(AbstractSplitterSlice.check_supported_constraints)
    def check_supported_constraints(self):
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)
