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

import matplotlib.pyplot as plt
import numpy
from pyNN.utility.plotting import Figure, Panel
import spynnaker as p
from spynnaker.pyNNutilities import neo_convertor
from spynnaker_integration_tests.base_test_case import BaseTestCase


def do_run(plot):

    p.setup(timestep=1.0)

    cell_params_lif = {'cm': 0.25,
                       'i_offset': 0.0,
                       'tau_m': 20.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 5.0,
                       'tau_syn_I': 5.0,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -50.0
                       }

    # Parameters
    nNeurons = 200
    weight_to_spike = 2.0
    delay = 17
    runtime = 5000
    p.set_number_of_neurons_per_core(p.IF_curr_exp, nNeurons / 2)

    # Populations
    pop = p.Population(nNeurons, p.IF_curr_exp(**cell_params_lif),
                       label='pop_1')
    pop2 = p.Population(nNeurons, p.IF_curr_exp(**cell_params_lif),
                        label='pop_2')

    # create loopConnections array for first population using numpy linspaces
    loopConnections = numpy.zeros((nNeurons, nNeurons))
    for i in range(nNeurons):
        if i != (nNeurons-1):
            loopConnections[i, i+1] = True
        else:
            loopConnections[i, 0] = True

    # do the same for the second population, but just for even numbered neurons
    loopConnections2 = numpy.zeros((nNeurons, nNeurons))
    for i in range(0, nNeurons, 2):
        if i != (nNeurons - 2):
            loopConnections2[i, i+2] = True
        else:
            loopConnections2[i, 0] = True

    # SpikeInjector
    injectionConnection = numpy.zeros((1, nNeurons))
    injectionConnection[0, 0] = True
    spikeArray = {'spike_times': [[0]]}
    inj_pop = p.Population(1, p.SpikeSourceArray(**spikeArray),
                           label='inputSpikes_1')

    # Projection for injector
    p.Projection(inj_pop, pop, p.ArrayConnector(injectionConnection),
                 p.StaticSynapse(weight=weight_to_spike, delay=1))
    p.Projection(inj_pop, pop2, p.ArrayConnector(injectionConnection),
                 p.StaticSynapse(weight=weight_to_spike, delay=1))

    # Projection within populations
    p.Projection(pop, pop, p.ArrayConnector(loopConnections),
                 p.StaticSynapse(weight=weight_to_spike, delay=delay))
    p.Projection(pop2, pop2, p.ArrayConnector(loopConnections2),
                 p.StaticSynapse(weight=weight_to_spike, delay=delay))

    pop.record(['v', 'spikes'])
    pop2.record(['v', 'spikes'])
    p.run(runtime)

    v = pop.get_data('v')
    spikes = pop.get_data('spikes')
    v2 = pop2.get_data('v')
    spikes2 = pop2.get_data('spikes')

    if plot:
        Figure(
            # raster plot of the presynaptic neurons' spike times
            Panel(spikes.segments[0].spiketrains,
                  yticks=True, markersize=1.2, xlim=(0, runtime), xticks=True),
            # membrane potential of the postsynaptic neurons
            Panel(v.segments[0].filter(name='v')[0],
                  ylabel="Membrane potential (mV)",
                  data_labels=[pop.label], yticks=True,
                  xlim=(0, runtime), xticks=True),
            Panel(spikes2.segments[0].spiketrains,
                  yticks=True, markersize=1.2, xlim=(0, runtime), xticks=True),
            # membrane potential of the postsynaptic neurons
            Panel(v2.segments[0].filter(name='v')[0],
                  ylabel="Membrane potential (mV)",
                  data_labels=[pop2.label], yticks=True,
                  xlim=(0, runtime), xticks=True),
            title="Testing ArrayConnector",
            annotations="Simulated with {}".format(p.name())
        )
        plt.show()

    p.end()

    return v, spikes, v2, spikes2


class ArrayConnectorTest(BaseTestCase):

    def a_run(self):
        v, spikes, v2, spikes2 = do_run(plot=False)
        # any checks go here
        spikes_test = neo_convertor.convert_spikes(spikes)
        spikes_test2 = neo_convertor.convert_spikes(spikes2)
        self.assertEqual(263, len(spikes_test))
        self.assertEqual(263, len(spikes_test2))

    def test_a_run(self):
        self.runsafe(self.a_run)


if __name__ == '__main__':
    v, spikes, v2, spikes2 = do_run(plot=True)
