from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.utility_models.exp_synapse_param\
    import write_exp_synapse_param
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

NUM_SYNAPSE_PARAMS = 6  # tau_syn_E, tau_syn_E2 and tau_syn_I and initializers


@add_metaclass(ABCMeta)
class AbstractDualExponentialVertex(object):
    """
    This represents a population with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """
    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step, tau_syn_E=5.0,
                 tau_syn_E2=5.0, tau_syn_I=5.0):

        self._tau_syn_E = utility_calls.convert_param_to_numpy(tau_syn_E,
                                                               n_neurons)
        self._tau_syn_E2 = utility_calls.convert_param_to_numpy(tau_syn_E2,
                                                                n_neurons)
        self._tau_syn_I = utility_calls.convert_param_to_numpy(tau_syn_I,
                                                               n_neurons)
        self._machine_time_step = machine_time_step

    # noinspection PyPep8Naming
    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    # noinspection PyPep8Naming
    @tau_syn_E.setter
    def tau_syn_E(self, new_value):
        self._tau_syn_E = new_value

    # noinspection PyPep8Naming
    @property
    def tau_syn_E2(self):
        return self._tau_syn_E2

    # noinspection PyPep8Naming
    @tau_syn_E2.setter
    def tau_syn_E2(self, new_value):
        self._tau_syn_E2 = new_value

    # noinspection PyPep8Naming
    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    # noinspection PyPep8Naming
    @tau_syn_I.setter
    def tau_syn_I(self, new_value):
        self._tau_syn_I = new_value

    @abstractmethod
    def is_duel_exponential_vertex(self):
        """ helper method for is_instance
        """

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

    def write_synapse_parameters(self, spec, subvertex, vertex_slice):
        """
        Write vectors of synapse parameters, one per neuron
        There is one parameter for each synapse, which is the decay constant
        for the exponential decay.

        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        """

        # Set the focus to the memory region 3 (synapse parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        spec.comment("\nWriting Synapse Parameters for {} Neurons:\n"
                     .format(self._atoms))

        # Write exponenential synapse parameters
        write_exp_synapse_param(self._tau_syn_E, self._machine_time_step,
                                vertex_slice, spec)
        write_exp_synapse_param(self._tau_syn_E2, self._machine_time_step,
                                vertex_slice, spec)
        write_exp_synapse_param(self._tau_syn_I, self._machine_time_step,
                                vertex_slice, spec)
