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

from typing import Dict, Iterable, List, Union

import numpy
from numpy import floating
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from pyNN.random import RandomDistribution

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.ranged import RangeDictionary, RangedList

from spynnaker.pyNN.utilities.ranged import SpynnakerRangedList
from spynnaker.pyNN.utilities.struct import Struct

#: The type of parameters to a neuron model.
ModelParameter: TypeAlias = Union[
    float, Iterable[float], RandomDistribution, NDArray[floating]]


class AbstractStandardNeuronComponent(object, metaclass=AbstractBase):
    """
    Represents a component of a standard neural model.
    """
    __slots__ = (
        "__structs",
        "__units")

    def __init__(self, structs: List[Struct], units: Dict[str, str]):
        """
        :param list(Struct) structs: The structures of the component
        :param dict units: The units to use for each parameter
        """
        self.__structs = structs
        self.__units = units

    @property
    def structs(self) -> List[Struct]:
        """
        The structures of the component.  If there are multiple structures,
        the order is how they will appear in memory; where there are
        structures that repeat per neuron the repeats will appear adjacent
        e.g. for non-repeating structure `g`, followed by repeating structures
        `s1` and `s2` with 3 neurons the layout will be:
        ``[g, s1, s1, s1, s2, s2, s2]``.

        :rtype: list(~spynnaker.pyNN.utilities.struct.Struct)
        """
        return self.__structs

    @abstractmethod
    def add_parameters(self, parameters: RangeDictionary[float]):
        """
        Add the initial values of the parameters to the parameter holder.

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            A holder of the parameters
        """
        raise NotImplementedError

    @abstractmethod
    def add_state_variables(self, state_variables: RangeDictionary[float]):
        """
        Add the initial values of the state variables to the state
        variables holder.

        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            A holder of the state variables
        """
        raise NotImplementedError

    def has_variable(self, variable: str) -> bool:
        """
        Determine if this component has a variable by the given name.

        :param str variable: The name of the variable
        :rtype: bool
        """
        return variable in self.__units

    def get_units(self, variable: str) -> str:
        """
        Get the units of the given variable.

        :param str variable: The name of the variable
        """
        return self.__units[variable]

    @staticmethod
    def _convert(value: ModelParameter) -> \
            Union[float, RangedList[float], RandomDistribution]:
        """
        Converts a model parameter into a form that can be ingested by a
        RangeDictionary.
        """
        if isinstance(value, (float, int, numpy.integer, numpy.floating)):
            return float(value)
        if isinstance(value, RandomDistribution):
            return value
        # TODO: Is this correct? Without this, things will only handle floats
        return SpynnakerRangedList(None, value)
