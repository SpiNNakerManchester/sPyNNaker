from pacman.model.graphs.common import Slice
from spynnaker.pyNN.models.common import NeuronRecorder


def test_simple_record():
    nr = NeuronRecorder(["v", "gsyn_exc", "gsyn_inh"], 100)
    assert(["v", "gsyn_exc", "gsyn_inh"] == nr.get_recordable_variables())
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    assert(["v"] == nr.recording_variables)
    slice = Slice(0, 50)
    gps = nr.get_global_parameters(slice)
    assert (gps[0].get_value() == 1)
