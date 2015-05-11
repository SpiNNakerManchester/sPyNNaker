"""
ExponentialComponent
"""
from spynnaker.pyNN.models.components.synapse_shape_components.\
    abstract_exp_component import AbstractExpComponent
from spynnaker.pyNN.models.components.synapse_shape_components.\
    abstract_synapse_shape_component import AbstractSynapseShapeComponent
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities import constants

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

# tau_syn_E and tau_syn_I, and initial multipiers
NUM_SYNAPSE_PARAMS = 4


@add_metaclass(ABCMeta)
class ExponentialComponent(AbstractSynapseShapeComponent, AbstractExpComponent):
    """
    This represents a pynn_population.py with two exponentially decaying
    synapses, one for excitatory connections and one for inhibitory connections
    """
    # noinspection PyPep8Naming
    def __init__(self, n_neurons, machine_time_step,
                 tau_syn_E=5.0, tau_syn_I=5.0):

        AbstractSynapseShapeComponent.__init__(self)
        AbstractExpComponent.__init__(self)
        self._tau_syn_E = utility_calls.convert_param_to_numpy(tau_syn_E,
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
    def tau_syn_I(self):
        return self._tau_syn_I

    # noinspection PyPep8Naming
    @tau_syn_I.setter
    def tau_syn_I(self, new_value):
        self._tau_syn_I = new_value

    @abstractmethod
    def is_exp_vertex(self):
        """helper method for is_instance
        :return:
        """

    def get_n_synapse_parameters_per_synapse_type(self):

        # There are 2 synapse parameters per synapse type (tau_syn and initial)
        return 2

    def get_n_synapse_types(self):

        # There are 2 synapse types (excitatory and inhibitory)
        return 2

    @staticmethod
    def get_n_synapse_type_bits():
        """
        Return the number of bits used to identify the synapse in the synaptic
        row
        """
        return 1

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

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Synapse Parameters for "
                     "{} Neurons:\n".format(n_atoms))

        # Write exponenential synapse parameters
        self._write_exp_synapse_param(self._tau_syn_E, self._machine_time_step,
                                      vertex_slice, spec)
        self._write_exp_synapse_param(self._tau_syn_I, self._machine_time_step,
                                      vertex_slice, spec)

    def get_synapse_shape_magic_number(self):
        """
        override from AbstractSynapseShapeComponent
        :return:
        """
        return constants.SYNAPSE_SHAPING_EXP_MAGIC_NUMBER