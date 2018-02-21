from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from unittests.mocks import MockSimulator


class MockNeuron(AbstractPopulationVertex):

    initialize_parameters = {'foo_init': 12, "bar_init": 13}

    def __init__(self, n_neurons):
        AbstractPopulationVertex.__init__(self,
                n_neurons=n_neurons,
                binary=None,
                label="Mock",
                max_atoms_per_core=None,

                spikes_per_second=self.non_pynn_default_parameters[
                'spikes_per_second'],

                ring_buffer_sigma=self.non_pynn_default_parameters[
                'ring_buffer_sigma'],

                incoming_spike_buffer_size=self.non_pynn_default_parameters[
                'incoming_spike_buffer_size'],

                model_name="Mock",
                neuron_model=None,
                input_type=None,
                synapse_type=None,
                threshold_type=None)


def test_simple():
    MockSimulator.setup()
    MockNeuron(5)


