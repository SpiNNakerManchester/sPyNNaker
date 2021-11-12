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

import pytest
from spynnaker.pyNN.exceptions import SynapseRowTooBigException
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, SynapseInformation)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, SynapseDynamicsSTDP)
from spynnaker.pyNN.models.neuron.synapse_io import _get_allowed_row_length
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)
import spynnaker8

# No unittest_setup as sim.setup must be called before SynapseDynamicsStatic


@pytest.mark.parametrize(
    "dynamics_class,timing,weight,size,exception,max_size",
    [
     # Normal static rows can be up to 256 words, 1 word per synapse
     (SynapseDynamicsStatic, None, None, 512, SynapseRowTooBigException, 256),

     # Normal static row of 20 is allowed - 20 words
     (SynapseDynamicsStatic, None, None, 20, None, 20),

     # STDP row with spike pair rule is 1 words per synapse but extra
     # header takes some of the space, so only 254 synapses allowed
     (SynapseDynamicsSTDP,
         TimingDependenceSpikePair, WeightDependenceAdditive,
      512, SynapseRowTooBigException, 254),

     # STDP row with spike pair rule of 20 is allowed - 20 words
     (SynapseDynamicsSTDP,
         TimingDependenceSpikePair, WeightDependenceAdditive,
      20, None, 20)])
def test_get_allowed_row_length(
        dynamics_class, timing, weight, size, exception, max_size):
    spynnaker8.setup()
    if timing is not None and weight is not None:
        dynamics = dynamics_class(timing(), weight())
    else:
        dynamics = dynamics_class()
    synapse_information = SynapseInformation(
        None, None, None, False, False, None, None, dynamics, 0, None, True,
        False)
    in_edge = ProjectionApplicationEdge(None, None, synapse_information)
    if exception is not None:
        with pytest.raises(exception) as exc_info:
            _get_allowed_row_length(size, dynamics, in_edge, size)
        assert exc_info.value.max_size == max_size
    else:
        actual_size = _get_allowed_row_length(size, dynamics, in_edge, size)
        assert actual_size == max_size
