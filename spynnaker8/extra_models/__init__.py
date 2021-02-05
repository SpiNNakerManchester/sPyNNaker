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

from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceRecurrent as
    RecurrentRule,
    TimingDependenceSpikeNearestPair as
    SpikeNearestPairRule,
    TimingDependenceVogels2011 as
    Vogels2011Rule,
    TimingDependencePfisterSpikeTriplet as
    PfisterSpikeTriplet)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditiveTriplet)
from spynnaker.pyNN.models.neuron.builds import (
    IFCondExpStoc, IFCurrDelta as
    IFCurDelta, IFCurrExpCa2Adaptive, IFCurrDualExpBase as
    IF_curr_dual_exp, IzkCondExpBase as
    Izhikevich_cond, IFCurrExpSEMDBase as
    IF_curr_exp_sEMD)
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVariable

__all__ = [
    # sPyNNaker 8 models
    'IFCurDelta', 'IFCurrExpCa2Adaptive', 'IFCondExpStoc',
    'Izhikevich_cond', 'IF_curr_dual_exp', 'IF_curr_exp_sEMD',

    # sPyNNaker 8 plastic stuff
    'WeightDependenceAdditiveTriplet',
    'PfisterSpikeTriplet',
    'SpikeNearestPairRule',
    'RecurrentRule', 'Vogels2011Rule',

    # Variable rate Poisson
    'SpikeSourcePoissonVariable']
