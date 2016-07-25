
"""
Synfirechain-like example
"""
from pyNN.random import RandomDistribution
import spynnaker.pyNN as p
from spinn_front_end_common.utilities import exceptions


def run():
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    nNeurons = 200  # number of neurons in each population
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
    
    populations = list()
    population_views = list()
    assemblies = list()
    
    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                       label='pop_1'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                       label='inputSpikes_1'))
    
    neuron_filter_1 = []
    for x in range(20, 50):
        neuron_filter_1.append(x)
    
    neuron_filter_2 = []
    for x in range(120, 150):
        neuron_filter_2.append(x)
    
    
    population_views.append(p.PopulationView(
        populations[0], neuron_filter_1, "pop_view_1"))
    population_views.append(p.PopulationView(
        populations[0], neuron_filter_2, "pop_view_2"))
    
    assemblies.append(p.Assembly(population_views, "assembly views"))
    assemblies.append(p.Assembly(populations[0], "assembly pop"))
    assemblies.append(p.Assembly(populations, "assembly pops"))

    index = 0
    for atom in populations[0]:
        internal_index = populations[0].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    index = 0
    for atom in populations[1]:
        internal_index = populations[1].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    cell = populations[0][4]
    internal_index = populations[0].id_to_index(cell)
    if internal_index != 4:
        raise AssertionError("Not working")

    index = 0
    for atom in population_views[0]:
        internal_index = population_views[0].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    index = 0
    for atom in population_views[1]:
        internal_index = population_views[1].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    cell = population_views[0][4]
    internal_index = population_views[0].id_to_index(cell)
    if internal_index != 4:
        raise AssertionError("Not working")

    index = 0
    for atom in assemblies[0]:
        internal_index = assemblies[0].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    cell = assemblies[0][4]
    internal_index = assemblies[0].id_to_index(cell)
    if internal_index != 4:
        raise AssertionError("Not working")

    index = 0
    for atom in assemblies[1]:
        internal_index = assemblies[1].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    index = 0
    for atom in assemblies[2]:
        internal_index = assemblies[2].id_to_index(atom)
        if index != internal_index:
            raise AssertionError("Not working")
        index += 1

    p.end()

if __name__ == '__main__':
    run()
