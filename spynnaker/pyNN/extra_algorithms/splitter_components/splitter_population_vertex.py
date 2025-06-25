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

from typing import List, Optional, final, Iterable
from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.utilities.algorithm_utilities\
    .partition_algorithm_utilities import get_multidimensional_slices
from pacman.model.graphs.machine.machine_vertex import MachineVertex
from spynnaker.pyNN.models.neuron import PopulationVertex
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay


class SplitterPopulationVertex(
        AbstractSplitterCommon[PopulationVertex],
        AbstractSpynnakerSplitterDelay, metaclass=AbstractBase):
    """
    Abstract base class of splitters for :py:class:`PopulationVertex`.
    """
    __slots__ = ("__slices", )

    def __init__(self) -> None:
        super().__init__()
        self.__slices: Optional[List[Slice]] = None

    @final
    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(
            self, app_vertex: PopulationVertex) -> None:
        if not isinstance(app_vertex, PopulationVertex):
            raise PacmanConfigurationException(
                f"The vertex {app_vertex} cannot be supported by the "
                f"{self.__class__.__name__} as the only vertex "
                "supported by this splitter is a PopulationVertex. "
                "Please use the correct splitter for your vertex and try "
                "again.")
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        self.__slices = None

    @final
    @overrides(AbstractSpynnakerSplitterDelay.max_support_delay)
    def max_support_delay(self) -> int:
        return self.governed_app_vertex.max_delay_steps_incoming

    @overrides(AbstractSpynnakerSplitterDelay.accepts_edges_from_delay_vertex)
    def accepts_edges_from_delay_vertex(self) -> bool:
        return self.governed_app_vertex.allow_delay_extension

    @final
    def _get_fixed_slices(self) -> List[Slice]:
        """
        Get a list of fixed slices from the Application vertex.
        """
        if self.__slices is not None:
            return self.__slices
        self.__slices = get_multidimensional_slices(self.governed_app_vertex)
        return self.__slices

    @abstractmethod
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        raise NotImplementedError
