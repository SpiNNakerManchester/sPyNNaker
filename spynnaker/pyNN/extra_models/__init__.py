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

from spynnaker.pyNN.models.neural_projections.connectors. \
    all_but_me_connector import AllButMeConnector
from spynnaker.pyNN.models.neural_projections.connectors. \
    one_to_one_offset_connector import OneToOneOffsetConnector
from spynnaker.pyNN.models.neuron.builds.if_cond_exp_stoc import (
    IFCondExpStoc,
)
from spynnaker.pyNN.models.neuron.builds.if_curr_delta import (
    IFCurrDelta as IFCurDelta,
)
from spynnaker.pyNN.models.neuron.builds.if_curr_delta_ca2_adaptive import (
    IFCurrDeltaCa2Adaptive,
)
from spynnaker.pyNN.models.neuron.builds.if_curr_delta_fixed_prob import (
    IFCurrDeltaFixedProb,
)
from spynnaker.pyNN.models.neuron.builds.if_curr_dual_exp_base import (
    IFCurrDualExpBase as IF_curr_dual_exp,
)
from spynnaker.pyNN.models.neuron.builds.if_curr_exp_ca2_adaptive import (
    IFCurrExpCa2Adaptive,
)
from spynnaker.pyNN.models.neuron.builds.if_curr_exp_semd_base import (
    IFCurrExpSEMDBase as IF_curr_exp_sEMD,
)
from spynnaker.pyNN.models.neuron.builds.if_trunc_delta import (
    IFTruncDelta,
)
from spynnaker.pyNN.models.neuron.builds.izk_cond_dual_exp_base import (
    IzkCondDualExpBase as Izhikevich_cond_dual,
)
from spynnaker.pyNN.models.neuron.builds.izk_cond_exp_base import (
    IzkCondExpBase as Izhikevich_cond,
)
from spynnaker.pyNN.models.neuron.builds.stoc_exp import StocExp
from spynnaker.pyNN.models.neuron.builds.stoc_exp_stable import StocExpStable
from spynnaker.pyNN.models.neuron.builds.stoc_sigma import StocSigma
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence. \
    timing_dependence_pfister_spike_triplet import (
        TimingDependencePfisterSpikeTriplet as PfisterSpikeTriplet,
    )
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence. \
    timing_dependence_recurrent import (
        TimingDependenceRecurrent as RecurrentRule,
    )
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence. \
    timing_dependence_spike_nearest_pair import (
        TimingDependenceSpikeNearestPair as SpikeNearestPairRule,
    )
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence. \
    timing_dependence_vogels_2011 import (
        TimingDependenceVogels2011 as Vogels2011Rule,
    )
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence. \
    weight_dependence_additive_triplet import WeightDependenceAdditiveTriplet
from spynnaker.pyNN.models.neuron.synapse_dynamics. \
    synapse_dynamics_neuromodulation import (
        SynapseDynamicsNeuromodulation as Neuromodulation,
    )
from spynnaker.pyNN.models.neuron.synapse_dynamics. \
    synapse_dynamics_weight_changable import (
        SynapseDynamicsWeightChangable as WeightChangeable,
    )
from spynnaker.pyNN.models.neuron.synapse_dynamics. \
    synapse_dynamics_weight_changer import (
        SynapseDynamicsWeightChanger as WeightChanger,
    )

# Variable rate poisson
from spynnaker.pyNN.models.spike_source.spike_source_poisson_variable import (
    SpikeSourcePoissonVariable,
)

__all__ = [  # noqa: RUF022
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
    'StocExp', 'StocExpStable', 'StocSigma', 'IFCurrDeltaFixedProb',

    # Special
    'IFTruncDelta',

    # Connectors
    'AllButMeConnector', 'OneToOneOffsetConnector',

    # Weight changeable synapse dynamics
    'WeightChangeable', 'WeightChanger'
    ]
