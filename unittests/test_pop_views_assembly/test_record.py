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
from spinn_front_end_common.utilities.exceptions import ConfigurationException
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestPopulation(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_depricated(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(4, sim.IF_curr_exp())
        assert [] == pop._vertex.get_recording_variables()
        target = {"v", 'gsyn_exc', 'gsyn_inh'}
        pop.record(target)
        assert target == set(pop._vertex.get_recording_variables())
        sim.end()

    def test_set_many(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(10, sim.IF_curr_exp())
        view = pop[2:5]
        view.record(["v", "spikes"])
        target = {"spikes", "v"}
        assert target == set(pop._vertex.get_recording_variables())
        target1 = [2, 3, 4]
        assert target1 == pop._vertex.neuron_recorder._indexes["v"]
        view2 = pop[4:7]
        view2.record("v")
        target2 = [2, 3, 4, 5, 6]
        assert target2 == pop._vertex.neuron_recorder._indexes["v"]
        assert target1 == pop._vertex.neuron_recorder._indexes["spikes"]
        sim.end()

    def test_same_rates(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(10, sim.IF_curr_exp())
        view = pop[2:5]
        view.record(["v", "spikes"], sampling_interval=2)
        target = {"spikes", "v"}
        assert target == set(pop._vertex.get_recording_variables())
        target1 = [2, 3, 4]
        assert target1 == pop._vertex.neuron_recorder._indexes["v"]
        view2 = pop[4:7]
        view2.record("v", sampling_interval=2)
        target2 = [2, 3, 4, 5, 6]
        assert target2 == pop._vertex.neuron_recorder._indexes["v"]
        assert target1 == pop._vertex.neuron_recorder._indexes["spikes"]
        sim.end()

    def test_different_rates(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(10, sim.IF_curr_exp())
        view = pop[2:5]
        view.record(["v", "spikes"], sampling_interval=2)
        view2 = pop[4:7]
        with pytest.raises(ConfigurationException):
            view2.record("v")
        sim.end()

    def test_different_rates2(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(10, sim.IF_curr_exp())
        view = pop[2:5]
        view.record(["v"], sampling_interval=2)
        view2 = pop[1:7]
        # work here as overrighting all indexes
        view2.record("v")
        sim.end()

    def test_record_with_indexes(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(10, sim.IF_curr_exp())
        pop[2, 3, 4].record("v", to_file=None, sampling_interval=None)
        target = {"v"}
        assert target == set(pop._vertex.get_recording_variables())
        target1 = [2, 3, 4]
        assert target1 == pop._vertex.neuron_recorder._indexes["v"]
        view2 = pop[4:7]
        view2.record(None)
        target2 = [2, 3]
        assert target2 == pop._vertex.neuron_recorder._indexes["v"]
        sim.end()

    def test_record_all_of_by_indexes(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp())
        pop.record("v")
        assert {"v"} == set(pop._vertex.get_recording_variables())
        view1 = pop[0:3]
        view1.record(None)
        assert [3, 4] == pop._vertex.neuron_recorder._indexes["v"]
        assert {"v"} == set(pop._vertex.get_recording_variables())
        view2 = pop[3:]
        view2.record(None)
        assert pop._vertex.neuron_recorder._indexes["v"] is None
        assert len(pop._vertex.get_recording_variables()) == 0
        sim.end()

    def test_clash(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp())
        pop.record("v")
        with pytest.raises(ConfigurationException):
            pop.record(None, sampling_interval=2)
        sim.end()
