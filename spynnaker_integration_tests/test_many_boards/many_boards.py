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
import time
from spinn_utilities.config_holder import get_config_bool
from spinn_front_end_common.interface.provenance import GlobalProvenance
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import ConfigurationException
import pyNN.spiNNaker as sim
from spynnaker_integration_tests.scripts import check_data
from spinnaker_testbase import BaseTestCase

CHIPS_PER_BOARD_EXCLUDING_SAFETY = 43.19


class ManyBoards(BaseTestCase):
    # pylint: disable=attribute-defined-outside-init
    n_boards = 1
    n_neurons = 400
    simtime = 600

    def add_pop(self, x, y, n_neurons, input_pop):
        pop = sim.Population(
            n_neurons, sim.IF_curr_exp(), label="pop_{}_{}".format(x, y))
        pop.add_placement_constraint(x=x, y=y)
        sim.Projection(input_pop, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop.record("all")
        return pop

    def setup(self):
        sim.setup(timestep=1.0, n_boards_required=self.n_boards)
        try:
            machine = sim.get_machine()
        except ConfigurationException as oops:
            if "Failure to detect machine " in str(oops):
                SpynnakerDataView.raise_skiptest(
                    f"You Need at least {self.n_boards} boards for this test",
                    oops)
            raise oops

        input_spikes = list(range(0, self.simtime - 100, 10))
        self._expected_spikes = len(input_spikes)
        input_pop = sim.Population(1, sim.SpikeSourceArray(
            spike_times=input_spikes), label="input")
        self._pops = []
        for i, chip in enumerate(machine.ethernet_connected_chips):
            if i >= self.n_boards:
                break
            version = SpynnakerDataView.get_machine_version()
            offset = version.expected_xys[i % 48]
            x = chip.x + offset[0]
            y = chip.y + offset[1]
            # safety code in case there is a hole in the board
            if not machine.is_chip_at(x, y):
                x = chip.x
                y = chip.y
            self._pops.append(self.add_pop(x, y, self.n_neurons, input_pop))

    def report_file(self):
        if get_config_bool("Java", "use_java"):
            style = "java_"
        else:
            style = "python_"
        if get_config_bool("Machine", "enable_advanced_monitor_support"):
            style += "advanced"
        else:
            style += "simple"
        return "{}_n_boards={}_n_neurons={}_simtime={}".format(
            style, self.n_boards, self.n_neurons, self.simtime)

    def do_run(self):
        self.setup()
        report_file = self.report_file()
        t_before = time.time()
        sim.run(self.simtime)
        t_after_machine = time.time()
        for pop in self._pops:
            check_data(pop, self._expected_spikes, self.simtime)
        t_after_check = time.time()
        with GlobalProvenance() as db:
            results = db.get_run_time_of_buffer_extractor()
        self.report(results, report_file)
        self.report(
            "machine run time was: {} seconds\n".format(
                t_after_machine-t_before),
            report_file)
        self.report(
            "total run time was: {} seconds\n".format(t_after_check-t_before),
            report_file)
        sim.end()


if __name__ == '__main__':
    me = ManyBoards()
    me.do_run()
