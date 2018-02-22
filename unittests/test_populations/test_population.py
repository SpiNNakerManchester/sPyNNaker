from unittests.mocks import MockSimulator
from spynnaker.pyNN.models.pynn_population_common import PyNNPopulationCommon
from spynnaker.pyNN.models.neuron.builds.if_curr_exp_base import IFCurrExpBase

def test_simple():
    simulator = MockSimulator.setup()
    pop = PyNNPopulationCommon(spinnaker_control=simulator, size=5, vertex=None,
                               structure=None, initial_values=None)

def test_init_by_in():
    simulator = MockSimulator.setup()
    vertex = IFCurrExpBase(5)
    pop = PyNNPopulationCommon(spinnaker_control=simulator, size=5, vertex=None,
                               structure=None, initial_values=None)
    assert 1 == pop.get_initial_value("foo")
    pop.set_initial_value(variable="foo", value=11, selector=1)
    assert [1, 11, 1, 1, 1] == pop.get_initial_value("foo")
    pop.set_initial_value(variable="foo", value=12, selector=2)
    assert [1, 11, 12, 1, 1] == pop.get_initial_value("foo")
    assert [11] == pop.get_initial_value("bar", selector=1)
    assert [12] == pop.get_initial_value("foo", selector=2)


def test_initial_values():
    simulator = MockSimulator.setup()
    vertex = IFCurrExpBase(5)
    pop = PyNNPopulationCommon(spinnaker_control=simulator, size=5,
                               vertex=vertex, structure=None,
                               initial_values=None)
    initial_values = pop.initial_values
    assert "foo" in initial_values
    assert "bar" in initial_values
    initial_values = pop.get_initial_values(selector=3)
    assert {"foo": [1], "bar": [11]} == initial_values