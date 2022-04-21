# Copyright (c) 2017-2022 The University of Manchester
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

import numpy
import pyNN.spiNNaker as p
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    calculate_spike_pair_multiplicative_stdp_weight)
from spinnaker_testbase import BaseTestCase


def post_spike_same_time():
    """ Check that the offsets between send times of different spike source
        arrays don't change the outcome of STDP
    """

    # STDP parameters
    a_plus = 0.01
    a_minus = 0.01
    tau_plus = 20
    tau_minus = 20
    plastic_delay = 1
    initial_weight = 4.0
    max_weight = 5.0
    min_weight = 0
    pre_spikes = range(0, 10, 2)

    p.setup(1)
    pre_1 = p.Population(1, p.SpikeSourceArray(pre_spikes), label="pre_1")
    pre_2 = p.Population(1, p.SpikeSourceArray(pre_spikes), label="pre_2")
    post_1 = p.Population(1, p.IF_curr_exp(), label="post_1")
    post_2 = p.Population(1, p.IF_curr_exp(), label="post_2")
    post_1.record("spikes")
    stdp = p.STDPMechanism(
            timing_dependence=p.SpikePairRule(
                tau_plus=tau_plus, tau_minus=tau_minus,
                A_plus=a_plus, A_minus=a_minus),
            weight_dependence=p.MultiplicativeWeightDependence(
                w_min=min_weight, w_max=max_weight),
            weight=initial_weight, delay=plastic_delay)
    conn = p.OneToOneConnector()
    proj_1 = p.Projection(pre_1, post_1, conn, stdp)
    proj_2 = p.Projection(pre_2, post_2, conn, stdp)

    p.run(12)

    # Get the weights
    weights_1 = list(proj_1.get('weight', 'list', with_address=False))
    weights_2 = list(proj_2.get('weight', 'list', with_address=False))

    # Get the spikes
    post_spikes = numpy.array(
        # pylint: disable=no-member
        post_1.get_data('spikes').segments[0].spiketrains[0].magnitude)

    p.end()

    new_weight_exact = calculate_spike_pair_multiplicative_stdp_weight(
        pre_spikes, post_spikes, initial_weight, plastic_delay, min_weight,
        max_weight, a_plus, a_minus, tau_plus, tau_minus)

#     print(weights_1)
#     print(weights_2)
#     print(new_weight_exact)

    assert(len(weights_1) == 1)
    assert(len(weights_2) == 1)
    assert(weights_1[0] == weights_2[0])
    assert(numpy.allclose(weights_1, new_weight_exact, rtol=0.001))


def potentiation_and_depression():
    p.setup(1)
    runtime = 100
    initial_run = 1000  # to negate any initial conditions

    # STDP parameters
    a_plus = 0.01
    a_minus = 0.01
    tau_plus = 20
    tau_minus = 20
    plastic_delay = 3
    initial_weight = 2.5
    max_weight = 5
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
    post_pop = p.Population(1, p.IF_curr_exp(),  label="post")

    # Create projections
    p.Projection(
        pre_pop, post_pop, p.OneToOneConnector(),
        p.StaticSynapse(weight=5.0, delay=1), receptor_type="excitatory")

    p.Projection(
        extra_pop, post_pop, p.OneToOneConnector(),
        p.StaticSynapse(weight=5.0, delay=1), receptor_type="excitatory")

    syn_plas = p.STDPMechanism(
        timing_dependence=p.SpikePairRule(tau_plus=tau_plus,
                                          tau_minus=tau_minus,
                                          A_plus=a_plus, A_minus=a_minus),
        weight_dependence=p.MultiplicativeWeightDependence(w_min=min_weight,
                                                           w_max=max_weight),
        weight=initial_weight, delay=plastic_delay)

    plastic_synapse = p.Projection(pre_pop, post_pop,
                                   p.OneToOneConnector(),
                                   synapse_type=syn_plas,
                                   receptor_type='excitatory')

    # Record the spikes
    post_pop.record("spikes")

    # Run
    p.run(initial_run + runtime)

    # Get the weights
    weights = plastic_synapse.get('weight', 'list',
                                  with_address=False)

    # Get the spikes
    post_spikes = numpy.array(
        # pylint: disable=no-member
        post_pop.get_data('spikes').segments[0].spiketrains[0].magnitude)

    # End the simulation as all information gathered
    p.end()

    new_weight_exact = calculate_spike_pair_multiplicative_stdp_weight(
        pre_spikes, post_spikes, initial_weight, plastic_delay, min_weight,
        max_weight, a_plus, a_minus, tau_plus, tau_minus)

    print("Pre neuron spikes at: {}".format(pre_spikes))
    print("Post-neuron spikes at: {}".format(post_spikes))
    target_spikes = [1014,  1032, 1053]
    assert(all(s1 == s2
               for s1, s2 in zip(list(post_spikes), target_spikes)))
    print("New weight exact: {}".format(new_weight_exact))
    print("New weight SpiNNaker: {}".format(weights))

    assert(numpy.allclose(weights, new_weight_exact, rtol=0.001))


class TestSTDPPairMultiplicative(BaseTestCase):

    def test_potentiation_and_depression(self):
        self.runsafe(potentiation_and_depression)

    def test_post_spike_same_time(self):
        self.runsafe(post_spike_same_time)


if __name__ == '__main__':
    post_spike_same_time()
