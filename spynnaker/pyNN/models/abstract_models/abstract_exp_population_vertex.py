from spynnaker.pyNN.utilities.constants import POPULATION_BASED_REGIONS
from spynnaker.pyNN.utilities import utility_calls
import numpy
from abc import ABCMeta
from six import add_metaclass

NUM_SYNAPSE_PARAMS = 4  # tau_syn_E and tau_syn_I, and initial multipiers

@add_metaclass(ABCMeta)
class AbstractExponentialPopulationVertex(object):
    """
    This represents a pynn_population.py with two exponentially decaying synapses,
    one for excitatory connections and one for inhibitory connections
    """

    def __init__(self, n_neurons, machine_time_step,
                 tau_syn_e=5.0, tau_syn_i=5.0):

        self._tau_syn_e = utility_calls.convert_param_to_numpy(tau_syn_e,
                                                               n_neurons)
        self._tau_syn_i = utility_calls.convert_param_to_numpy(tau_syn_i,
                                                               n_neurons)
        self._machine_time_step = machine_time_step

    @staticmethod
    def get_synapse_parameter_size(vertex_slice):
        """
        Gets the size of the synapse parameters for a range of neurons
        """
        return NUM_SYNAPSE_PARAMS * 4 * \
               ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)

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
        There is one parameter for each synapse, which is the decay constant for
        the exponential decay.

        Exponential decay factor calculated as:
        p11_XXX = exp(-h/tau_syn_XXX)
        where h is the internal time step in milliseconds (passed in a uSec).
        """

        # Set the focus to the memory region 3 (synapse parameters):
        spec.switch_write_focus(
            region=POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value)

        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spec.comment("\nWriting Synapse Parameters for "
                     "{} Neurons:\n".format(n_atoms))

        decay_ex = numpy.exp(float(-self._machine_time_step) /
                             (1000.0 * self._tau_syn_e))

        init_ex = (self._tau_syn_e * (1 - decay_ex)
                                   * (1000.0 / self._machine_time_step))

        decay_in = numpy.exp(float(-self._machine_time_step) /
                             (1000.0 * self._tau_syn_i))

        init_in = (self._tau_syn_i * (1 - decay_in)
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
            if len(rescaled_decay_in) > 1:
                spec.write_value(data=rescaled_decay_in[atom])
            else:
                spec.write_value(data=rescaled_decay_in[0])
            # noinspection PyTypeChecker
            if len(rescaled_init_in) > 1:
                spec.write_value(data=rescaled_init_in[atom])
            else:
                spec.write_value(data=rescaled_init_in[0])
