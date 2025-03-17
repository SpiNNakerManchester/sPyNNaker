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

from typing import Optional, Sequence

import pytest
import pyNN.spiNNaker as sim

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary

from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, AbstractPyNNNeuronModelStandard)
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModel

from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)

from unittests.mocks import (
    MockInputType, MockSynapseType, MockThresholdType)


class _MyNeuronModel(NeuronModel):
    def __init__(self, foo: int, bar: int):
        super().__init__([], {})
        self._foo = foo
        self._bar = bar

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        pass

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        state_variables["foo"] = self._foo
        state_variables["bar"] = self._bar


class FooBar(AbstractPyNNNeuronModelStandard):
    @default_initial_values({"foo", "bar"})
    def __init__(self, foo:int = 1, bar: int = 11):
        super().__init__(
            "FooBar", "foobar.aplx", _MyNeuronModel(foo, bar),
            MockInputType(), MockSynapseType(), MockThresholdType())


class MockNeuron(AbstractPopulationVertex):
    def __init__(self) -> None:
        foo_bar = FooBar()
        super().__init__(
            n_neurons=5, label="Mock",
            max_atoms_per_core=4, spikes_per_second=None,
            ring_buffer_sigma=None, incoming_spike_buffer_size=None,
            max_expected_summed_weight=None,
            neuron_impl=foo_bar._model, pynn_model=foo_bar,
            drop_late_spikes=True, splitter=None, seed=None,
            n_colour_bits=None)


def test_initializable() -> None:
    unittest_setup()
    sim.setup(1.0)
    neuron = MockNeuron()
    assert [1, 1, 1, 1, 1] == neuron.get_initial_state_values("foo")
    neuron.set_initial_state_values("foo", 2)
    assert [11, 11, 11, 11, 11] == neuron.get_initial_state_values("bar")


def test_init_by_in() -> None:
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


def test_init_bad() -> None:
    unittest_setup()
    neuron = MockNeuron()
    with pytest.raises(KeyError):
        neuron.get_initial_state_values("badvariable")
    with pytest.raises(KeyError):
        assert 1 == neuron.set_initial_state_values(
            "anotherbad", "junk")  # type: ignore[arg-type]


def test_initial_values()  -> None:
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
