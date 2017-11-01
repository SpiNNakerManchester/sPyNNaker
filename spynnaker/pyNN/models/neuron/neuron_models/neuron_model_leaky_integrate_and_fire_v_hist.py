from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators import overrides
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .neuron_model_leaky_integrate_and_fire import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.utilities import utility_calls

from data_specification.enums import DataType

import numpy
from enum import Enum

class _LIFVHist_TYPES(Enum):
    V_HIST = (1, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class NeuronModelLeakyIntegrateAndFireVHist(NeuronModelLeakyIntegrateAndFire):

    def __init__(
            self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac, v_hist):

        NeuronModelLeakyIntegrateAndFire.__init__(
            self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac)

        self._v_hist = v_hist
        self._my_units = {'v_hist': 'mV'}


    @overrides(NeuronModelLeakyIntegrateAndFire.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return NeuronModelLeakyIntegrateAndFire.get_n_neural_parameters(self) + 1

    def _tau_refrac_timesteps(self, machine_time_step):
        return numpy.ceil(self._tau_refrac /
                          (machine_time_step / 1000.0))

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_neural_parameters(self, machine_time_step):
        params = NeuronModelLeakyIntegrateAndFire.get_neural_parameters(self)
        params.extend([
            # V history parameter (S1615)
            NeuronParameter(
                self._v_hist,
                _LIFVHist_TYPES.V_HIST.data_type),
        ])
        return params

    @overrides(NeuronModelLeakyIntegrateAndFire.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        if_types = NeuronModelLeakyIntegrateAndFire.get_neural_parameter_types(self)
        if_types.extend([item.data_type for item in _LIFVHist_TYPES])
        return if_types

    def get_n_cpu_cycles_per_neuron(self):
        # A guess - 20 for the reset procedure
        return NeuronModelLeakyIntegrateAndFire.get_n_cpu_cycles_per_neuron(self) + 20

    @overrides(NeuronModelLeakyIntegrateAndFire.get_units)
    def get_units(self, variable):
        if variable in self._my_units:
            return self._my_units[variable]
        else:
            return NeuronModelLeakyIntegrateAndFire.get_units(variable)
