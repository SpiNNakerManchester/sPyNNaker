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
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceRecurrent as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6

_defaults = _BaseClass.default_parameters


class TimingDependenceRecurrent(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence.TimingDependenceRecurrent`
        instead.
    """
    __slots__ = []

    def __init__(
            self, accumulator_depression=_defaults['accumulator_depression'],
            accumulator_potentiation=_defaults['accumulator_potentiation'],
            mean_pre_window=_defaults['mean_pre_window'],
            mean_post_window=_defaults['mean_post_window'],
            dual_fsm=_defaults['dual_fsm'], A_plus=0.01, A_minus=0.01):
        """
        :param int accumulator_depression:
        :param int accumulator_potentiation:
        :param float mean_pre_window:
        :param float mean_post_window:
        :param bool dual_fsm:
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.synapse_dynamics.timing_dependence."
                    "TimingDependenceRecurrent",
                    "spynnaker.pyNN.models.neuron.plasticity.stdp."
                    "timing_dependence.TimingDependenceRecurrent")
        super(TimingDependenceRecurrent, self).__init__(
            accumulator_depression=accumulator_depression,
            accumulator_potentiation=accumulator_potentiation,
            mean_pre_window=mean_pre_window,
            mean_post_window=mean_post_window,
            dual_fsm=dual_fsm, A_plus=A_plus, A_minus=A_minus)
