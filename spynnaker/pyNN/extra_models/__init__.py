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

from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceRecurrent as RecurrentRule,
    TimingDependenceSpikeNearestPair as SpikeNearestPairRule,
    TimingDependenceVogels2011 as Vogels2011Rule,
    TimingDependencePfisterSpikeTriplet as PfisterSpikeTriplet)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsNeuromodulation as Neuromodulation)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditiveTriplet)
from spynnaker.pyNN.models.neuron.builds import (
    IFCondExpStoc,
    IFCurrDelta as IFCurDelta,
    IFCurrExpCa2Adaptive,
    IFCurrDualExpBase as IF_curr_dual_exp,
    IzkCondExpBase as Izhikevich_cond,
    IzkCondDualExpBase as Izhikevich_cond_dual,
    IFCurrExpSEMDBase as IF_curr_exp_sEMD,
    IFCurrDeltaCa2Adaptive, StocExp)

# Variable rate poisson
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVariable

__all__ = [
    # sPyNNaker models not currently part of full pyNN
    'IFCurDelta', 'IFCurrExpCa2Adaptive', 'IFCondExpStoc',
    'Izhikevich_cond', 'IF_curr_dual_exp', 'IF_curr_exp_sEMD',
    'Izhikevich_cond_dual', 'IFCurrDeltaCa2Adaptive',

    # Neuromodulation synapse dynamics (Mantas Mikaitis)
    'Neuromodulation',

    # sPyNNaker 8 plastic stuff
    'WeightDependenceAdditiveTriplet',
    'PfisterSpikeTriplet',
    'SpikeNearestPairRule',
    'RecurrentRule', 'Vogels2011Rule',

    # Variable rate Poisson
    'SpikeSourcePoissonVariable',

    # Stochastic
    'StocExp']
