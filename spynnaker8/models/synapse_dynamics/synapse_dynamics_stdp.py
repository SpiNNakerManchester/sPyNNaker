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
from pyNN.standardmodels.synapses import StaticSynapse as PyNNStaticSynapse
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsSTDP as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class SynapseDynamicsSTDP(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.synapse_dynamics.SynapseDynamicsSTDP`
        instead.
    """

    __slots__ = []

    def __init__(
            self, timing_dependence, weight_dependence,
            voltage_dependence=None, dendritic_delay_fraction=1.0,
            weight=PyNNStaticSynapse.default_parameters['weight'], delay=None,
            backprop_delay=True):
        """
        :param AbstractTimingDependence timing_dependence:
        :param AbstractWeightDependence weight_dependence:
        :param None voltage_dependence: Unsupported
        :param float dendritic_delay_fraction:
        :param float weight:
        :param delay:
        :type delay: float or None
        :param bool backprop_delay:
        """
        # pylint: disable=too-many-arguments

        # instantiate common functionality.
        moved_in_v6("spynnaker8.models.synapse_dynamics.SynapseDynamicsSTDP",
                    "spynnaker.pyNN.models.neuron.synapse_dynamics"
                    ".SynapseDynamicsSTDP")
        super(SynapseDynamicsSTDP, self).__init__(
            timing_dependence, weight_dependence, voltage_dependence,
            dendritic_delay_fraction, weight, delay,
            backprop_delay=backprop_delay)
