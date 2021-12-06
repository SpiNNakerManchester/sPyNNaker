# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .abstract_synapse_dynamics import AbstractSynapseDynamics
from .abstract_generate_on_machine import AbstractGenerateOnMachine
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
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
           "AbstractSynapseDynamicsStructural",
           "calculate_spike_pair_additive_stdp_weight",
           "calculate_spike_pair_multiplicative_stdp_weight",
           "PyNNSynapseDynamics", "SynapseDynamicsStatic",
           "SynapseDynamicsSTDP",
           # Structural plasticity
           "SynapseDynamicsStructuralCommon",
           "SynapseDynamicsStructuralStatic",
           "SynapseDynamicsStructuralSTDP",
           # Neuromodulation
           "SynapseDynamicsNeuromodulation"]
