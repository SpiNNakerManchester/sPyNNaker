from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type import \
    AbstractSynapseType
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from pacman.executor.injection_decorator import inject_items

from data_specification.enums.data_type import DataType

import numpy
from enum import Enum


class _EXP_TYPES(Enum):
 
     E_DECAY = (1, DataType.UINT32)
     E_INIT = (2, DataType.UINT32)
     I_DECAY = (3, DataType.UINT32)
     I_INIT = (4, DataType.UINT32)

     def __new__(cls, value, data_type):
         obj = object.__new__(cls)
         obj._value_ = value
         obj._data_type = data_type
         return obj

     @property
     def data_type(self):
         return self._data_type

def get_exponential_decay_and_init(tau, machine_time_step):
    decay = numpy.exp(numpy.divide(-float(machine_time_step),
                                   numpy.multiply(1000.0, tau)))
    init = numpy.multiply(numpy.multiply(tau, numpy.subtract(1.0, decay)),
                          (1000.0 / float(machine_time_step)))
    scale = float(pow(2, 32))
    decay_scaled = numpy.multiply(decay, scale).astype("uint32")
    init_scaled = numpy.multiply(init, scale).astype("uint32")
    return decay_scaled, init_scaled


class ExpSupervision(AbstractSynapseType):

    def __init__(self, n_neurons, tau_syn_E, tau_syn_I):

        AbstractSynapseType.__init__(self)
        self._n_neurons = n_neurons

        # TODO: Store the parameters
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, n_neurons)
        self._tau_syn_I = utility_calls.convert_param_to_numpy(
            tau_syn_I, n_neurons)

    def get_n_synapse_types(self):
        return 4

    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        elif target == "reward":
            return 2
        elif target == "punishment":
            return 3

        return None

    def get_synapse_targets(self):
        return "excitatory", "inhibitory", "reward", "punishment"

    def get_n_synapse_type_parameters(self):
        return 4

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_synapse_type_parameters(self, machine_time_step):
        e_decay, e_init = get_exponential_decay_and_init(
            self._tau_syn_E, machine_time_step)
        i_decay, i_init = get_exponential_decay_and_init(
            self._tau_syn_I, machine_time_step)

        return [
            NeuronParameter(e_decay, DataType.UINT32),
            NeuronParameter(e_init, DataType.UINT32),
            NeuronParameter(i_decay, DataType.UINT32),
            NeuronParameter(i_init, DataType.UINT32)
        ]

    def get_n_cpu_cycles_per_neuron(self):

        # TODO: update to match the number of cycles used by
        # synapse_types_shape_input, synapse_types_add_neuron_input,
        # synapse_types_get_excitatory_input and
        # synapse_types_get_inhibitory_input
        return 100

    def get_synapse_type_parameter_types(self):
        return

    def get_synapse_type_parameter_types(self):
        return [item.data_type for item in _EXP_TYPES] 
