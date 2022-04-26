# Copyright (c) 2017-2022 The University of Manchester
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

from neo.io import PickleIO
from spinn_front_end_common.utilities.exceptions import ConfigurationException
import pyNN.spiNNaker as sim
from spynnaker.pyNN.utilities import neo_compare
from spinnaker_testbase import BaseTestCase

pickle_path = "data.pickle"


class TestRecordingOnOff(BaseTestCase):
    # pylint: disable=no-member

    def record_all(self):
        sim.setup(timestep=1)
        simtime = 100
        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0, 30]),
                               label="input")
        pop = sim.Population(32, sim.IF_curr_exp(), label="pop")
        sim.Projection(input, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop.record("all")
        sim.run(simtime)

        neo = pop.get_data("all")
        pop.write_data(pickle_path, "all")
        io = PickleIO(filename=pickle_path)
        all_saved = io.read()[0]
        neo_compare.compare_blocks(neo, all_saved)
        assert len(neo.segments[0].spiketrains) > 0
        assert len(neo.segments[0].filter(name="v")) > 0
        assert len(neo.segments[0].filter(name="gsyn_exc")) > 0

        spikes_neo = pop.get_data("spikes")
        pop.write_data(pickle_path, "spikes")
        io = PickleIO(filename=pickle_path)
        spikes_saved = io.read()[0]
        neo_compare.compare_blocks(spikes_neo, spikes_saved)
        assert len(spikes_neo.segments[0].spiketrains) > 0
        assert len(spikes_neo.segments[0].filter(name="v")) == 0
        assert len(spikes_neo.segments[0].filter(name="gsyn_exc")) == 0

        v_neo = pop.get_data("v")
        pop.write_data(pickle_path, "v")
        io = PickleIO(filename=pickle_path)
        v_saved = io.read()[0]
        neo_compare.compare_blocks(v_neo, v_saved)
        assert len(v_neo.segments[0].spiketrains) == 0
        assert len(v_neo.segments[0].filter(name="v")) > 0
        assert len(v_neo.segments[0].filter(name="gsyn_exc")) == 0

        gsyn_neo = pop.get_data("gsyn_exc")
        pop.write_data(pickle_path, "gsyn_exc")
        io = PickleIO(filename=pickle_path)
        gsyn_saved = io.read()[0]
        neo_compare.compare_blocks(gsyn_neo, gsyn_saved)
        assert len(gsyn_neo.segments[0].spiketrains) == 0
        assert len(spikes_neo.segments[0].filter(name="v")) == 0
        assert len(gsyn_neo.segments[0].filter(name="gsyn_exc")) > 0

    def test_record_all(self):
        self.runsafe(self.record_all)

    def record_v(self):
        sim.setup(timestep=1)
        simtime = 100
        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0, 30]),
                               label="input")
        pop = sim.Population(32, sim.IF_curr_exp(), label="pop")
        sim.Projection(input, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop.record("v")
        sim.run(simtime)

        neo = pop.get_data("all")
        pop.write_data(pickle_path, "all")
        io = PickleIO(filename=pickle_path)
        saved = io.read()[0]
        neo_compare.compare_blocks(neo, saved)
        assert len(neo.segments[0].spiketrains) == 0
        assert len(neo.segments[0].filter(name="v")) > 0
        assert len(neo.segments[0].filter(name="gsyn_exc")) == 0

        v_neo = pop.get_data("v")
        pop.write_data(pickle_path, "v")
        io = PickleIO(filename=pickle_path)
        v_saved = io.read()[0]
        neo_compare.compare_blocks(v_neo, v_saved)
        neo_compare.compare_blocks(v_neo, neo)

        with self.assertRaises(ConfigurationException):
            pop.get_data("spikes")
        with self.assertRaises(ConfigurationException):
            pop.get_data("gsyn_exc")
        with self.assertRaises(ConfigurationException):
            pop.write_data(pickle_path, "spikes")
        with self.assertRaises(ConfigurationException):
            pop.write_data(pickle_path, "gsyn_exc")

    def test_record_v(self):
        self.runsafe(self.record_v)
