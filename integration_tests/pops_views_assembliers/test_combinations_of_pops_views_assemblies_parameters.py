
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

    pop_atom_mapping = populations[0]._spinnaker.get_pop_atom_mapping()
    view_atom_mapping = populations[0]._spinnaker.get_pop_view_atom_mapping()
    assembly_atom_mapping = \
        populations[0]._spinnaker.get_assembly_atom_mapping()


    atoms = pop_atom_mapping[populations[0]._class][populations[0]]
    param_sweep(populations[0], nNeurons, atoms)

    atoms = view_atom_mapping[population_views[0]]
    param_sweep(population_views[0], len(atoms), atoms)

    atoms = view_atom_mapping[population_views[1]]
    param_sweep(population_views[1], len(atoms), atoms)

    atoms = assembly_atom_mapping[assemblies[0]]
    param_sweep(assemblies[0], len(atoms), atoms)

    p.end()
    
    
def param_sweep(pop, nNeurons, atoms):
    # test one param scalar
    pop.set("cm", 0.26)
    for atom in atoms:
        if atom.get("cm") != 0.26:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    # test multiple params
    pop.set({"cm": 0.27, "tau_m": 21})
    for atom in atoms:
        if atom.get("cm") != 0.27 and atom.get('tau_m') != 21:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    # test list
    elements = list()
    for _ in range(0, nNeurons):
        elements.append(11)
    pop.set("tau_m", elements)
    for atom in atoms:
        if atom.get('tau_m') != 11:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    # test t set
    elements = list()
    for _ in range(0, nNeurons):
        elements.append(14)
    pop.tset("tau_m", elements)
    for atom in atoms:
        if atom.get('tau_m') != 14:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    # test random
    param = RandomDistribution("uniform", parameters=[1, 60])
    pop.set("v_thresh", param)
    for atom in atoms:
        if atom.get('v_thresh') == -50.0:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    # test r set
    param = RandomDistribution("uniform", parameters=[1, 30])
    pop.rset("v_rest", param)
    for atom in atoms:
        if atom.get('v_rest') == -65.0:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    pop.initialize("v", 12345)
    for atom in atoms:
        if atom.get_state_variable('v') != 12345:
            raise AssertionError("Pop view didnt set the atom correctly.")
    
    # test incorrect param setting
    try:
        pop.initialize("v_rest", 12345)
        raise AssertionError("Pop view let init of a neuron parameter.")
    except exceptions.ConfigurationException:
        pass
    
    try:
        pop.set("v", 12345)
        raise AssertionError("Pop view let init of a neuron parameter.")
    except exceptions.ConfigurationException:
        pass
    
    try:
        pop.rset("v", 12345)
        raise AssertionError("Pop view let init of a neuron parameter.")
    except exceptions.ConfigurationException:
        pass
    
    try:
        pop.tset("v", 12345)
        raise AssertionError("Pop view let init of a neuron parameter.")
    except exceptions.ConfigurationException:
        pass


if __name__ == '__main__':
    run()
