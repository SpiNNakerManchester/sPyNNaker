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

from spynnaker8.models.synapse_dynamics.timing_dependence import (
    TimingDependenceRecurrent as RecurrentRule,
    TimingDependenceSpikeNearestPair as SpikeNearestPairRule,
    TimingDependenceVogels2011 as Vogels2011Rule,
    TimingDependencePfisterSpikeTriplet as PfisterSpikeTriplet)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsNeuromodulation as Neuromodulation)
from spynnaker8.models.synapse_dynamics.weight_dependence import (
    WeightDependenceAdditiveTriplet)
from spynnaker.pyNN.models.neuron.builds import (
    IFCondExpStoc,
    IFCurrDelta as IFCurDelta,
    IFCurrExpCa2Adaptive,
    IFCurrDualExpBase as IF_curr_dual_exp,
    IzkCondExpBase as Izhikevich_cond,
    IFCurrExpSEMDBase as IF_curr_exp_sEMD)

# Variable rate poisson
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVariable
from spynnaker.pyNN.utilities.utility_calls import moved_in_v7

__all__ = [
    # sPyNNaker 8 models
    'IFCurDelta', 'IFCurrExpCa2Adaptive', 'IFCondExpStoc',
    'Izhikevich_cond', 'IF_curr_dual_exp', 'IF_curr_exp_sEMD',

    # Neuromodulation synapse dynamics (Mantas Mikaitis)
    'Neuromodulation',

    # sPyNNaker 8 plastic stuff
    'WeightDependenceAdditiveTriplet',
    'PfisterSpikeTriplet',
    'SpikeNearestPairRule',
    'RecurrentRule', 'Vogels2011Rule',

    # Variable rate Poisson
    'SpikeSourcePoissonVariable']

moved_in_v7("spynnaker8.extra_models",
            "spynnaker.pyNN.extra_models")
