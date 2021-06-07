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

import random
import time
from spinn_utilities.config_holder import get_config_bool
import spynnaker8 as sim
from spinnaker_testbase import BaseTestCase


class TestBigConnection(BaseTestCase):

    def do_run(self):
        sources = 300
        destinations = 300
        aslist = []
        spiketimes = []
        for s in range(sources):
            for d in range(destinations):
                aslist.append(
                    (s, d, 5 + random.random(), random.randint(1, 5)))
            spiketimes.append([s * 20])

        sim.setup(1.0)
        pop1 = sim.Population(
            sources, sim.SpikeSourceArray(spike_times=spiketimes),
            label="input")
        pop2 = sim.Population(destinations, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=2)
        projection = sim.Projection(
            pop1, pop2, sim.FromListConnector(aslist),
            synapse_type=synapse_type)
        pop2.record("spikes")
        sim.run(sources * 20)
        from_pro = projection.get(["weight", "delay"], "list")
        self.assertEqual(sources * destinations, len(from_pro))
        spikes = pop2.spinnaker_get_data("spikes")
        self.assertEqual(sources * destinations, len(spikes))
        sim.end()

    def do_big(self):
        report_file = self.report_file()
        t_before = time.time()

        self.do_run()

        t_after = time.time()
        results = self.get_run_time_of_BufferExtractor()
        self.report(results, report_file)
        self.report(
            "total run time was: {} seconds\n".format(t_after-t_before),
            report_file)

    def report_file(self):
        if get_config_bool("Java", "use_java"):
            style = "java_"
        else:
            style = "python_"
        if get_config_bool("Machine", "enable_advanced_monitor_support"):
            style += "advanced"
        else:
            style += "simple"
        return "{}_test_big_connection".format(style)
