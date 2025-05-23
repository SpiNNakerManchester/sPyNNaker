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

from typing import Optional, Union, Tuple

import matplotlib.pyplot as plt
from neo import Block
import numpy
from pyNN.space import BaseStructure
from pyNN.utility.plotting import Figure, Panel
import pyNN.spiNNaker as p

from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(plot: bool) -> Tuple[Block, Block, Block, Block]:

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


def do_larger_array(plot: bool) -> Tuple[Block, Block, Block]:
    p.setup(timestep=1.0)

    n_i = 64
    n_e = 64

    spikeArray = {'spike_times': [0]}
    input_pop = p.Population(n_e, p.SpikeSourceArray(**spikeArray),
                             label='inputSpikes')
    excit_pop = p.Population(n_e, p.IF_curr_exp, label='excit')
    inhit_pop = p.Population(n_i, p.IF_curr_exp, label='inhib')
    p.Projection(input_pop, excit_pop, p.AllToAllConnector(),
                 synapse_type=p.StaticSynapse(weight=5),
                 receptor_type='excitatory')

    ie_conn = numpy.ones((n_i, n_e))
    for i in range(n_e):
        ie_conn[i, i] = 0

    p.Projection(excit_pop, inhit_pop, p.OneToOneConnector(),
                 synapse_type=p.StaticSynapse(weight=2),
                 receptor_type='inhibitory')

    ie_projec = p.Projection(inhit_pop, excit_pop, p.ArrayConnector(ie_conn),
                             synapse_type=p.StaticSynapse(weight=3),
                             receptor_type='excitatory')

    excit_pop.record(["spikes", "v"])

    runtime = 1000
    p.run(runtime)

    ie_conns = ie_projec.get(['weight', 'delay'], 'list')
    v = excit_pop.get_data("v")
    spikes = excit_pop.get_data("spikes")

    if plot:
        Figure(
            # raster plot of the presynaptic neurons' spike times
            Panel(spikes.segments[0].spiketrains,
                  yticks=True, markersize=1.2, xlim=(0, runtime), xticks=True),
            # membrane potential of the postsynaptic neurons
            Panel(v.segments[0].filter(name='v')[0],
                  ylabel="Membrane potential (mV)",
                  data_labels=[inhit_pop.label], yticks=True,
                  xlim=(0, runtime), xticks=True),
            title="Testing ArrayConnector",
            annotations="Simulated with {}".format(p.name())
        )
        plt.show()

    p.end()

    return v, spikes, ie_conns


class ArrayConnectorTest(BaseTestCase):

    def a_run(self) -> None:
        v, spikes, v2, spikes2 = do_run(plot=False)
        # any checks go here
        spikes_test = neo_convertor.convert_spikes(spikes)
        spikes_test2 = neo_convertor.convert_spikes(spikes2)
        self.assertEqual(263, len(spikes_test))
        self.assertEqual(263, len(spikes_test2))

    def test_a_run(self) -> None:
        self.runsafe(self.a_run)

    def larger_array(self) -> None:
        v, spikes, conns = do_larger_array(plot=False)
        # checks go here
        spikes_test = neo_convertor.convert_spikes(spikes)
        self.assertEqual(4032, len(conns))
        self.assertEqual(640, len(spikes_test))

    def test_larger_array(self) -> None:
        self.runsafe(self.larger_array)

    def do_array_nd_test(
            self, neurons_per_core_pre: Tuple[int, ...], pre_size: int,
            pre_shape: BaseStructure,
            neurons_per_core_post: Union[int, Tuple[int, ...]],
            post_size: int, post_shape: Optional[BaseStructure]) -> None:
        p.setup(1.0)
        pre = p.Population(
            pre_size, p.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = p.Population(
            post_size, p.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)

        # Make up to 100 unique connections (might be less if less atoms)
        random_conns = numpy.unique(numpy.random.randint(
            0, (pre_size, post_size), (100, 2)), axis=0)
        conn_matrix = numpy.zeros((pre_size, post_size), dtype=numpy.uint)
        conn_matrix[random_conns[:, 0], random_conns[:, 1]] = 1

        proj = p.Projection(
            pre, post, p.ArrayConnector(conn_matrix),
            p.StaticSynapse(weight=1.0, delay=1.0))
        p.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        p.end()

        assert numpy.array_equal(numpy.sort(random_conns, axis=0),
                                 numpy.sort(conns, axis=0))

    def test_3d_to_1d_array(self) -> None:
        self.do_array_nd_test((5, 2, 1), 10 * 6 * 4, p.Grid3D(10 / 6, 10 / 4),
                              12, 40, None)

    def test_2d_to_2d_array(self) -> None:
        self.do_array_nd_test((3, 4), 9 * 8, p.Grid2D(9 / 8),
                              (1, 2), 5 * 6, p.Grid2D(5 / 6))


if __name__ == '__main__':
    v, spikes, v2, spikes2 = do_run(plot=True)
    v, spikes, conns = do_larger_array(plot=True)
