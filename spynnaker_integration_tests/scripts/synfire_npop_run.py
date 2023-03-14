#!/usr/bin/python

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

"""
Synfirechain-like example
"""
import numpy
import pyNN.spiNNaker as p
from spinnaker_testbase.root_test_case import RootTestCase


def do_synfire_npop(nNeurons, n_pops, neurons_per_core, runtime=25000):
    """
    Runs the script Does the run based on the parameters

    :param nNeurons: Number of Neurons in chain
    :type  nNeurons: int
    :param n_pops: Number of populations
    :type  n_pops: int
    :param neurons_per_core: Number of neurons per core
    :type  neurons_per_core: int
    :param runtime: time to run the script for
    :type  runtime: int
    """
    p.setup(timestep=1.0)
    RootTestCase.assert_not_spin_three()
    p.set_number_of_neurons_per_core(p.IF_curr_exp, neurons_per_core)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 2.0
    delay = 1

    connections = list()
    for i in range(0, nNeurons - 1):
        singleConnection = (i, i + 1, weight_to_spike, delay)
        connections.append(singleConnection)

    pop_jump_connection = [(nNeurons - 1, 0, weight_to_spike, 1)]

    injectionConnection = [(0, 0, weight_to_spike, 1)]

    spikeArray = {'spike_times': [[0]]}

    for i in range(0, n_pops):
        populations.append(p.Population(
            nNeurons, p.IF_curr_exp(**cell_params_lif),
            label='pop_{}'.format(i)))

    populations.append(p.Population(
        1, p.SpikeSourceArray(**spikeArray), label='inputSpikes_1'))

    for i in range(0, n_pops):
        projections.append(p.Projection(
            presynaptic_population=populations[i],
            postsynaptic_population=populations[i],
            connector=p.FromListConnector(connections),
            synapse_type=p.StaticSynapse()))

        connector = p.FromListConnector(pop_jump_connection)

        projections.append(p.Projection(
            presynaptic_population=populations[i],
            postsynaptic_population=populations[((i + 1) % n_pops)],
            connector=connector, synapse_type=p.StaticSynapse()))

    projections.append(p.Projection(
        presynaptic_population=populations[n_pops],
        postsynaptic_population=populations[0],
        connector=p.FromListConnector(injectionConnection),
        synapse_type=p.StaticSynapse()))

    for pop_index in range(0, n_pops):
        populations[pop_index].record("spikes")

    p.run(runtime)

    total_spikes = populations[0].spinnaker_get_data("spikes")
    for pop_index in range(1, n_pops):
        spikes = populations[pop_index].spinnaker_get_data("spikes")
        if spikes is not None:
            for spike in spikes:
                spike[0] += (nNeurons * pop_index)
            total_spikes = numpy.concatenate((total_spikes, spikes), axis=0)

    p.end()

    return total_spikes
