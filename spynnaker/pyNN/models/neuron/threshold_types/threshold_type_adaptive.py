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
from spinn_front_end_common.interface.ds import DataType
from .abstract_threshold_type import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct

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
        "__B",
        "__small_b",
        "__small_b_0",
        "__tau_a",
        "__beta",
        "__scalar"
        ]

    def __init__(self,  B, small_b, small_b_0, tau_a, beta):
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
        self.__B = B
        self.__small_b = small_b
        self.__small_b_0 = small_b_0
        self.__tau_a = tau_a
        self.__beta = beta
        self.__scalar = 1000

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[SMALL_B_0] = self.__small_b_0
        parameters[TAU_A] = self.__tau_a
        parameters[BETA] = self.__beta
        parameters[SCALAR] = self.__scalar

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[BIG_B] = self.__B
        state_variables[SMALL_B] = self.__small_b

    @property
    def B(self):
        return self.__B

    @B.setter
    def B(self, new_value):
        self.__B = new_value

    @property
    def small_b(self):
        return self.__small_b

    @small_b.setter
    def small_b(self, new_value):
        self.__small_b = new_value

    @property
    def small_b_0(self):
        return self.__small_b_0

    @small_b_0.setter
    def small_b_0(self, new_value):
        self.__small_b_0 = new_value

    @property
    def tau_a(self):
        return self.__tau_a

    @tau_a.setter
    def tau_a(self, new_value):
        self.__tau_a = new_value

    @property
    def beta(self):
        return self.__beta

    @beta.setter
    def beta(self, new_value):
        self.__beta = new_value