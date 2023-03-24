# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from .abstract_elimination import AbstractElimination


class RandomByWeightElimination(AbstractElimination):
    """ Elimination Rule that depends on the weight of a synapse
    """

    __slots__ = [
        "__prob_elim_depressed",
        "__prob_elim_potentiated",
        "__threshold"
    ]

    def __init__(
            self, threshold, prob_elim_depressed=0.0245,
            prob_elim_potentiated=1.36 * 10 ** -4):
        """
        :param float threshold:
            Below this weight is considered depression, above or equal to this
            weight is considered potentiation (or the static weight of the
            connection on static weight connections)
        :param float prob_elim_depressed:
            The probability of elimination if the weight has been depressed
            (ignored on static weight connections)
        :param float prob_elim_potentiated:
            The probability of elimination of the weight has been potentiated
            or has not changed (and also used on static weight connections)
        """
        self.__prob_elim_depressed = prob_elim_depressed
        self.__prob_elim_potentiated = prob_elim_potentiated
        self.__threshold = threshold

    @property
    @overrides(AbstractElimination.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_weight"

    @overrides(AbstractElimination.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 3 * 4

    @overrides(AbstractElimination.write_parameters)
    def write_parameters(self, spec, weight_scale):
        spec.write_value(int(self.__prob_elim_depressed * 0xFFFFFFFF))
        spec.write_value(int(self.__prob_elim_potentiated * 0xFFFFFFFF))
        spec.write_value(self.__threshold * weight_scale)

    @overrides(AbstractElimination.get_parameter_names)
    def get_parameter_names(self):
        return ["prob_elim_depressed", "prob_elim_potentiated", "threshold"]
