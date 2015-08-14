from spynnaker.pyNN.models.components.synapse_shape_components.\
    abstract_exp_component import \
    AbstractExpComponent
from spynnaker.pyNN.models.components.synapse_shape_components.\
    abstract_synapse_shape_component import \
    AbstractSynapseShapeComponent
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import hashlib

# tau_syn_E, tau_syn_E2 and tau_syn_I and initializers
NUM_SYNAPSE_PARAMS = 6


@add_metaclass(ABCMeta)
class DualExponentialComponent(AbstractSynapseShapeComponent,
                               AbstractExpComponent):
    """
    This represents a population with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """
    # noinspection PyPep8Naming
    def __init__(self, n_keys, machine_time_step, tau_syn_E=5.0,
                 tau_syn_E2=5.0, tau_syn_I=5.0):
        AbstractSynapseShapeComponent.__init__(self)
        AbstractExpComponent.__init__(self)

        self._tau_syn_E = utility_calls.convert_param_to_numpy(tau_syn_E,
                                                               n_keys)
        self._tau_syn_E2 = utility_calls.convert_param_to_numpy(tau_syn_E2,
                                                                n_keys)
        self._tau_syn_I = utility_calls.convert_param_to_numpy(tau_syn_I,
                                                               n_keys)
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

    def get_n_synapse_parameters_per_synapse_type(self):
        """

        :return:
        """

        # There are 2 synapse parameters per synapse type (tau_syn and initial)
        return 2

    def get_n_synapse_types(self):
        """

        :return:
        """

        # There are 3 synapse types (2 excitatory and 1 inhibitory)
        return 3

    def write_synapse_parameters(self, spec, subvertex, vertex_slice):
        """
        Write vectors of synapse parameters, one per neuron
        There is one parameter for each synapse, which is the decay constant
        for the exponential decay.

        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        :param spec:
        :param subvertex:
        :param vertex_slice:
        :return: None
        """

        utility_calls.unused(subvertex)

        # Set the focus to the memory region 3 (synapse parameters):
        spec.switch_write_focus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)
        spec.comment("\nWriting Synapse Parameters for {} Neurons:\n"
                     .format(self._atoms))

        # Write exponential synapse parameters
        self._write_exp_synapse_param(self._tau_syn_E, self._machine_time_step,
                                      vertex_slice, spec)
        self._write_exp_synapse_param(self._tau_syn_E2, self._machine_time_step,
                                      vertex_slice, spec)
        self._write_exp_synapse_param(self._tau_syn_I, self._machine_time_step,
                                      vertex_slice, spec)

    def get_synapse_shape_magic_number(self):
        """
        override from AbstractSynapseShapeComponent
        :return:
        """
        return [hashlib.md5(
            "synapse_types_duel_excitatory_exponential_impl").hexdigest()[:8]]