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

import os
import numpy
import random
import matplotlib.pyplot as plt
from pyNN.utility.plotting import Figure, Panel
import spynnaker8 as p
from spynnaker8.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


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
                       'v_thresh': -40.0
                       }

    # Parameters
    n = 256
    weight_to_spike = 5.0
    delay = 5
    runtime = 200

    # Populations
    exc_pop = p.Population(n, p.IF_curr_exp(**cell_params_lif),
                           label='exc_pop')
    inh_pop = p.Population(n, p.IF_curr_exp(**cell_params_lif),
                           label='inh_pop')

    # SpikeInjector
    injectionConnection = [(0, 0)]
    spikeArray = {'spike_times': [[0]]}
    inj_pop = p.Population(1, p.SpikeSourceArray(**spikeArray),
                           label='inputSpikes_1')

    # Projection for injector
    p.Projection(inj_pop, exc_pop, p.FromListConnector(injectionConnection),
                 p.StaticSynapse(weight=weight_to_spike, delay=delay))

    # Set up fromfileconnector
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    file1 = os.path.join(current_file_path, "large.connections")
    file_connector1 = p.FromFileConnector(file1)

    # Projections between populations
    p.Projection(exc_pop, inh_pop, file_connector1,
                 p.StaticSynapse(weight=2.0, delay=5))
    p.Projection(inh_pop, exc_pop, file_connector1,
                 p.StaticSynapse(weight=1.5, delay=10))
    p.Projection(inh_pop, exc_pop, file_connector1,
                 p.StaticSynapse(weight=1.0, delay=1))

    exc_pop.record(['v', 'spikes'])
    inh_pop.record(['v', 'spikes'])
    p.run(runtime)

    v_exc = exc_pop.get_data('v')
    spikes_exc = exc_pop.get_data('spikes')

    if plot:
        # pylint: disable=no-member
        Figure(
            # raster plot of the presynaptic neurons' spike times
            Panel(spikes_exc.segments[0].spiketrains,
                  yticks=True, markersize=1.2, xlim=(0, runtime), xticks=True),
            # membrane potential of the postsynaptic neurons
            Panel(v_exc.segments[0].filter(name='v')[0],
                  ylabel="Membrane potential (mV)",
                  data_labels=[exc_pop.label], yticks=True,
                  xlim=(0, runtime), xticks=True),
            title="Testing FromFileConnector",
            annotations="Simulated with {}".format(p.name())
        )
        plt.show()

    p.end()

    return v_exc, spikes_exc


class FromFileConnectorLargeTest(BaseTestCase):

    def make_file(self):
        connection_list = []
        for i in range(255):
            connection_list.append(
                (i, random.randint(0, 255), random.random(),
                 random.randint(10, 15)))

        current_file_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_file_path, "large.connections")
        if os.path.exists(path):
            os.remove(path)

        numpy.savetxt(path, connection_list)

    def do_run(self):
        self.make_file()
        v, spikes = do_run(plot=False)
        # any checks go here
        spikes_test = neo_convertor.convert_spikes(spikes)
        self.assertEquals(2, len(spikes_test))

    def test_do_run(self):
        self.runsafe(self.do_run)


if __name__ == '__main__':
    v, spikes = do_run(plot=True)
