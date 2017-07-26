from spynnaker.pyNN.utilities import utility_calls
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AbstractAdditionalInput

import numpy
from enum import Enum


class _CA2_TYPES(Enum):
    EXP_TAU_CA2 = (1, DataType.S1615)
    I_CA2 = (2, DataType.S1615)
    I_ALPHA = (3, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class AdditionalInputCa2Adaptive(AbstractAdditionalInput):

    def __init__(self, n_neurons, tau_ca2, i_ca2, i_alpha):
        AbstractAdditionalInput.__init__(self)

        self._n_neurons = n_neurons

        self._tau_ca2 = utility_calls.convert_param_to_numpy(
            tau_ca2, n_neurons)
        self._i_ca2 = utility_calls.convert_param_to_numpy(
            i_ca2, n_neurons)
        self._i_alpha = utility_calls.convert_param_to_numpy(
            i_alpha, n_neurons)

    @property
    def tau_ca2(self):
        return self._tau_ca2

    @tau_ca2.setter
    def tau_ca2(self, tau_ca2):
        self._tau_ca2 = utility_calls.convert_param_to_numpy(
            tau_ca2, self._n_neurons)

    @property
    def i_ca2(self):
        return self._i_ca2

    @i_ca2.setter
    def i_ca2(self, i_ca2):
        self._i_ca2 = utility_calls.convert_param_to_numpy(
            i_ca2, self._n_neurons)

    @property
    def i_alpha(self):
        return self._i_alpha

    @i_alpha.setter
    def i_alpha(self, i_alpha):
        self._i_alpha = utility_calls.convert_param_to_numpy(
            i_alpha, self._n_neurons)

    def _exp_tau_ca2(self, machine_time_step):
        return numpy.exp(float(-machine_time_step) /
                         (1000.0 * self._tau_ca2))

    def get_n_parameters(self):
        return 3

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_parameters(self, machine_time_step):
        return [
            NeuronParameter(
                self._exp_tau_ca2(machine_time_step),
                _CA2_TYPES.EXP_TAU_CA2.data_type),
            NeuronParameter(self._i_ca2, _CA2_TYPES.I_CA2.data_type),
            NeuronParameter(self._i_alpha, _CA2_TYPES.I_ALPHA.data_type)
        ]

    def get_parameter_types(self):
        return [item.data_type for item in _CA2_TYPES]

    def set_parameters(self, parameters, vertex_slice):

        # Can ignore anything that isn't a state variable
        self._i_ca_2[vertex_slice.slice] = parameters[1]

    def get_n_cpu_cycles_per_neuron(self):
        return 3

    def get_dtcm_usage_per_neuron_in_bytes(self):
        return 12

    def get_sdram_usage_per_neuron_in_bytes(self):
        return 12
