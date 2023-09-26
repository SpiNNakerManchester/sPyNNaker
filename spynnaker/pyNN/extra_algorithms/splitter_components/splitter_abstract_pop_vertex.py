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

from typing import List, Optional, final
from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import Slice
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.utilities.algorithm_utilities\
    .partition_algorithm_utilities import get_multidimensional_slices
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay


# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14


class SplitterAbstractPopulationVertex(
        AbstractSplitterCommon[AbstractPopulationVertex],
        AbstractSpynnakerSplitterDelay):
    """
    Abstract base class of splitters for :py:class:`AbstractPopulationVertex`.
    """
    __slots__ = ("_max_delay", "__slices")

    def __init__(self, max_delay: Optional[int]) -> None:
        super().__init__()
        self._max_delay = max_delay
        self.__slices: Optional[List[Slice]] = None

    @final
    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex: AbstractPopulationVertex):
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                f"The vertex {app_vertex} cannot be supported by the "
                f"{self.__class__.__name__} as the only vertex "
                "supported by this splitter is a AbstractPopulationVertex. "
                "Please use the correct splitter for your vertex and try "
                "again.")
        super().set_governed_app_vertex(app_vertex)

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        self._max_delay = None
        self.__slices = None

    @property
    @final
    def _apv(self) -> AbstractPopulationVertex:
        v = self.governed_app_vertex
        assert v is not None
        return v

    @abstractmethod
    def _update_max_delay(self) -> None:
        """
        Find the maximum delay from incoming synapses.
        Must set `_max_delay`, and must not set it to `None`.
        """
        raise NotImplementedError

    @final
    @overrides(AbstractSpynnakerSplitterDelay.max_support_delay)
    def max_support_delay(self) -> int:
        if self._max_delay is None:
            self._update_max_delay()
        assert self._max_delay is not None
        return self._max_delay

    @final
    def _get_fixed_slices(self) -> List[Slice]:
        """
        Get a list of fixed slices from the Application vertex.

        :rtype: list(~pacman.model.graphs.common.Slice)
        """
        if self.__slices is not None:
            return self.__slices
        self.__slices = get_multidimensional_slices(self._apv)
        return self.__slices
