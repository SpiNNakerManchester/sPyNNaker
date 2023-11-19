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
from spinn_front_end_common.interface.ds import DataType
from .abstract_input_type import AbstractInputType
from spynnaker.pyNN.utilities.struct import Struct

E_REV_E = "e_rev_E"
E_REV_I = "e_rev_I"


class InputTypeConductance(AbstractInputType):
    """
    The conductance input type.
    """
    __slots__ = [
        "__e_rev_E",
        "__e_rev_I"]

    def __init__(self, e_rev_E, e_rev_I):
        """
        :param e_rev_E: Reversal potential for excitatory input;
            :math:`E^{rev}_e`
        :type e_rev_E: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param e_rev_I: Reversal potential for inhibitory input;
            :math:`E^{rev}_i`
        :type e_rev_I: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([(DataType.S1615, E_REV_E),
                     (DataType.S1615, E_REV_I)])],
            {E_REV_E: "mV", E_REV_I: "mV"})
        self.__e_rev_E = e_rev_E
        self.__e_rev_I = e_rev_I

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        parameters[E_REV_E] = self.__e_rev_E
        parameters[E_REV_I] = self.__e_rev_I

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        # IMPLICIT WEIGHT SCALING -- the default in main branch is 2**10
        return float(2**5)

    @property
    def e_rev_E(self):
        """
        :math:`E_{{rev}_e}`
        """
        return self.__e_rev_E

    @property
    def e_rev_I(self):
        """
        :math:`E_{{rev}_i}`
        """
        return self.__e_rev_I
