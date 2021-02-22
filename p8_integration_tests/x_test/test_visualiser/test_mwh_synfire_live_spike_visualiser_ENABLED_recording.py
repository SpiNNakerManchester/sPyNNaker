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

import spynnaker8 as p
from spynnaker.pyNN.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase


def do_run():
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    nNeurons = 100  # number of neurons in each population
    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 2.0
    delay = 3
    delays = list()
    connections = list()
    for i in range(0, nNeurons):
        delays.append(float(delay))
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, 1)]
    spikeArray = {'spike_times': [[0]]}

    populations.append(p.Population(nNeurons, p.IF_curr_exp(**cell_params_lif),
                                    label='pop_1'))
    populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray),
                                    label='inputSpikes_1'))

    projections.append(p.Projection(populations[0], populations[0],
                                    p.FromListConnector(connections),
                                    p.StaticSynapse(weight=weight_to_spike,
                                                    delay=delay)))
    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector(injectionConnection),
                                    p.StaticSynapse(weight=weight_to_spike,
                                                    delay=1)))

    populations[0].record(['spikes'])
    p.external_devices.activate_live_output_for(populations[0])
    populations[0].add_placement_constraint(0, 0, 2)
    populations[1].add_placement_constraint(0, 0, 3)

    run_time = 1000
    print("Running for {} ms".format(run_time))
    p.run(run_time)

    spikes = neo_convertor.convert_spikes(populations[0].get_data('spikes'))

    p.end()

    return spikes


class TestMWHSynfireEnabledRecording(BaseTestCase):
    def test_run(self):
        spikes = do_run()
        # check something
        self.assertEqual(len(spikes), 200)


if __name__ == '__main__':
    import pylab
    spikes = do_run()
    if spikes is not None:
        print(spikes)
        pylab.figure()
        pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
        pylab.ylabel('neuron id')
        pylab.xlabel('Time/ms')
        pylab.yticks([0, 20, 40, 60, 80, 100])
        pylab.xticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
        pylab.title('spikes')
        pylab.show()
    else:
        print("No spikes received")

# Make some graphs
"""ticks = len(v) / nNeurons

if v != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    for pos in range(0, nNeurons, 20):
        v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in v_for_neuron],
                [i[2] for i in v_for_neuron])
    pylab.show()

if gsyn != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn')
    pylab.title('gsyn')
    for pos in range(0, nNeurons, 20):
        gsyn_for_neuron = gsyn[pos * ticks : (pos + 1) * ticks]
        pylab.plot([i[1] for i in gsyn_for_neuron],
                [i[2] for i in gsyn_for_neuron])
    pylab.show()
"""
# p.end()
