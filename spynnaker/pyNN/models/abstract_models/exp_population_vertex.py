'''
Created on 1 Apr 2014

@author: zzalsar4
'''
from pacman103.front.common.population_vertex import PopulationVertex, REGIONS

import math
import numpy

NUM_SYNAPSE_PARAMS = 4 # tau_syn_E and tau_syn_I, and initial multipiers

class ExponentialPopulationVertex(PopulationVertex):
    """
    This represents a population.py with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """
    
    def __init__( self, n_neurons, n_params, binary, constraints = None, 
            label = None, tau_syn_E = 5.0, tau_syn_I = 5.0):
        
        # Instantiate the parent class
        super(ExponentialPopulationVertex, self).__init__(
            n_neurons = n_neurons,
            n_params = n_params,
            binary = binary,
            constraints = constraints,
            label = label
        )
        self.tau_syn_E = self.convert_param(tau_syn_E, n_neurons)
        self.tau_syn_I = self.convert_param(tau_syn_I, n_neurons)

    def get_n_synapse_type_bits(self):
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        return 1
    
    def getSynapseParameterSize(self, lo_atom, hi_atom):
        """
        Gets the size of the synapse parameters for a range of neurons
        """
        return NUM_SYNAPSE_PARAMS * 4 * ((hi_atom - lo_atom) + 1)
        
    def writeSynapseParameters(self, spec, machineTimeStep, subvertex ):
        """
        Write vectors of synapse parameters, one per neuron
        There is one parameter for each synapse, which is the decay constant for
        the exponential decay.
        
        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        """
        
        # Set the focus to the memory region 3 (synapse parameters):
        spec.switchWriteFocus(region = REGIONS.SYNAPSE_PARAMS)
        spec.comment("\nWriting Synapse Parameters for "
                     "{} Neurons:\n".format(self.atoms))
        
        decay_ex = numpy.exp(float(-machineTimeStep) 
                / (1000.0 * self.tau_syn_E))
        
        init_ex = self.tau_syn_E * (1.0 - decay_ex) 

        decay_in = numpy.exp(float(-machineTimeStep)
                / (1000.0 * self.tau_syn_I))
        
        init_in = self.tau_syn_I * (1.0 - decay_in)
        
        rescaled_decay_ex = numpy.multiply(decay_ex,
            numpy.array([float(pow(2, 32))], dtype=float)).astype("uint32")
        rescaled_init_ex = numpy.multiply(init_ex,
            numpy.array([float(pow(2, 32))], dtype=float)).astype("uint32")
        rescaled_decay_in = numpy.multiply(decay_in,
            numpy.array([float(pow(2, 32))], dtype=float)).astype("uint32")
        rescaled_init_in = numpy.multiply(init_in,
            numpy.array([float(pow(2, 32))], dtype=float)).astype("uint32")
        

        for atom in range(0, subvertex.n_atoms):
            if len(rescaled_decay_ex) > 1:
                spec.write(data=rescaled_decay_ex[atom])
            else:
                spec.write(data=rescaled_decay_ex[0])
            
            if len(rescaled_init_ex) > 1:
                spec.write(data=rescaled_init_ex[atom])
            else:
                spec.write(data=rescaled_init_ex[0])
        
        for atom in range(0, subvertex.n_atoms):
            if len(rescaled_decay_in) > 1:
                spec.write(data=rescaled_decay_in[atom])
            else:
                spec.write(data=rescaled_decay_in[0])
            
            if len(rescaled_init_in) > 1:
                spec.write(data=rescaled_init_in[atom])
            else:
                spec.write(data=rescaled_init_in[0])
