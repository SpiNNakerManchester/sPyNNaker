#!/usr/bin/python
"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.plot_utils as plot_utils
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest


def do_run(nNeurons, neurons_per_core):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", neurons_per_core)

    nPopulations = 62
    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 1.5
    delay = 5

    for i in range(0, nPopulations):
        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif,
                                        label='pop_' + str(i)))
        print "++++++++++++++++"
        print "Added population %s" % (i)
        print "o-o-o-o-o-o-o-o-"
    for i in range(0, nPopulations):
        projections.append(p.Projection(populations[i],
                                        populations[(i + 1) % nPopulations],
                                        p.OneToOneConnector(weight_to_spike,
                                                            delay),
                                        label="Projection from pop {} to pop "
                                              "{}".format(i, (i + 1) %
                                                          nPopulations)))
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++"
        print "Added projection from population %s to population %s" \
              % (i, (i + 1) % nPopulations)
        print "----------------------------------------------------"

    from pprint import pprint as pp
    pp(projections)
    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))
    projections.append(p.Projection(populations[-1], populations[0],
                                    p.AllToAllConnector(weight_to_spike,
                                                        delay)))

    for i in range(0, nPopulations):
        populations[i].record_v()
        populations[i].record_gsyn()
        populations[i].record()

    p.run(1500)

    v = None
    gsyn = None
    spikes = None
    ''''
    weights = projections[0].getWeights()
    delays = projections[0].getDelays()
    '''

    v = populations[0].get_v(compatible_output=True)
    gsyn = populations[0].get_gsyn(compatible_output=True)
    spikes = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v, gsyn, spikes)


class MwhPopulationSynfire(BaseTestCase):
    def test_run_heavy(self):
        try:
            nNeurons = 200  # number of neurons in each population
            neurons_per_core = 256
            (v, gsyn, spikes) = do_run(nNeurons, neurons_per_core)
            self.assertLess(580, len(spikes))
            self.assertGreater(620, len(spikes))
        except SpinnmanTimeoutException as ex:
            raise SkipTest(ex)

    def test_run_light(self):
        nNeurons = 200  # number of neurons in each population
        neurons_per_core = 50
        (v, gsyn, spikes) = do_run(nNeurons, neurons_per_core)
        self.assertLess(580, len(spikes))
        self.assertGreater(620, len(spikes))


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    neurons_per_core = 256
    (v, gsyn, spikes) = do_run(nNeurons, neurons_per_core)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")
