# Copyright (c) 2014-2023 The University of Manchester
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

from .abstract_synapse_dynamics import AbstractSynapseDynamics
from .abstract_sdram_synapse_dynamics import AbstractSDRAMSynapseDynamics
from .abstract_generate_on_machine import AbstractGenerateOnMachine
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_supports_signed_weights import AbstractSupportsSignedWeights
from .pynn_synapse_dynamics import PyNNSynapseDynamics
from .synapse_dynamics_static import SynapseDynamicsStatic
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_structural_common import SynapseDynamicsStructuralCommon
from .synapse_dynamics_structural_static import SynapseDynamicsStructuralStatic
from .synapse_dynamics_structural_stdp import SynapseDynamicsStructuralSTDP
from .synapse_dynamics_utils import (
    calculate_spike_pair_additive_stdp_weight,
    calculate_spike_pair_multiplicative_stdp_weight)
from .synapse_dynamics_neuromodulation import SynapseDynamicsNeuromodulation


__all__ = ["AbstractGenerateOnMachine", "AbstractPlasticSynapseDynamics",
           "AbstractStaticSynapseDynamics", "AbstractSynapseDynamics",
           "AbstractSDRAMSynapseDynamics", "AbstractSynapseDynamicsStructural",
           "calculate_spike_pair_additive_stdp_weight",
           "calculate_spike_pair_multiplicative_stdp_weight",
           "PyNNSynapseDynamics", "SynapseDynamicsStatic",
           "SynapseDynamicsSTDP",
           # Structural plasticity
           "SynapseDynamicsStructuralCommon",
           "SynapseDynamicsStructuralStatic",
           "SynapseDynamicsStructuralSTDP",
           # Neuromodulation
           "SynapseDynamicsNeuromodulation",
           "AbstractSupportsSignedWeights"]
