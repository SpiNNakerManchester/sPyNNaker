# Copyright (c) 2017 The University of Manchester
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
from __future__ import annotations
from enum import Enum
from typing import Mapping, Optional, Sequence, Union, TYPE_CHECKING
from typing_extensions import TypeAlias
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_front_end_common.interface.ds import DataType
if TYPE_CHECKING:
    from spynnaker.pyNN.models.populations import Population, PopulationBase
    from spynnaker.pyNN.models.neuron.abstract_population_vertex import (
        AbstractPopulationVertex)

#: General type of parameters to current sources.
#: Individual parameters will only be one of these!
CurrentParameter: TypeAlias = Union[int, float, Sequence[int], Sequence[float]]


# Hashes of the current sources currently supported
class CurrentSourceIDs(Enum):
    NO_SOURCE = 0
    DC_SOURCE = 1
    AC_SOURCE = 2
    STEP_CURRENT_SOURCE = 3
    NOISY_CURRENT_SOURCE = 4
    N_SOURCES = 4


class AbstractCurrentSource(object, metaclass=AbstractBase):
    """
    A simplified version of the PyNN class, since in most cases we work
    out the actual offset value on the SpiNNaker machine itself based on
    the parameters during the run.
    """
    __slots__ = (
        "__app_vertex",
        "__population")

    def __init__(self) -> None:
        self.__app_vertex: Optional[AbstractPopulationVertex] = None
        self.__population: Optional[Population] = None

    def inject_into(self, cells: PopulationBase):
        """
        Inject this source into the specified population cells.

        :param PopulationBase cells: The cells to inject the source into
        """
        # Call the population method to pass the source in
        cells.inject(self)

    def set_app_vertex(self, vertex: AbstractPopulationVertex):
        """
        Set the application vertex associated with the current source.

        :param AbstractPopulationVertex vertex: The population vertex
        """
        self.__app_vertex = vertex

    @property
    def app_vertex(self) -> Optional[AbstractPopulationVertex]:
        """
        The application vertex associated with the current source.

        :rtype: AbstractPopulationVertex
        """
        return self.__app_vertex

    def set_population(self, population: Population):
        """
        Set the population associated with the current source.

        :param ~spynnaker.pyNN.models.populations.Population population:
        """
        self.__population = population

    @property
    def population(self) -> Optional[Population]:
        """
        The population associated with the current source.

        :rtype: ~spynnaker.pyNN.models.populations.Population
        """
        return self.__population

    @abstractmethod
    def set_parameters(self, **parameters: CurrentParameter):
        """
        Set the current source parameters.

        :param parameters: the parameters to set
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def parameters(self) -> Mapping[str, CurrentParameter]:
        """
        The parameters of the current source.

        :rtype: dict(str, Any)
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def parameter_types(self) -> Mapping[str, DataType]:
        """
        The parameter types for the current source.

        :rtype: dict(str, ~.DataType)
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def current_source_id(self) -> int:
        """
        The ID of the current source.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_sdram_usage_in_bytes(self) -> int:
        """
        The SDRAM usage in bytes of the current source.

        :rtype: int
        """
        raise NotImplementedError
