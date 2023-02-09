# Copyright (c) 2017-2023 The University of Manchester
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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase

import numpy


def triplet_additive():
    # -------------------------------------------------------------------
    # This test uses a single data point from the Pfister/Gerstner example
    # which is described and evaluated in more detail in
    # PyNN8Examples/extra_models_examples/stdp_triplet.py
    # -------------------------------------------------------------------

    # -------------------------------------------------------------------
    # Common parameters
    # -------------------------------------------------------------------
    start_time = 100
    num_pairs = 60
    start_w = 0.5
    freq = 10
    delta_t = [-10, 10]

    # -------------------------------------------------------------------
    # Experiment loop
    # -------------------------------------------------------------------
    # Population parameters
    model = sim.IF_curr_exp
    cell_params = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 10.0,
                   'tau_refrac': 2.0, 'tau_syn_E': 2.5, 'tau_syn_I': 2.5,
                   'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -55.4}

    # SpiNNaker setup
    sim.setup(timestep=1.0, min_delay=1.0)

    # Sweep times and frequencies
    projections = []
    sim_time = 0
    for t in delta_t:
        # Neuron populations
        pre_pop = sim.Population(1, model(**cell_params))
        post_pop = sim.Population(1, model(**cell_params))

        # Stimulating populations
        pre_times = [start_time - 1 + (s * int(1000.0 / float(freq)))
                     for s in range(num_pairs + 1)]
        post_times = [start_time + t + (s * int(1000.0 / float(freq)))
                      for s in range(num_pairs)]

        # pre_times = generate_fixed_frequency_test_data(
        #     f, start_time - 1, num_pairs + 1)
        # post_times = generate_fixed_frequency_test_data(
        #     f, start_time + t, num_pairs)
        pre_stim = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[pre_times]))
        post_stim = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[post_times]))

        # Update simulation time
        # You can not nest max or a int and a list
        # pylint: disable=nested-min-max
        sim_time = max(sim_time, max(max(pre_times), max(post_times)) + 100)

        # Connections between spike sources and neuron populations
        ee_connector = sim.OneToOneConnector()
        sim.Projection(
            pre_stim, pre_pop, ee_connector, receptor_type='excitatory',
            synapse_type=sim.StaticSynapse(weight=2))
        sim.Projection(
            post_stim, post_pop, ee_connector, receptor_type='excitatory',
            synapse_type=sim.StaticSynapse(weight=2))

        # **HACK**
        param_scale = 0.5

        # Plastic Connection between pre_pop and post_pop
        # Sjostrom visual cortex min-triplet params
        stdp_model = sim.STDPMechanism(
            timing_dependence=sim.extra_models.PfisterSpikeTriplet(
                tau_plus=16.8, tau_minus=33.7, tau_x=101, tau_y=114,
                A_plus=param_scale * 0.0, A_minus=param_scale * 7.1e-3),
            weight_dependence=sim.extra_models.WeightDependenceAdditiveTriplet(
                w_min=0.0, w_max=1.0, A3_plus=param_scale * 6.5e-3,
                A3_minus=param_scale * 0.0),
            weight=start_w, delay=1)

        projections.append(sim.Projection(
            pre_pop, post_pop, sim.OneToOneConnector(),
            synapse_type=stdp_model))

    # Run simulation
    sim.run(sim_time)

    # Read weights from each parameter value being tested
    weights = []
    weights.append([p.get('weight', 'list', with_address=False)
                    for p in projections])

    # End simulation on SpiNNaker
    sim.end()

    test_weights = [[0.324], [0.549]]

    assert numpy.allclose(weights[0], test_weights, rtol=0.001)


class TestSTDPPairAdditive(BaseTestCase):

    def test_triplet_additive(self):
        self.runsafe(triplet_additive)


if __name__ == '__main__':
    triplet_additive()
