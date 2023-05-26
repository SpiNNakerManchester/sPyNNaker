# Copyright (c) 2021 The University of Manchester
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

from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependencePfisterSpikeTriplet as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class TimingDependencePfisterSpikeTriplet(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence.TimingDependencePfisterSpikeTriplet`
        instead.
    """
    __slots__ = []

    # noinspection PyPep8Naming
    def __init__(
            self, tau_plus, tau_minus, tau_x, tau_y, A_plus=0.01,
            A_minus=0.01):
        r"""
        :param float tau_plus: :math:`\tau_+`
        :param float tau_minus: :math:`\tau_-`
        :param float tau_x: :math:`\tau_x`
        :param float tau_y: :math:`\tau_y`
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.synapse_dynamics.timing_dependence."
                    "TimingDependencePfisterSpikeTriplet",
                    "spynnaker.pyNN.models.neuron.plasticity.stdp."
                    "timing_dependence.TimingDependencePfisterSpikeTriplet")
        super().__init__(
            tau_plus=tau_plus, tau_minus=tau_minus, tau_x=tau_x,
            tau_y=tau_y, A_plus=A_plus, A_minus=A_minus)
