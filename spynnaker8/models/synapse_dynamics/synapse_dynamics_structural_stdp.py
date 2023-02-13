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
from pyNN.standardmodels.synapses import StaticSynapse
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStructuralSTDP as
    _BaseClass)
from spynnaker.pyNN.models.neuron.synapse_dynamics.\
    synapse_dynamics_structural_common import (
        DEFAULT_F_REW, DEFAULT_INITIAL_WEIGHT, DEFAULT_INITIAL_DELAY,
        DEFAULT_S_MAX)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class SynapseDynamicsStructuralSTDP(_BaseClass):
    """
    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neuron.synapse_dynamics.SynapseDynamicsStructuralSTDP`
        instead.
    """
    __slots__ = []

    def __init__(
            self, partner_selection, formation, elimination,
            timing_dependence=None, weight_dependence=None,
            voltage_dependence=None, dendritic_delay_fraction=1.0,
            f_rew=DEFAULT_F_REW, initial_weight=DEFAULT_INITIAL_WEIGHT,
            initial_delay=DEFAULT_INITIAL_DELAY, s_max=DEFAULT_S_MAX,
            seed=None, weight=StaticSynapse.default_parameters['weight'],
            delay=None, backprop_delay=True):
        """
        :param AbstractPartnerSelection partner_selection:
            The partner selection rule
        :param AbstractFormation formation: The formation rule
        :param AbstractElimination elimination: The elimination rule
        :param AbstractTimingDependence timing_dependence:
            The STDP timing dependence rule
        :param AbstractWeightDependence weight_dependence:
            The STDP weight dependence rule
        :param None voltage_dependence:
            The STDP voltage dependence (unsupported)
        :param float dendritic_delay_fraction:
            The STDP dendritic delay fraction
        :param int f_rew: How many rewiring attempts will be done per second.
        :param float initial_weight:
            Weight assigned to a newly formed connection
        :param initial_delay:
            Delay assigned to a newly formed connection; a single value means\
            a fixed delay value, or a tuple of two values means the delay will\
            be chosen at random from a uniform distribution between the given\
            values
        :type initial_delay: float or tuple(float, float)
        :param int s_max: Maximum fan-in per target layer neuron
        :param int seed: seed the random number generators
        :param float weight: The weight of connections formed by the connector
        :param delay: The delay of connections formed by the connector
        :type delay: float or None
        """
        moved_in_v6("spynnaker8.models.synapse_dynamics."
                    "SynapseDynamicsStructuralSTDP",
                    "spynnaker.pyNN.models.neuron.synapse_dynamics"
                    ".synapseDynamicsStructuralSTDP")
        _BaseClass.__init__(
            self, partner_selection, formation, elimination,
            timing_dependence=timing_dependence,
            weight_dependence=weight_dependence,
            voltage_dependence=voltage_dependence,
            dendritic_delay_fraction=dendritic_delay_fraction, f_rew=f_rew,
            initial_weight=initial_weight, initial_delay=initial_delay,
            s_max=s_max, seed=seed, weight=weight, delay=delay,
            backprop_delay=backprop_delay)
