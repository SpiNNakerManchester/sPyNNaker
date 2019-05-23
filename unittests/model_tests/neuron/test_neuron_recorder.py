from unittests.mocks import MockSimulator
from pacman.model.graphs.common import Slice
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.models.common import NeuronRecorder
from spynnaker.pyNN.utilities.spynnaker_failed_state import (
    SpynnakerFailedState)


class _MockBasicSimulator(object):
    @property
    def machine_time_step(self):
        return 1000


def test_simple_record():
    simulator = _MockBasicSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    nr = NeuronRecorder(["spikes", "v", "gsyn_exc", "gsyn_inh"], 100)
    assert(frozenset(["spikes", "v", "gsyn_exc", "gsyn_inh"]) ==
           frozenset(nr.get_recordable_variables()))
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    assert(["v"] == nr.recording_variables)
    _slice = Slice(0, 50)
    gps = nr.get_global_parameters(_slice)
    # 4 rates second (index "1") is v
    assert (gps[1].get_value() == 1)
    # 4 n_neurons second (index "5") is v
    assert (gps[5].get_value() == _slice.n_atoms)


def test_recording_variables():
    simulator = MockSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    nr = NeuronRecorder(["spikes", "v", "gsyn_exc", "gsyn_inh"], 100)
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    nr.set_recording("gsyn_inh", True)
    assert(["v", "gsyn_inh"] == nr.recording_variables)
    assert([1, 3] == nr.recorded_region_ids)
