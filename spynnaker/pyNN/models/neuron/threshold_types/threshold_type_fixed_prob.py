# Copyright (c) 2024 The University of Manchester
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

from pyNN.random import NumpyRNG
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary
from spinn_front_end_common.interface.ds import DataType
from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.random_distribution import RandomDistribution
from .abstract_threshold_type import AbstractThresholdType

V_THRESH = "v_thresh"
P_THRESH = "p_thresh"
SEED0 = "seed0"
SEED1 = "seed1"
SEED2 = "seed2"
SEED3 = "seed3"


class ThresholdTypeFixedProb(AbstractThresholdType):
    """
    A threshold that spikes with a fixed probability when over a static value.
    """
    __slots__ = ("__v_thresh", "__p_thresh", "__random")

    def __init__(self, v_thresh: ModelParameter, p_thresh: ModelParameter,
                 seed: int):

        """
        :param v_thresh: :math:`V_{thresh}`
        :type v_thresh: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param p_thresh: :math:`P_{thresh}`
        :type p_thresh: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param seed: Random number generator seed
        """
        super().__init__(
            [Struct([(DataType.S1615, V_THRESH),
                     (DataType.U1616, P_THRESH),
                     (DataType.UINT32, SEED0),
                     (DataType.UINT32, SEED1),
                     (DataType.UINT32, SEED2),
                     (DataType.UINT32, SEED3)])],
            {V_THRESH: "mV",
             P_THRESH: ""})
        self.__v_thresh = v_thresh
        self.__p_thresh = p_thresh
        self.__random = RandomDistribution(
            "uniform", low=0, high=0xFFFFFFFF, rng=NumpyRNG(seed))

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]):
        parameters[V_THRESH] = self._convert(self.__v_thresh)
        parameters[P_THRESH] = self._convert(self.__p_thresh)

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary[float]):
        state_variables[SEED0] = self.__random
        state_variables[SEED1] = self.__random
        state_variables[SEED2] = self.__random
        state_variables[SEED3] = self.__random

    @property
    def v_thresh(self) -> ModelParameter:
        """
        :math:`V_{thresh}`
        """
        return self.__v_thresh

    @property
    def p_thresh(self) -> ModelParameter:
        """
        :math:`P_{thresh}`
        """
        return self.__p_thresh
