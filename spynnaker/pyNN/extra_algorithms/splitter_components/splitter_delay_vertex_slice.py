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

from typing import Dict, Iterable, Sequence, Tuple
from spinn_utilities.overrides import overrides
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.model.resources import ConstantSDRAM
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, BYTES_PER_WORD)
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionVertex, DelayExtensionMachineVertex)
from pacman.utilities.utility_objs.chip_counter import ChipCounter
from pacman.model.resources.abstract_sdram import AbstractSDRAM


class SplitterDelayVertexSlice(AbstractSplitterCommon[DelayExtensionVertex]):
    """
    Handles the splitting of the :py:class:`DelayExtensionVertex`
    via slice logic.
    """

    __slots__ = ("_machine_vertex_by_slice", )

    _EXPANDER_BASE_PARAMS_SIZE = 3 * BYTES_PER_WORD

    NEED_EXACT_ERROR_MESSAGE = (
        "DelayExtensionsSplitters need exact incoming slices. Please fix "
        "and try again")

    DELAY_RECORDING_ERROR = (
        "The delay extensions does not record any variables. Therefore "
        "asking for them is deemed an error.")

    def __init__(self) -> None:
        super().__init__()
        self._machine_vertex_by_slice: Dict[
            Slice, DelayExtensionMachineVertex] = dict()

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        # pylint: disable=missing-function-docstring
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        # pylint: disable=missing-function-docstring
        return list(self.governed_app_vertex.machine_vertices)

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex,
            partition_id: str) -> Sequence[Tuple[
                DelayExtensionMachineVertex, Sequence[MachineVertex]]]:
        # pylint: disable=missing-function-docstring
        # Only connect to the source that matches the slice
        return [
            (self._machine_vertex_by_slice[m_vertex.vertex_slice], [m_vertex])
            for m_vertex in source_vertex.splitter.get_out_going_vertices(
                partition_id)]

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter):
        # pylint: disable=missing-function-docstring
        source_app_vertex = self.governed_app_vertex.source_vertex
        slices = source_app_vertex.splitter.get_out_going_slices()

        # create vertices correctly
        for vertex_slice in slices:
            vertex = self.create_machine_vertex(
                source_app_vertex, vertex_slice)
            self.governed_app_vertex.remember_machine_vertex(vertex)
            chip_counter.add_core(vertex.sdram_required)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        # pylint: disable=missing-function-docstring
        other_splitter = self.governed_app_vertex.source_vertex.splitter
        return other_splitter.get_in_coming_slices()

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        # pylint: disable=missing-function-docstring
        other_splitter = self.governed_app_vertex.source_vertex.splitter
        return other_splitter.get_out_going_slices()

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex: DelayExtensionVertex):
        # pylint: disable=missing-function-docstring
        super().set_governed_app_vertex(app_vertex)
        if not isinstance(app_vertex, DelayExtensionVertex):
            raise PacmanConfigurationException(
                f"The vertex {app_vertex} cannot be supported by the "
                "SplitterDelayVertexSlice as the only vertex supported by "
                "this splitter is a DelayExtensionVertex. Please use the "
                "correct splitter for your vertex and try again.")

    def create_machine_vertex(
            self, source_app_vertex: ApplicationVertex, vertex_slice: Slice):
        """
        Creates a delay extension machine vertex and adds to the tracker.

        :param ~pacman.model.graphs.machine.MachineVertex source_vertex:
            The source of the delay
        :return: machine vertex
        :rtype: DelayExtensionMachineVertex
        """
        label = f"Delay extension for {source_app_vertex}"
        sdram = self.get_sdram_used_by_atoms()

        machine_vertex = DelayExtensionMachineVertex(
            sdram, label, vertex_slice, self.governed_app_vertex)

        self._machine_vertex_by_slice[vertex_slice] = machine_vertex
        return machine_vertex

    def get_sdram_used_by_atoms(self) -> AbstractSDRAM:
        """
        Gets the amount of SDRAM used by the delay extension.

        :rtype: ~pacman.model.resources.ConstantSDRAM
        """
        return ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            self.governed_app_vertex.delay_params_size() +
            DelayExtensionMachineVertex.get_provenance_data_size(
                DelayExtensionMachineVertex.N_EXTRA_PROVENANCE_DATA_ENTRIES))

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        # pylint: disable=missing-function-docstring
        raise PacmanInvalidParameterException(
            variable_to_record, variable_to_record, self.DELAY_RECORDING_ERROR)

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        # pylint: disable=missing-function-docstring
        self._machine_vertex_by_slice = dict()

    def get_machine_vertex(
            self, vertex_slice: Slice) -> DelayExtensionMachineVertex:
        """
        Get a delay extension machine vertex for a given vertex slice.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice to get the data for
        :rtype: DelayExtensionMachineVertex
        """
        return self._machine_vertex_by_slice[vertex_slice]
