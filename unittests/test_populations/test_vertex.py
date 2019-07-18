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
import numpy
from spynnaker.pyNN.models.neuron import (
    AbstractPopulationVertex, AbstractPyNNNeuronModelStandard)
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
from spynnaker.pyNN.models.neuron.neuron_models import AbstractNeuronModel
from spynnaker.pyNN.models.defaults import default_initial_values, defaults
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)
from unittests.mocks import MockSimulator


class EmptyNeuronComponent(AbstractStandardNeuronComponent):

    def __init__(self):
        AbstractStandardNeuronComponent.__init__(self, [])

    def get_n_cpu_cycles(self, n_neurons):
        return 0

    def add_parameters(self, parameters):
        pass

    def add_state_variables(self, state_variables):
        pass

    def get_values(self, parameters, state_variables, vertex_slice):
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


class _MyNeuronModel(AbstractNeuronModel):

    def __init__(self, foo, bar):
        AbstractNeuronModel.__init__(self, [], [])
        self._foo = foo
        self._bar = bar

    def get_n_cpu_cycles(self, n_neurons):
        return 0

    def add_parameters(self, parameters):
        pass

    def add_state_variables(self, state_variables):
        state_variables["foo"] = self._foo
        state_variables["bar"] = self._bar

    def get_values(self, parameters, state_variables, vertex_slice):
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
        super(FooBar, self).__init__(
            "FooBar", "foobar.aplx", _MyNeuronModel(foo, bar),
            EmptyNeuronComponent(), EmptySynapseType(), EmptyNeuronComponent())

    @property
    def model(self):
        return self._model


class MockNeuron(AbstractPopulationVertex):

    def __init__(self):
        foo_bar = FooBar()

        super(MockNeuron, self).__init__(
            n_neurons=5, label="Mock", constraints=None,
            max_atoms_per_core=None, spikes_per_second=None,
            ring_buffer_sigma=None, incoming_spike_buffer_size=None,
            neuron_impl=foo_bar.model, pynn_model=foo_bar)


def test_initializable():
    MockSimulator.setup()
    neuron = MockNeuron()
    assert [1, 1, 1, 1, 1] == neuron.get_initial_value("foo")
    neuron.initialize("foo", 2)
    assert [2, 2, 2, 2, 2] == neuron.get_initial_value("foo_init")
    assert [11, 11, 11, 11, 11] == neuron.get_initial_value("bar_init")
    assert [11, 11, 11, 11, 11] == neuron.get_initial_value("bar")


def test_init_by_in():
    MockSimulator.setup()
    neuron = MockNeuron()
    assert [1, 1, 1, 1, 1] == neuron.get_initial_value("foo")
    neuron.set_initial_value(variable="foo", value=11, selector=1)
    assert [1, 11, 1, 1, 1] == neuron.get_initial_value("foo")
    neuron.set_initial_value(variable="foo", value=12, selector=2)
    assert [1, 11, 12, 1, 1] == neuron.get_initial_value("foo")
    assert [11] == neuron.get_initial_value("bar", selector=1)
    assert [12] == neuron.get_initial_value("foo", selector=2)


def test_init_bad():
    MockSimulator.setup()
    neuron = MockNeuron()
    with pytest.raises(KeyError):
        neuron.get_initial_value("badvariable")
    with pytest.raises(KeyError):
        assert 1 == neuron.initialize("anotherbad", "junk")


def test_initial_values():
    MockSimulator.setup()
    neuron = MockNeuron()
    initial_values = neuron.initial_values
    assert "foo" in initial_values
    assert "bar" in initial_values
    initial_values = neuron.get_initial_values(selector=3)
    assert {"foo": [1], "bar": [11]} == initial_values
