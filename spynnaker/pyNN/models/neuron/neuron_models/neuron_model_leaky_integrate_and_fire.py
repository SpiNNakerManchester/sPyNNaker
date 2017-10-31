from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators import overrides
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .neuron_model_leaky_integrate import NeuronModelLeakyIntegrate
from spinn_utilities.ranged.ranged_list import RangedList

from data_specification.enums import DataType

import numpy
from enum import Enum


class _LIF_TYPES(Enum):
    REFRACT_COUNT = (1, DataType.INT32)
    V_RESET = (2, DataType.S1615)
    TAU_REFRACT = (3, DataType.INT32)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class NeuronModelLeakyIntegrateAndFire(NeuronModelLeakyIntegrate):

    def __init__(
            self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac):
        NeuronModelLeakyIntegrate.__init__(
            self, n_neurons, v_init, v_rest, tau_m, cm, i_offset)
        a_list = RangedList(size=n_neurons, default=v_reset)
        self._data.add_list(key="v_reset", a_list=a_list)
        a_list = RangedList(size=n_neurons, default=tau_refrac)
        self._data.add_list(key="tau_refrac", a_list=a_list)
        a_list = RangedList(size=n_neurons, default=0)
        self._data.add_list(key="countdown_to_refactory_period", a_list=a_list)

        self._my_units = {'v_reset': 'mV', 'tau_refac': 'ms'}

    @property
    def v_reset(self):
        return self._data.get_list("v_reset")

    @v_reset.setter
    def v_reset(self, v_reset):
        self._data.set_value("v_reset", v_reset)

    @property
    def tau_refrac(self):
        return self._data.get_list("tau_refrac")

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self._data.set_value("tau_refrac", tau_refrac)

    @overrides(NeuronModelLeakyIntegrate.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return NeuronModelLeakyIntegrate.get_n_neural_parameters(self) + 3

    def _tau_refrac_timesteps(self, machine_time_step):
        operation = lambda x: numpy.ceil(x / (machine_time_step / 1000.0))
        return self._data.get_list("tau_refrac").\
            apply_operation(operation=operation)

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_neural_parameters(self, machine_time_step):
        params = NeuronModelLeakyIntegrate.get_neural_parameters(self)
        params.extend([

            # count down to end of next refractory period [timesteps]
            # int32_t  refract_timer;
            NeuronParameter(
                self._data.get_list("countdown_to_refactory_period"),
                _LIF_TYPES.REFRACT_COUNT.data_type),

            # post-spike reset membrane voltage [mV]
            # REAL     V_reset;
            NeuronParameter(self._data.get_list("v_reset"),
                            _LIF_TYPES.V_RESET.data_type),

            # refractory time of neuron [timesteps]
            # int32_t  T_refract;
            NeuronParameter(
                self._tau_refrac_timesteps(machine_time_step),
                _LIF_TYPES.TAU_REFRACT.data_type)
        ])
        return params

    @overrides(NeuronModelLeakyIntegrate.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        if_types = NeuronModelLeakyIntegrate.get_neural_parameter_types(self)
        if_types.extend([item.data_type for item in _LIF_TYPES])
        return if_types

    def get_n_cpu_cycles_per_neuron(self):

        # A guess - 20 for the reset procedure
        return NeuronModelLeakyIntegrate.get_n_cpu_cycles_per_neuron(self) + 20

    @overrides(NeuronModelLeakyIntegrate.get_units)
    def get_units(self, variable):
        if variable in self._my_units:
            return self._my_units[variable]
        else:
            return NeuronModelLeakyIntegrate.get_units(variable)
