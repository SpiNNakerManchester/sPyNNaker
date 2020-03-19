from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsSTDP
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive)
from unittests.mocks import MockSimulator
import pytest


@pytest.mark.timeout(1)
def test_get_max_synapses():
    MockSimulator.setup()
    d = SynapseDynamicsSTDP(timing_dependence=TimingDependenceSpikePair(),
                            weight_dependence=WeightDependenceAdditive(),
                            pad_to_length=258)
    assert d.get_max_synapses(256) <= 256
