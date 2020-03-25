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
from data_specification.enums import DataType
from unittests.mocks import MockSimulator
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.models.common import NeuronRecorder
from spynnaker.pyNN.utilities.spynnaker_failed_state import (
    SpynnakerFailedState)


def test_simple_record():
    simulator = MockSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    recordables = ["v", "gsyn_exc", "gsyn_inh"]

    data_types = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    nr = NeuronRecorder(recordables, data_types, [], 100)
    assert(frozenset(["v", "gsyn_exc", "gsyn_inh"]) ==
           frozenset(nr.get_recordable_variables()))
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    assert(["v"] == nr.recording_variables)


def test_recording_variables():
    simulator = MockSimulator()
    globals_variables.set_failed_state(SpynnakerFailedState())
    globals_variables.set_simulator(simulator)

    recordables = ["v", "gsyn_exc", "gsyn_inh"]

    data_types = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    nr = NeuronRecorder(recordables, data_types, [], 100)
    assert([] == nr.recording_variables)
    nr.set_recording("v", True)
    nr.set_recording("gsyn_inh", True)
    assert(["v", "gsyn_inh"] == nr.recording_variables)
    assert([0, 2] == nr.recorded_region_ids)
