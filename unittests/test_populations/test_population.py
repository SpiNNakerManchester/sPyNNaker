from spynnaker.pyNN.models.neuron.builds import IFCurrExpBase
from spynnaker.pyNN.models.pynn_population_common import PyNNPopulationCommon
from unittests.mocks import MockSimulator


def test_selector():
    simulator = MockSimulator.setup()
    model = IFCurrExpBase()
    pop_1 = PyNNPopulationCommon(spinnaker_control=simulator, size=5,
                                 label="Test", constraints=None, model=model,
                                 structure=None, initial_values=None)
    pop_1.set("tau_m", 2)
    values = pop_1.get("tau_m")
    assert [2, 2, 2, 2, 2] == values
    values = pop_1.get_by_selector(slice(1, 3), "tau_m")
    assert [2, 2] == values
    pop_1.set_by_selector(slice(1, 3), "tau_m", 3)
    values = pop_1.get("tau_m")
    assert [2, 3, 3, 2, 2] == values
    values = pop_1.get(["cm", "v_thresh"])
    assert [1.0, 1.0, 1.0, 1.0, 1.0] == values['cm']
    assert [-50.0, -50.0, -50.0, -50.0, -50.0] == values["v_thresh"]
    values = pop_1.get_by_selector([1, 3, 4], ["cm", "v_thresh"])
    assert [1.0, 1.0, 1.0] == values['cm']
    assert [-50.0, -50.0, -50.0] == values["v_thresh"]
