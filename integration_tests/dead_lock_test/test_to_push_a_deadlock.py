#!/usr/bin/python
import spynnaker.pyNN as p
import pylab

if __name__ == '__main__':
    #p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
    p.setup(timestep=1.0, min_delay = 1.0, max_delay = 144.0)
    nNeurons = 100  # number of neurons in each population
    populations = list()
    projections = list()

    weight_to_spike = 2.0
    delay = 3

    injectionConnection = [(0, 0, weight_to_spike, 1)]
    spikeArray = {'spike_times': [0]}

    cell_params_lif = {'cm'        : 0.25, # nF
                         'i_offset'  : 0.0,
                         'tau_m'     : 20.0,
                         'tau_refrac': 2.0,
                         'tau_syn_E' : 5.0,
                         'tau_syn_I' : 5.0,
                         'v_reset'   : -70.0,
                         'v_rest'    : -65.0,
                         'v_thresh'  : -50.0
                         }
    population_index = 0

    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='in_cur_esp1'))
    populations[population_index].set_mapping_constraint({'x':0, 'y':0})
    population_index += 1
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='in_cur_esp2'))
    populations[population_index].set_mapping_constraint({'x':7, 'y':7})
    population_index += 1


    #upwards path

    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_2:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':0, 'y':0})
        projections.append(p.Projection(populations[population_index],
                                        populations[0], p.AllToAllConnector()))
        population_index += 1
    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_2:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':1, 'y':1})
        projections.append(p.Projection(populations[population_index],
                                        populations[0], p.AllToAllConnector()))
        population_index += 1
    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_2:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':2, 'y':2})
        projections.append(p.Projection(populations[population_index],
                                        populations[0], p.AllToAllConnector()))
        population_index += 1
    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_2:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':3, 'y':3})
        projections.append(p.Projection(populations[population_index],
                                        populations[0], p.AllToAllConnector()))
        population_index += 1

    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_1:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':7, 'y':7})
        projections.append(p.Projection(populations[population_index],
                                        populations[1], p.AllToAllConnector()))
        population_index += 1
    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_1:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':6, 'y':6})
        projections.append(p.Projection(populations[population_index],
                                        populations[1], p.AllToAllConnector()))
        population_index += 1
    for processor in range(2, 16):
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
                                        label='inputSpikes_1:{}'.format(processor)))
        populations[population_index].set_mapping_constraint({'x':5, 'y':5})
        projections.append(p.Projection(populations[population_index],
                                        populations[1], p.AllToAllConnector()))
        population_index += 1

    run_time = 100
    print "Running for {} ms".format(run_time)
    p.run(run_time)

    p.end()
