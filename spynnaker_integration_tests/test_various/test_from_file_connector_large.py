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

import os
import random

import numpy
import matplotlib.pyplot as plt
from neo import Block
from pyNN.utility.plotting import Figure, Panel
import pyNN.spiNNaker as p

from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(plot: bool) -> Block:

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

    def make_file(self) -> None:
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

    def do_run(self) -> None:
        self.make_file()
        v, spikes = do_run(plot=False)
        # any checks go here
        spikes_test = neo_convertor.convert_spikes(spikes)
        self.assertEqual(2, len(spikes_test))

    def test_do_run(self) -> None:
        self.runsafe(self.do_run)


if __name__ == '__main__':
    v, spikes = do_run(plot=True)
