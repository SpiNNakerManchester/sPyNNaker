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

import pyNN.spiNNaker as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run():
    p.setup(timestep=1, min_delay=1)

    spiker = p.Population(1, p.SpikeSourceArray(spike_times=[[5, 25]]),
                          label='inputSSA')

    if_pop = p.Population(1, p.IF_cond_exp(), label='pop')

    if_pop.record("spikes")
    if_pop.record("v")

    runtime = 30

    # Create projection with delay such that the second spike occurs after
    # the run has finished
    weight = 5.0
    delay = 7
    p.Projection(spiker, if_pop, p.OneToOneConnector(),
                 synapse_type=p.StaticSynapse(weight=weight, delay=delay),
                 receptor_type="excitatory", source=None, space=None)

    p.run(runtime)
    all1 = if_pop.get_data(["spikes", "v"])

    # Reset (to time=0) and run again
    p.reset()
    p.run(runtime)
    all2 = if_pop.get_data(["spikes", "v"])

    p.end()

    return (all1, all2)


class ResetClearsDelayedSpikeTest(BaseTestCase):
    def check_run(self):
        all1, all2 = do_run()
        spikes1 = neo_convertor.convert_spiketrains(
            all1.segments[0].spiketrains)
        spikes2 = neo_convertor.convert_spiketrains(
            all2.segments[1].spiketrains)
        self.assertEqual(spikes1.all(), spikes2.all())
        v1 = neo_convertor.convert_data(all1, name="v", run=0)
        v2 = neo_convertor.convert_data(all2, name="v", run=1)
        self.assertEqual(v1.all(), v2.all())

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    all1, all2 = do_run()
    spikes1 = neo_convertor.convert_spiketrains(all1.segments[0].spiketrains)
    print(spikes1)
    spikes2 = neo_convertor.convert_spiketrains(all2.segments[1].spiketrains)
    print(spikes2)
    v1 = neo_convertor.convert_data(all1, name="v", run=0)
    print(v1)
    v2 = neo_convertor.convert_data(all2, name="v", run=1)
    print(v2)
