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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
import numpy
import unittest


class TestIFCondExpSTDPPairAdditive(BaseTestCase):

    def potentiation_and_depression(self) -> None:
        p.setup(1)
        runtime = 100
        initial_run = 1000  # to negate any initial conditions

        # STDP parameters
        a_plus = 0.1
        a_minus = 0.0375
        tau_plus = 20
        tau_minus = 64
        plastic_delay = 1
        initial_weight = 0.05
        max_weight = 0.5
        min_weight = 0

        pre_spikes = [10, 50]
        extra_spikes = [30]

        for i in range(len(pre_spikes)):
            pre_spikes[i] += initial_run

        for i in range(len(extra_spikes)):
            extra_spikes[i] += initial_run

        # Spike source to send spike via plastic synapse
        pre_pop = p.Population(1, p.SpikeSourceArray,
                               {'spike_times': pre_spikes}, label="pre")

        # Spike source to send spike via static synapse to make
        # post-plastic-synapse neuron fire
        extra_pop = p.Population(1, p.SpikeSourceArray,
                                 {'spike_times': extra_spikes}, label="extra")

        # Post-plastic-synapse population
        post_pop = p.Population(1, p.IF_cond_exp(),  label="post")

        # Create projections
        p.Projection(
            pre_pop, post_pop, p.OneToOneConnector(),
            p.StaticSynapse(weight=0.1, delay=1), receptor_type="excitatory")

        p.Projection(
            extra_pop, post_pop, p.OneToOneConnector(),
            p.StaticSynapse(weight=0.1, delay=1), receptor_type="excitatory")

        syn_plas = p.STDPMechanism(
            timing_dependence=p.extra_models.SpikeNearestPairRule(
                tau_plus=tau_plus, tau_minus=tau_minus,
                A_plus=a_plus, A_minus=a_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min=min_weight,
                                                         w_max=max_weight),
            weight=initial_weight, delay=plastic_delay)

        plastic_synapse = p.Projection(pre_pop, post_pop,
                                       p.OneToOneConnector(),
                                       synapse_type=syn_plas,
                                       receptor_type='excitatory',
                                       download_synapses=True)

        # Record the spikes
        post_pop.record("spikes")

        # Run
        p.run(initial_run + runtime)

        # Get the weights
        weights = plastic_synapse.get('weight', 'list',
                                      with_address=False)

        # Get the spikes
        post_spikes = numpy.array(
            post_pop.get_data('spikes').segments[0].spiketrains[0].magnitude)

        # End the simulation as all information gathered
        p.end()

        # Get the spikes and time differences that will be considered by
        # the simulation (as the last pre-spike will be considered differently)
        pre_spikes_n = numpy.array(pre_spikes)
        last_pre_spike = pre_spikes_n[-1]
        considered_post_spikes = post_spikes[post_spikes < last_pre_spike]
        considered_post_spikes += plastic_delay
        potentiation_times = list()
        depression_times = list()
        for time in pre_spikes_n:
            post_times = considered_post_spikes[considered_post_spikes > time]
            if len(post_times) > 0:
                last_time = post_times[0]
                potentiation_times.append(time - last_time)
            post_times = considered_post_spikes[considered_post_spikes < time]
            if len(post_times) > 0:
                last_time = post_times[-1]
                depression_times.append(last_time - time)

        # Work out the weight according to the rules
        potentiations = a_plus * numpy.exp(
            (numpy.array(potentiation_times) / tau_plus))
        depressions = a_minus * numpy.exp(
            (numpy.array(depression_times) / tau_minus))
        new_weight_exact = \
            initial_weight + numpy.sum(potentiations) - numpy.sum(depressions)

        print("Pre neuron spikes at: {}".format(pre_spikes_n))
        print("Post-neuron spikes at: {}".format(post_spikes))
        target_spikes = [1013, 1032, 1051, 1055]
        self.assertListEqual(list(post_spikes), target_spikes)
        print("New weight exact: {}".format(new_weight_exact))
        print("New weight SpiNNaker: {}".format(weights))

        self.assertTrue(numpy.allclose(weights, new_weight_exact, rtol=0.001))

    def test_potentiation_and_depression(self) -> None:
        self.runsafe(self.potentiation_and_depression)


if __name__ == '__main__':
    unittest.main()
