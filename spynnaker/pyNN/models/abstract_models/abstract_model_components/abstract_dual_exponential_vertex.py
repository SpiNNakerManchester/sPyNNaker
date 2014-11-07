from spynnaker.pyNN.utilities import constants
import math
from abc import ABCMeta
from six import add_metaclass

NUM_SYNAPSE_PARAMS = 3  # tau_syn_E, tau_syn_E2 and tau_syn_I


@add_metaclass(ABCMeta)
class AbstractDualExponentialVertex(object):
    """
    This represents a population with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """
    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, tau_syn_E=5.0,
                 tau_syn_E2=5.0, tau_syn_I=5.0):

        # Instantiate the parent class
        self._tau_syn_E = tau_syn_E
        self._tau_syn_E2 = tau_syn_E2
        self._tau_syn_I = tau_syn_I
        self._machine_time_step = machine_time_step
        self._atoms = n_neurons

    @staticmethod
    def get_synapse_targets():
        """
        Gets the supported names of the synapse targets
        """
        return 'excitatory', 'excitatory2', 'inhibitory'

    @staticmethod
    def get_synapse_id(target_name):
        """
        Returns the numeric identifier of a synapse, given its name.  This
        is used by the neuron models.
        """
        if target_name == "excitatory":
            return 0
        elif target_name == "excitatory2":
            return 1
        elif target_name == "inhibitory":
            return 2
        return None

    @staticmethod
    def get_n_synapse_type_bits():
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        return 2

    @staticmethod
    def get_synapse_parameter_size(vertex_slice):
        """
        Gets the size of the synapse parameters for a range of neurons
        """
        return NUM_SYNAPSE_PARAMS * 4 * ((vertex_slice.hi_atom -
                                          vertex_slice.lo_atom) + 1)

    def write_synapse_parameters(self, spec, subvertex):
        """
        Write vectors of synapse parameters, one per neuron
        There is one parameter for each synapse, which is the decay constant for
        the exponential decay.

        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        """

        # Set the focus to the memory region 3 (synapse parameters):
        spec.switchWriteFocus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS)
        spec.comment("\nWriting Synapse Parameters for {%d} Neurons:\n"
                     .format(self._atoms))
        decay_ex = math.exp(-float(self._machine_time_step)
                            / (1000.0 * float(self._tau_syn_E)))
        decay_ex2 = math.exp(-float(self._machine_time_step)
                             / (1000.0 * float(self._tau_syn_E2)))
        decay_in = math.exp(-float(self._machine_time_step)
                            / (1000.0 * float(self._tau_syn_I)))

        rescaled_decay_ex = int(decay_ex * pow(2, 32))
        rescaled_decay_ex2 = int(decay_ex2 * pow(2, 32))
        rescaled_decay_in = int(decay_in * pow(2, 32))

        spec.write(data=rescaled_decay_ex, repeats=subvertex.n_atoms)
        spec.write(data=rescaled_decay_ex2, repeats=subvertex.n_atoms)
        spec.write(data=rescaled_decay_in, repeats=subvertex.n_atoms)
