"""
tests fixed probabilities
"""
import spynnaker.pyNN as p
import os
import unittest
import numpy


class TestPrintSpikes(unittest.TestCase):
    """
    tests the printing of get spikes given a simulation
    """

    def test_fixed_probabilityies(self):

        pop_size = 1024

        rng_weights = p.NumpyRNG(seed=369121518)

        min_weight = 0.1
        max_weight = 5.0
        weight_scale_ex_in = 0.25
        weight_dependence_n = \
            p.RandomDistribution(
                distribution='uniform',
                parameters=[1.0 + min_weight, 1.0 + max_weight],
                rng=rng_weights)
        weight_dependence_e = \
            p.RandomDistribution(distribution='uniform',
                                 parameters=[min_weight, max_weight],
                                 rng=rng_weights)
        weight_dependence_i = \
            p.RandomDistribution(distribution='uniform',
                                 parameters=[-(max_weight * weight_scale_ex_in),
                                             -min_weight],
                                 rng=rng_weights)

        runtime = 1000.0
        stim_start = 0.0
        stim_rate = 10
        pops_to_observe = ['mapped_pop_1']

        # Simulation Setup
        p.setup(timestep=1.0, min_delay=1.0, max_delay=11.0)

        # Neural Parameters
        tau_m = 24.0    # (ms)
        cm = 1
        v_rest = -65.0     # (mV)
        v_thresh = -45.0     # (mV)
        v_reset = -65.0     # (mV)
        t_refrac = 3.0       # (ms) (clamped at v_reset)
        tau_syn_exc = 3.0
        tau_syn_inh = tau_syn_exc * 3

        # cell_params will be passed to the constructor of the Population Object

        cell_params = {
            'tau_m': tau_m,
            'cm': cm,
            'v_init': v_reset,
            'v_rest': v_rest,
            'v_reset': v_reset,
            'v_thresh': v_thresh,
            'tau_syn_E': tau_syn_exc,
            'tau_syn_I': tau_syn_inh,
            'tau_refrac': t_refrac,
            'i_offset': 0
        }

        observed_pop_list = []
        inputs = p.Population(
            pop_size, p.SpikeSourcePoisson, {'duration': runtime,
                                             'start': stim_start,
                                             'rate': stim_rate},
            label="inputs")
        if 'inputs' in pops_to_observe:
            inputs.record()
            observed_pop_list.append(inputs)

        mapped_pop_1 = p.Population(pop_size, p.IF_curr_exp, cell_params,
                                    label="mapped_pop_1")
        if 'mapped_pop_1' in pops_to_observe:
            mapped_pop_1.record()
            observed_pop_list.append(mapped_pop_1)

        pop_inhibit = p.Population(pop_size, p.IF_curr_exp, cell_params,
                                   label="pop_inhibit")
        if 'pop_inhibit' in pops_to_observe:
            pop_inhibit.record()
            observed_pop_list.append(pop_inhibit)

        mapped_pop_2 = p.Population(pop_size, p.IF_curr_exp, cell_params,
                                    label="mapped_pop_2")

        if 'mapped_pop_2' in pops_to_observe:
            mapped_pop_2.record()
            observed_pop_list.append(mapped_pop_2)

        p.Projection(inputs, mapped_pop_1,
                     p.OneToOneConnector(
                         weights=weight_dependence_n, delays=1.0),
                     target='excitatory')

        p.Projection(mapped_pop_1, pop_inhibit,
                     p.OneToOneConnector(
                         weights=weight_dependence_e,
                         delays=1.0), target='excitatory')

        p.NativeRNG(123456)

        p.Projection(pop_inhibit, mapped_pop_2,
                     p.FixedProbabilityConnector(
                         p_connect=0.5, allow_self_connections=True,
                         weights=weight_dependence_i, delays=4.0),
                     target='inhibitory')

        p.Projection(mapped_pop_1, mapped_pop_2,
                     p.FixedProbabilityConnector(
                         p_connect=0.5, allow_self_connections=True,
                         weights=weight_dependence_e, delays=4.0),
                     target='excitatory')

        p.run(runtime)

        current_file_path = os.path.dirname(os.path.abspath(__file__))

        for pop in observed_pop_list:
            data = numpy.asarray(pop.getSpikes())
            current_pop_file_path = os.path.join(current_file_path,
                                                 "{}.data".format(pop.label))
            pre_recorded_data = p.utility_calls.read_spikes_from_file(
                current_pop_file_path, 0, pop_size, 0, runtime)
            for spike_element, read_element in zip(data, pre_recorded_data):
                    self.assertEqual(round(spike_element[0], 1),
                                     round(read_element[0], 1))
                    self.assertEqual(round(spike_element[1], 1),
                                     round(read_element[1], 1))