# Copyright (c) 2015 The University of Manchester
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
from data_specification.enums import DataType
from .abstract_threshold_type import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct

V_THRESH = "v_thresh"


class ThresholdTypeStatic(AbstractThresholdType):
    """
    A threshold that is a static value.
    """
    __slots__ = ["__v_thresh"]

    def __init__(self, v_thresh):
        """
        :param v_thresh: :math:`V_{thresh}`
        :type v_thresh:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__(
            [Struct([(DataType.S1615, V_THRESH)])],
            {V_THRESH: "mV"})
        self.__v_thresh = v_thresh

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_THRESH] = self.__v_thresh

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @property
    def v_thresh(self):
        """
        :math:`V_{thresh}`
        """
        return self.__v_thresh
