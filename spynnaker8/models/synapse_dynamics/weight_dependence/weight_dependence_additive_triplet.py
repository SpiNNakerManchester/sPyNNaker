# Copyright (c) 2021-2023 The University of Manchester
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
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditiveTriplet as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class WeightDependenceAdditiveTriplet(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence.WeightDependenceAdditiveTriplet`
        instead.
    """
    __slots__ = []

    # noinspection PyPep8Naming
    def __init__(
            self, w_min=0.0, w_max=1.0, A3_plus=0.01, A3_minus=0.01):
        r"""
        :param float w_min: :math:`w_\mathrm{min}`
        :param float w_max: :math:`w_\mathrm{max}`
        :param float A3_plus: :math:`A_3^+`
        :param float A3_minus: :math:`A_3^-`
        """
        moved_in_v6("spynnaker8.models.synapse_dynamics.weight_dependence"
                    ".WeightDependenceAdditiveTriplet",
                    "spynnaker.pyNN.models.neuron.plasticity.stdp."
                    "weight_dependence.WeightDependenceAdditiveTriplet")
        super(WeightDependenceAdditiveTriplet, self).__init__(
            w_max=w_max, w_min=w_min, A3_plus=A3_plus, A3_minus=A3_minus)
