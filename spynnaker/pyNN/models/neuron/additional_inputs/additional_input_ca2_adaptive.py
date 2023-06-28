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
from .abstract_additional_input import AbstractAdditionalInput
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

I_ALPHA = "i_alpha"
I_CA2 = "i_ca2"
TAU_CA2 = "tau_ca2"
TIME_STEP = "time_step"


class AdditionalInputCa2Adaptive(AbstractAdditionalInput):
    __slots__ = (
        "__tau_ca2",
        "__i_ca2",
        "__i_alpha")

    def __init__(self, tau_ca2, i_ca2, i_alpha):
        r"""
        :param tau_ca2: :math:`\tau_{\mathrm{Ca}^{+2}}`
        :type tau_ca2: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param i_ca2: :math:`I_{\mathrm{Ca}^{+2}}`
        :type i_ca2: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param i_alpha: :math:`I_{\alpha}`
        :type i_alpha: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                 (DataType.S1615, TAU_CA2),
                 (DataType.S1615, I_CA2),
                 (DataType.S1615, I_ALPHA),
                 (DataType.S1615, TIME_STEP)])],
            {I_ALPHA: "nA", I_CA2: "nA", TAU_CA2: "ms"})
        self.__tau_ca2 = tau_ca2
        self.__i_ca2 = i_ca2
        self.__i_alpha = i_alpha

    @overrides(AbstractAdditionalInput.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU_CA2] = self.__tau_ca2
        parameters[I_ALPHA] = self.__i_alpha
        parameters[TIME_STEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[I_CA2] = self.__i_ca2

    @property
    def tau_ca2(self):
        r"""
        Settable model parameter: :math:`\tau_{\mathrm{Ca}^{+2}}`

        :rtype: float
        """
        return self.__tau_ca2

    @property
    def i_ca2(self):
        r"""
        Settable model parameter: :math:`I_{\mathrm{Ca}^{+2}}`

        :rtype: float
        """
        return self.__i_ca2

    @property
    def i_alpha(self):
        r"""
        Settable model parameter: :math:`I_{\alpha}`

        :rtype: float
        """
        return self.__i_alpha
