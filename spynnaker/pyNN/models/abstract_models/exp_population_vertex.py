from spynnaker.pyNN.models.abstract_models.population_vertex \
    import PopulationVertex
from spynnaker.pyNN.utilities.memory_constants import REGIONS
import numpy

NUM_SYNAPSE_PARAMS = 4  # tau_syn_E and tau_syn_I, and initial multipiers


class ExponentialPopulationVertex(PopulationVertex):
    """
    This represents a population.py with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """
    
    def __init__(self, n_neurons, n_params, binary, constraints=None,
                 label=None, tau_syn_e=5.0, tau_syn_i=5.0):
        
        # Instantiate the parent class
        PopulationVertex.__init__(self, n_neurons=n_neurons, n_params=n_params,
                                  binary=binary, constraints=constraints,
                                  label=label)
        self.tau_syn_e = self.convert_param(tau_syn_e, n_neurons)
        self.tau_syn_i = self.convert_param(tau_syn_i, n_neurons)

    @staticmethod
    def get_n_synapse_type_bits():
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        return 1

    @staticmethod
    def get_synapse_parameter_size(lo_atom, hi_atom):
        """
        Gets the size of the synapse parameters for a range of neurons
        """
        return NUM_SYNAPSE_PARAMS * 4 * ((hi_atom - lo_atom) + 1)
        
    def write_synapse_parameters(self, spec, machine_time_step, subvertex):
        """
        Write vectors of synapse parameters, one per neuron
        There is one parameter for each synapse, which is the decay constant for
        the exponential decay.
        
        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        """
        
        # Set the focus to the memory region 3 (synapse parameters):
        spec.switchWriteFocus(region=REGIONS.SYNAPSE_PARAMS)
        spec.comment("\nWriting Synapse Parameters for "
                     "{} Neurons:\n".format(self.atoms))
        
        decay_ex = numpy.exp(float(-machine_time_step) /
                             (1000.0 * self.tau_syn_e))
        
        init_ex = self.tau_syn_e * (1.0 - decay_ex)

        decay_in = numpy.exp(float(-machine_time_step) /
                             (1000.0 * self.tau_syn_i))
        
        init_in = self.tau_syn_i * (1.0 - decay_in)

        # noinspection PyNoneFunctionAssignment
        rescaled_decay_ex = \
            numpy.multiply(decay_ex, numpy.array([float(pow(2, 32))],
                                                 dtype=float)).astype("uint32")
        # noinspection PyNoneFunctionAssignment
        rescaled_init_ex = \
            numpy.multiply(init_ex, numpy.array([float(pow(2, 32))],
                                                dtype=float)).astype("uint32")
        # noinspection PyNoneFunctionAssignment
        rescaled_decay_in = \
            numpy.multiply(decay_in, numpy.array([float(pow(2, 32))],
                                                 dtype=float)).astype("uint32")
        # noinspection PyNoneFunctionAssignment
        rescaled_init_in = \
            numpy.multiply(init_in, numpy.array([float(pow(2, 32))],
                                                dtype=float)).astype("uint32")

        for atom in range(0, subvertex.n_atoms):
            # noinspection PyTypeChecker
            if len(rescaled_decay_ex) > 1:
                spec.write(data=rescaled_decay_ex[atom])
            else:
                spec.write(data=rescaled_decay_ex[0])
            # noinspection PyTypeChecker
            if len(rescaled_init_ex) > 1:
                spec.write(data=rescaled_init_ex[atom])
            else:
                spec.write(data=rescaled_init_ex[0])
        
        for atom in range(0, subvertex.n_atoms):
            # noinspection PyTypeChecker
            if len(rescaled_decay_in) > 1:
                spec.write(data=rescaled_decay_in[atom])
            else:
                spec.write(data=rescaled_decay_in[0])
            # noinspection PyTypeChecker
            if len(rescaled_init_in) > 1:
                spec.write(data=rescaled_init_in[atom])
            else:
                spec.write(data=rescaled_init_in[0])
