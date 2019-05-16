import pytest
from spynnaker.pyNN.exceptions import SynapseRowTooBigException
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, SynapseInformation)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, SynapseDynamicsSTDP)
from spynnaker.pyNN.models.neuron.master_pop_table_generators import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.models.neuron.synapse_io import SynapseIORowBased
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence import (
    WeightDependenceAdditive)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    TimingDependenceSpikePair)


@pytest.mark.parametrize(
    "dynamics,size,exception,max_size",
    [
     # Normal static rows can be up to 255 words, 1 word per synapse
     (SynapseDynamicsStatic(), 512, SynapseRowTooBigException, 255),

     # Normal static row of 20 is allowed - 20 words
     (SynapseDynamicsStatic(), 20, None, 20),

     # STDP row with spike pair rule is 1 words per synapse but extra
     # header takes some of the space, so only 252 synapses allowed
     (SynapseDynamicsSTDP(
         TimingDependenceSpikePair(), WeightDependenceAdditive()),
      512, SynapseRowTooBigException, 252),

     # STDP row with spike pair rule of 20 is allowed - 20 words
     (SynapseDynamicsSTDP(
         TimingDependenceSpikePair(), WeightDependenceAdditive()),
      20, None, 20)])
def test_get_max_row_length(dynamics, size, exception, max_size):
    io = SynapseIORowBased()
    population_table = MasterPopTableAsBinarySearch()
    synapse_information = SynapseInformation(None, dynamics, 0)
    in_edge = ProjectionApplicationEdge(None, None, synapse_information)
    if exception is not None:
        with pytest.raises(exception) as exc_info:
            io._get_max_row_length(
                size, dynamics, population_table, in_edge, size)
        assert exc_info.value.max_size == max_size
    else:
        actual_size = io._get_max_row_length(
            size, dynamics, population_table, in_edge, size)
        assert actual_size == max_size
