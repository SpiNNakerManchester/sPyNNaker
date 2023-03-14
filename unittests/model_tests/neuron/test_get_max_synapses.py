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

from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsSTDP
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive)
import pyNN.spiNNaker as sim


def test_get_max_synapses():
    unittest_setup()
    sim.setup()
    d = SynapseDynamicsSTDP(timing_dependence=TimingDependenceSpikePair(),
                            weight_dependence=WeightDependenceAdditive(),
                            pad_to_length=258)
    assert d.get_max_synapses(256) <= 256
