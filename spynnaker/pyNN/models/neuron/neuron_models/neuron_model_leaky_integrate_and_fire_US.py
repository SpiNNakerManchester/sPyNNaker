from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators import overrides
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .neuron_model_leaky_integrate_and_fire import NeuronModelLeakyIntegrateAndFire

from data_specification.enums import DataType

import numpy
from enum import Enum

V_COMPARTMENT1 = "V_compartment1"
C_COMPARTMENT1 = "C_compartment1"

class _LIF_US_TYPES(Enum):
    V_COMPARTMENT = (1, DataType.S1615)
    C_COMPARTMENT = (2, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type

class NeuronModelLeakyIntegrateAndFireUS(NeuronModelLeakyIntegrateAndFire):
    def __init__(self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac, V_compartment1, C_compartment1):

        NeuronModelLeakyIntegrateAndFire.__init__(self, n_neurons, v_init,
            v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        self._data[V_COMPARTMENT1] = V_compartment1
        self._data[C_COMPARTMENT1] = C_compartment1

        self._my_units = {'V_compartment1': 'mV', 'C_compartment1': 'nF'}

    @property
    def V_compartment1(self):
        return self._data['V_compartment1']

    @V_compartment1.setter
    def V_compartment1(self, V_compartment1):
        self._data.set_value(key=V_COMPARTMENT1, value=V_compartment1)

    @property
    def C_compartment1(self):
        return self._data['C_compartment1']

    @C_compartment1.setter
    def C_compartment1(self, C_compartment1):
        self._data.set_value(key=C_COMPARTMENT1, value=C_compartment1)

    @overrides(NeuronModelLeakyIntegrateAndFire.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return NeuronModelLeakyIntegrateAndFire.get_n_neural_parameters(self) + 2

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_neural_parameters(self, machine_time_step):
        params = NeuronModelLeakyIntegrateAndFire.get_neural_parameters(self)
        params.extend([
            NeuronParameter(self._data[V_COMPARTMENT1],
                            _LIF_US_TYPES.V_COMPARTMENT.data_type),
            NeuronParameter(self._data[C_COMPARTMENT1],
                            _LIF_US_TYPES.C_COMPARTMENT.data_type),
        ])
        return params

    @overrides(NeuronModelLeakyIntegrateAndFire.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        lif_US_types = NeuronModelLeakyIntegrateAndFire.get_neural_parameter_types(self)
        lif_US_types.extend([item.data_type for item in _LIF_US_TYPES])
        return lif_US_types

    def get_n_cpu_cycles_per_neuron(self):
        return NeuronModelLeakyIntegrateAndFire.get_n_cpu_cycles_per_neuron(self) + 20

    @overrides(NeuronModelLeakyIntegrateAndFire.get_units)
    def get_units(self, variable):
        if variable in self._my_units:
            return self._my_units[variable]
        else:
            return NeuronModelLeakyIntegrateAndFire.get_units(variable)
