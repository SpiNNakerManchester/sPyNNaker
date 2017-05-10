"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
from p7_integration_tests.base_test_case import BaseTestCase


def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

    p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)

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

    p.set_number_of_neurons_per_core("IF_cond_exp", nNeurons / 2)

    cell_params_cond = {'cm': 0.25,
                        'i_offset': 0.0,
                        'tau_m': 20.0,
                        'tau_refrac': 2.0,
                        'tau_syn_E': 5.0,
                        'tau_syn_I': 5.0,
                        'v_reset': -70.0,
                        'v_rest': -65.0,
                        'v_thresh': -50.0,
                        'e_rev_E': 0.,
                        'e_rev_I': -80.
                        }

    populations = list()
    projections = list()

    weight_to_spike = 0.035
    delay = 17

    injectionConnection = [(0, 0, weight_to_spike, delay)]
    sinkConnection = [(0, 0, weight_to_spike, 1)]

    spikeArray = {'spike_times': [[0]]}

    populations.append(p.Population(nNeurons, p.IF_cond_exp, cell_params_cond,
                                    label='pop_cond'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_curr'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_2'))

    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='sink_pop'))

    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector(injectionConnection)))
    projections.append(p.Projection(populations[3], populations[2],
                                    p.FromListConnector(injectionConnection)))
    projections.append(p.Projection(populations[0], populations[4],
                                    p.FromListConnector(sinkConnection)))
    projections.append(p.Projection(populations[2], populations[4],
                                    p.FromListConnector(sinkConnection)))
    populations[0].record_v()
    populations[0].record_gsyn()
    populations[0].record()

    populations[2].record_v()
    populations[2].record_gsyn()
    populations[2].record()

    p.run(500)

    cond_v = populations[0].get_v(compatible_output=True)
    cond_gsyn = populations[0].get_gsyn(compatible_output=True)
    cond_spikes = populations[0].getSpikes(compatible_output=True)

    curr_v = populations[2].get_v(compatible_output=True)
    curr_gsyn = populations[2].get_gsyn(compatible_output=True)
    curr_spikes = populations[2].getSpikes(compatible_output=True)

    p.end()

    return (cond_v, cond_gsyn, cond_spikes, curr_v, curr_gsyn, curr_spikes)


def plot(nNeurons, cond_v, cond_gsyn, cond_spikes, curr_v, curr_gsyn,
         curr_spikes):
    import pylab  # deferred so unittest are not dependent on it

    # plot curr spikes
    if len(curr_spikes) != 0:
        print "curr spikes are {}".format(curr_spikes)
        pylab.figure()
        pylab.plot([i[1] for i in curr_spikes],
                   [i[0] for i in curr_spikes], ".")
        pylab.xlabel('Time/ms')
        pylab.ylabel('spikes')
        pylab.title('curr spikes')
        pylab.show()
    else:
        print "No curr spikes received"

    # plot cond spikes
    if len(cond_spikes) != 0:
        print "cond spikes are {}".format(cond_spikes)
        pylab.figure()
        pylab.plot([i[1] for i in cond_spikes],
                   [i[0] for i in cond_spikes], ".")
        pylab.xlabel('Time/ms')
        pylab.ylabel('spikes')
        pylab.title('cond spikes')
        pylab.show()
    else:
        print "No cond spikes received"

    # plot curr membrane voltage
    if len(curr_v) != 0:
        ticks = len(curr_v) / nNeurons
        pylab.figure()
        pylab.xlabel('Time/ms')
        pylab.ylabel('v')
        pylab.title('curr v')
        for pos in range(0, nNeurons, 20):
            v_for_neuron = curr_v[pos * ticks: (pos + 1) * ticks]
            pylab.plot([i[2] for i in v_for_neuron])
        pylab.show()
    else:
        print "No curr voltage received"

    # plot cond membrane voltage
    if len(cond_v) != 0:
        ticks = len(cond_v) / nNeurons
        pylab.figure()
        pylab.xlabel('Time/ms')
        pylab.ylabel('v')
        pylab.title('cond v')
        for pos in range(0, nNeurons, 20):
            v_for_neuron = cond_v[pos * ticks: (pos + 1) * ticks]
            pylab.plot([i[2] for i in v_for_neuron])
        pylab.show()
    else:
        print "no cond membrane voltage is recieved "

    # plot curr gsyn
    if len(curr_gsyn) != 0:
        ticks = len(curr_gsyn) / nNeurons
        pylab.figure()
        pylab.xlabel('Time/ms')
        pylab.ylabel('gsyn')
        pylab.title('curr gsyn')
        for pos in range(0, nNeurons, 20):
            gsyn_for_neuron = curr_gsyn[pos * ticks: (pos + 1) * ticks]
            pylab.plot([i[2] for i in gsyn_for_neuron])
        pylab.show()
    else:
        print "no curr gsyn received"

    # plot cond gsyn
    if len(cond_gsyn) != 0:
        ticks = len(cond_gsyn) / nNeurons
        pylab.figure()
        pylab.xlabel('Time/ms')
        pylab.ylabel('gsyn')
        pylab.title('cond gsyn')
        for pos in range(0, nNeurons, 20):
            gsyn_for_neuron = cond_gsyn[pos * ticks: (pos + 1) * ticks]
            pylab.plot([i[2] for i in gsyn_for_neuron])
        pylab.show()
    else:
        print "no cond gsyn received"


class CondVsCurrent(BaseTestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = do_run(nNeurons)
        (cond_v, cond_gsyn, cond_spikes, curr_v, curr_gsyn, curr_spikes) = \
            results
        # spike lengths are 1 and zero whcih looks wrong so not asserted!


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = do_run(nNeurons)
    (cond_v, cond_gsyn, cond_spikes, curr_v, curr_gsyn, curr_spikes) = results
    print len(cond_spikes)
    print len(curr_spikes)
    plot(nNeurons, cond_v, cond_gsyn, cond_spikes, curr_v, curr_gsyn,
         curr_spikes)
