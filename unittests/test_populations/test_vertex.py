import pytest

from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model import \
    AbstractNeuronModel
from unittests.mocks import MockSimulator


class MockModel(AbstractNeuronModel):

    def get_global_parameter_types(self):
        raise NotImplementedError

    def get_global_parameters(self):
        raise NotImplementedError

    def get_n_cpu_cycles_per_neuron(self):
        raise NotImplementedError

    def get_n_global_parameters(self):
        raise NotImplementedError

    def get_n_neural_parameters(self):
        raise NotImplementedError

    def get_neural_parameter_types(self):
        raise NotImplementedError

    def get_neural_parameters(self):
        raise NotImplementedError


class FooBar(MockModel):

    def __init__(self):
        self._foo = 1
        self._bar = 11

    def initialize_foo(self, value):
        self._foo = value

    @property
    def foo_init(self):
        return self._foo

    def initialize_bar(self, value):
        self._bar = value

    @property
    def bar(self):
        return self._bar


class MockNeuron(AbstractPopulationVertex):

    initialize_parameters = {'foo': 12, "bar_init": 13}

    def __init__(self, n_neurons, neuron_model):
        AbstractPopulationVertex.__init__(
            self,
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
            neuron_model=neuron_model,
            input_type=None,
            synapse_type=None,
            threshold_type=None)


def test_initializable():
    MockSimulator.setup()
    neuron = MockNeuron(5, FooBar())
    assert 1 == neuron.get_initial_value("foo")
    neuron.initialize("foo", 2)
    assert 2 == neuron.get_initial_value("foo_init")
    assert 11 == neuron.get_initial_value("bar_init")
    assert 11 == neuron.get_initial_value("bar")


def test_init_by_in():
    MockSimulator.setup()
    neuron = MockNeuron(5, FooBar())
    assert 1 == neuron.get_initial_value("foo")
    neuron.set_initial_value(variable="foo", value=11, selector=1)
    assert [1, 11, 1, 1, 1] == neuron.get_initial_value("foo")
    neuron.set_initial_value(variable="foo", value=12, selector=2)
    assert [1, 11, 12, 1, 1] == neuron.get_initial_value("foo")
    assert [11] == neuron.get_initial_value("bar", selector=1)
    assert [12] == neuron.get_initial_value("foo", selector=2)


def test_init_bad():
    MockSimulator.setup()
    neuron = MockNeuron(5, FooBar())
    with pytest.raises(KeyError):
        neuron.get_initial_value("badvariable")
    with pytest.raises(KeyError):
        assert 1 == neuron.initialize("anotherbad", "junk")


def test_initial_values():
    MockSimulator.setup()
    neuron = MockNeuron(5, FooBar())
    initial_values = neuron.initial_values
    assert "foo" in initial_values
    assert "bar" in initial_values
    initial_values = neuron.get_initial_values(selector=3)
    assert {"foo": [1], "bar": [11]} == initial_values
