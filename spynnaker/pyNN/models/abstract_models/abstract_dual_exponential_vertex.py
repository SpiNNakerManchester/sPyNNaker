from spynnaker.pyNN.utilities import constants
import numpy
from abc import ABCMeta
from six import add_metaclass

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
        spec.switchWriteFocus(
            region=constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS)
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Synapse Parameters for {%d} Neurons:\n"
                     .format(self._atoms))

        decay_ex = numpy.exp(float(-self._machine_time_step)
                             / (1000.0 * self._tau_syn_E))
        init_ex = (self._tau_syn_E * (1 - decay_ex)
                                   * (1000.0 / self._machine_time_step))
        decay_ex2 = numpy.exp(float(-self._machine_time_step)
                             / (1000.0 * float(self._tau_syn_E2)))
        init_ex2 = (self._tau_syn_E2 * (1 - decay_ex2)
                                   * (1000.0 / self._machine_time_step))
        decay_in = numpy.exp(float(-self._machine_time_step)
                            / (1000.0 * float(self._tau_syn_I)))
        init_in = (self._tau_syn_I * (1 - decay_in)
                                   * (1000.0 / self._machine_time_step))

        # noinspection PyNoneFunctionAssignment
        rescaled_decay_ex = \
            numpy.multiply(decay_ex, numpy.array([float(pow(2, 32))],
                                                 dtype=float)).astype("uint32")
        # noinspection PyNoneFunctionAssignment
        rescaled_init_ex = \
            numpy.multiply(init_ex, numpy.array([float(pow(2, 32))],
                                                dtype=float)).astype("uint32")

        # noinspection PyNoneFunctionAssignment
        rescaled_decay_ex2 = \
            numpy.multiply(decay_ex2, numpy.array([float(pow(2, 32))],
                                                 dtype=float)).astype("uint32")
        # noinspection PyNoneFunctionAssignment
        rescaled_init_ex2 = \
            numpy.multiply(init_ex2, numpy.array([float(pow(2, 32))],
                                                dtype=float)).astype("uint32")

        # noinspection PyNoneFunctionAssignment
        rescaled_decay_in = \
            numpy.multiply(decay_in, numpy.array([float(pow(2, 32))],
                                                 dtype=float)).astype("uint32")
        # noinspection PyNoneFunctionAssignment
        rescaled_init_in = \
            numpy.multiply(init_in, numpy.array([float(pow(2, 32))],
                                                dtype=float)).astype("uint32")

        for atom in range(0, n_atoms):
            # noinspection PyTypeChecker
            if len(rescaled_decay_ex) > 1:
                spec.write_value(data=rescaled_decay_ex[atom])
            else:
                spec.write_value(data=rescaled_decay_ex[0])
            # noinspection PyTypeChecker
            if len(rescaled_init_ex) > 1:
                spec.write_value(data=rescaled_init_ex[atom])
            else:
                spec.write_value(data=rescaled_init_ex[0])

        for atom in range(0, n_atoms):
            # noinspection PyTypeChecker
            if len(rescaled_decay_ex2) > 1:
                spec.write_value(data=rescaled_decay_ex2[atom])
            else:
                spec.write_value(data=rescaled_decay_ex2[0])
            # noinspection PyTypeChecker
            if len(rescaled_init_ex2) > 1:
                spec.write_value(data=rescaled_init_ex2[atom])
            else:
                spec.write_value(data=rescaled_init_ex2[0])

        for atom in range(0, n_atoms):
            # noinspection PyTypeChecker
            if len(rescaled_decay_in) > 1:
                spec.write_value(data=rescaled_decay_in[atom])
            else:
                spec.write_value(data=rescaled_decay_in[0])
            # noinspection PyTypeChecker
            if len(rescaled_init_in) > 1:
                spec.write_value(data=rescaled_init_in[atom])
            else:
                spec.write_value(data=rescaled_init_in[0])
