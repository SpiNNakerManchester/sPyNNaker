# Copyright (c) 2017 The University of Manchester
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

import pytest
import numpy
import pyNN.spiNNaker as sim
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, AbstractPyNNNeuronModelStandard)
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
from spynnaker.pyNN.models.defaults import default_initial_values, defaults
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)


class EmptyNeuronComponent(AbstractStandardNeuronComponent):
    def __init__(self):
        super().__init__([], [])

    def add_parameters(self, parameters):
        pass

    def add_state_variables(self, state_variables):
        pass

    def get_values(self, parameters, state_variables, vertex_slice, ts):
        return numpy.zeros(dtype="uint32")

    def update_values(self, values, parameters, state_variables):
        pass

    def has_variable(self, variable):
        return False

    def get_units(self, variable):
        return None


class EmptySynapseType(AbstractSynapseType, EmptyNeuronComponent):
    def get_n_synapse_types(self):
        return 0

    def get_synapse_targets(self):
        return []

    def get_synapse_id_by_target(self, target):
        return None


class _MyNeuronModel(AbstractStandardNeuronComponent):
    def __init__(self, foo, bar):
        super().__init__([], [])
        self._foo = foo
        self._bar = bar

    def add_parameters(self, parameters):
        pass

    def add_state_variables(self, state_variables):
        state_variables["foo"] = self._foo
        state_variables["bar"] = self._bar

    def get_values(self, parameters, state_variables, vertex_slice, ts):
        return numpy.zeros(dtype="uint32")

    def update_values(self, values, parameters, state_variables):
        pass

    def has_variable(self, variable):
        return False

    def get_units(self, variable):
        return None


@defaults
class FooBar(AbstractPyNNNeuronModelStandard):
    @default_initial_values({"foo", "bar"})
    def __init__(self, foo=1, bar=11):
        super().__init__(
            "FooBar", "foobar.aplx", _MyNeuronModel(foo, bar),
            EmptyNeuronComponent(), EmptySynapseType(), EmptyNeuronComponent())

    @property
    def model(self):
        return self._model


class MockNeuron(AbstractPopulationVertex):
    def __init__(self):
        foo_bar = FooBar()
        super().__init__(
            n_neurons=5, label="Mock",
            max_atoms_per_core=None, spikes_per_second=None,
            ring_buffer_sigma=None, min_weights=None, weight_random_sigma=None,
            max_stdp_spike_delta=None, incoming_spike_buffer_size=None,
            neuron_impl=foo_bar.model, pynn_model=foo_bar,
            drop_late_spikes=True, splitter=None, seed=None,
            n_colour_bits=None)


def test_initializable():
    unittest_setup()
    sim.setup(1.0)
    neuron = MockNeuron()
    assert [1, 1, 1, 1, 1] == neuron.get_initial_state_values("foo")
    neuron.set_initial_state_values("foo", 2)
    assert [11, 11, 11, 11, 11] == neuron.get_initial_state_values("bar")


def test_init_by_in():
    unittest_setup()
    sim.setup(1.0)
    neuron = MockNeuron()
    assert [1, 1, 1, 1, 1] == neuron.get_initial_state_values("foo")
    neuron.set_initial_state_values("foo", 11, selector=1)
    assert [1, 11, 1, 1, 1] == neuron.get_initial_state_values("foo")
    neuron.set_initial_state_values("foo", 12, selector=2)
    assert [1, 11, 12, 1, 1] == neuron.get_initial_state_values("foo")
    assert 11 == neuron.get_initial_state_values("bar", selector=1)
    assert 12 == neuron.get_initial_state_values("foo", selector=2)


def test_init_bad():
    unittest_setup()
    neuron = MockNeuron()
    with pytest.raises(KeyError):
        neuron.get_initial_state_values("badvariable")
    with pytest.raises(KeyError):
        assert 1 == neuron.set_initial_state_values("anotherbad", "junk")


def test_initial_values():
    unittest_setup()
    sim.setup(1.0)
    neuron = MockNeuron()
    initial_values = neuron.get_initial_state_values(
        neuron.get_state_variables())
    assert "foo" in initial_values
    assert "bar" in initial_values
    initial_values = neuron.get_initial_state_values(
        neuron.get_state_variables(), selector=3)
    assert {"foo": 1, "bar": 11} == initial_values
