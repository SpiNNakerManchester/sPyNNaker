# Copyright (c) 2017-2021 The University of Manchester
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
import time
from unittest import SkipTest
from spinn_utilities.config_holder import get_config_bool
from spinn_front_end_common.interface.provenance import GlobalProvenance
from spynnaker.pyNN.exceptions import ConfigurationException
import pyNN.spiNNaker as sim
from spynnaker_integration_tests.scripts import check_data
from spinnaker_testbase import BaseTestCase

CHIPS_PER_BOARD_EXCLUDING_SAFETY = 43.19


class ManyBoards(BaseTestCase):
    n_boards = 1
    n_neurons = 400
    simtime = 600

    def add_pop(self, x, y, n_neurons, input):
        pop = sim.Population(
            n_neurons, sim.IF_curr_exp(), label="pop_{}_{}".format(x, y))
        pop.add_placement_constraint(x=x, y=y)
        sim.Projection(input, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop.record("all")
        return pop

    def setup(self):
        sim.setup(timestep=1.0, n_boards_required=self.n_boards)
        try:
            machine = sim.get_machine()
        except ConfigurationException as oops:
            if "Failure to detect machine " in str(oops):
                raise SkipTest(
                    "You Need at least {} boards to run this test".format(
                        self.n_boards)) from oops
            raise oops

        input_spikes = list(range(0, self.simtime - 100, 10))
        self._expected_spikes = len(input_spikes)
        input = sim.Population(1, sim.SpikeSourceArray(
            spike_times=input_spikes), label="input")
        self._pops = []
        for i, chip in enumerate(machine.ethernet_connected_chips):
            if i >= self.n_boards:
                break
            offset = machine.BOARD_48_CHIPS[i % 48]
            x = chip.x + offset[0]
            y = chip.y + offset[1]
            # safety code in case there is a hole in the board
            if not machine.is_chip_at(x, y):
                x = chip.x
                y = chip.y
            self._pops.append(self.add_pop(x, y, self.n_neurons, input))

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
            results = db.get_run_time_of_BufferExtractor()
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
    """
    main entrance method
    """
    me = ManyBoards()
    run = me.do_run()
    me.check_all_data()
    run.end()
