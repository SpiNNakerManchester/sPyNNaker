# Copyright (c) 2019 The University of Manchester
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

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.range_dictionary import RangeDictionary

from spinn_front_end_common.interface.ds import DataType

from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.utilities.struct import Struct

from .abstract_threshold_type import AbstractThresholdType

BIG_B = "big_b"
SMALL_B = "small_b"
SMALL_B_0 = "small_b_0"
TAU_A = "tau_a"
BETA = "beta"
ADPT = "adpt"
SCALAR = "scalar"


class ThresholdTypeAdaptive(AbstractThresholdType):
    """ A threshold that is adaptive
    """
    __slots__ = [
        "__beta",
        "__big_b",
        "__scalar",
        "__small_b",
        "__small_b_0",
        "__tau_a"
        ]

    def __init__(self,  big_b: ModelParameter, small_b: ModelParameter,
                 small_b_0: ModelParameter, tau_a: ModelParameter,
                 beta: ModelParameter) -> None:
        """
        :param big_b: The big b parameter
        :param small_b: The small b parameter
        :param small_b_0: The small b 0 parameter
        :param tau_a: The tau a parameter
        :param beta: The beta parameter
        """
        super().__init__(
            [Struct([
                (DataType.S1615, BIG_B),
                (DataType.S1615, SMALL_B),
                (DataType.S1615, SMALL_B_0),
                (DataType.UINT32, TAU_A),
                (DataType.S1615, BETA),
                (DataType.UINT32, SCALAR)])],
            {BIG_B: "mV", SMALL_B: "mV", SMALL_B_0: "mV", TAU_A: "ms",
             BETA: "", SCALAR: ""})
        self.__big_b: ModelParameter = big_b
        self.__small_b: ModelParameter = small_b
        self.__small_b_0: ModelParameter = small_b_0
        self.__tau_a: ModelParameter = tau_a
        self.__beta: ModelParameter = beta
        self.__scalar: int = 1000

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        parameters[SMALL_B_0] = self._convert(self.__small_b_0)
        parameters[TAU_A] = self._convert(self.__tau_a)
        parameters[BETA] = self._convert(self.__beta)
        parameters[SCALAR] = self._convert(self.__scalar)

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        state_variables[BIG_B] = self._convert(self.__big_b)
        state_variables[SMALL_B] = self._convert(self.__small_b)

    @property
    def big_b(self) -> ModelParameter:
        """ The big b parameter """
        return self.__big_b

    @big_b.setter
    def big_b(self, new_value: ModelParameter) -> None:
        """ Set the big b parameter """
        self.__big_b = new_value

    @property
    def small_b(self) -> ModelParameter:
        """ The small b parameter """
        return self.__small_b

    @small_b.setter
    def small_b(self, new_value: ModelParameter) -> None:
        """ Set the small b parameter """
        self.__small_b = new_value

    @property
    def small_b_0(self) -> ModelParameter:
        """ The small b 0 parameter """
        return self.__small_b_0

    @small_b_0.setter
    def small_b_0(self, new_value: ModelParameter) -> None:
        """ Set the small b 0 parameter """
        self.__small_b_0 = new_value

    @property
    def tau_a(self) -> ModelParameter:
        """ The tau a parameter """
        return self.__tau_a

    @tau_a.setter
    def tau_a(self, new_value: ModelParameter) -> None:
        """ Set the tau a parameter """
        self.__tau_a = new_value

    @property
    def beta(self) -> ModelParameter:
        """ The beta parameter """
        return self.__beta

    @beta.setter
    def beta(self, new_value: ModelParameter) -> None:
        self.__beta = new_value
