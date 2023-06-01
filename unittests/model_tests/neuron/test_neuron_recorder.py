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
from data_specification.enums import DataType
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.common import NeuronRecorder


def test_simple_record():
    unittest_setup()
    recordables = ["v", "gsyn_exc", "gsyn_inh"]

    data_types = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    nr = NeuronRecorder(recordables, data_types, [], 100, [], [], [], [])
    assert (frozenset(["v", "gsyn_exc", "gsyn_inh"]) ==
            frozenset(nr.get_recordable_variables()))
    assert [] == list(nr.recording_variables)
    nr.set_recording("v", True)
    assert ["v"] == list(nr.recording_variables)


def test_recording_variables():
    unittest_setup()
    recordables = ["v", "gsyn_exc", "gsyn_inh"]

    data_types = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    nr = NeuronRecorder(recordables, data_types, [], 100, [], [], [], [])
    assert [] == list(nr.recording_variables)
    nr.set_recording("v", True)
    nr.set_recording("gsyn_inh", True)
    assert ["v", "gsyn_inh"] == list(nr.recording_variables)
    assert [0, 2] == list(nr.recorded_region_ids)
