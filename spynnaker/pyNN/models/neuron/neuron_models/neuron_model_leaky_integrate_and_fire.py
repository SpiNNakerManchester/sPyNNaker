from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .neuron_model_leaky_integrate import NeuronModelLeakyIntegrate

from data_specification.enums import DataType

import numpy
from enum import Enum

V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNTDOWN_TO_REFRACTORY_PERIOD = "countdown_to_refactory_period"
_CPU_RESET_CYCLES = 20  # pure guesswork


class _LIF_TYPES(Enum):
    REFRACT_COUNT = (1, DataType.INT32)
    V_RESET = (2, DataType.S1615)
    TAU_REFRACT = (3, DataType.INT32)

    def __new__(cls, value, data_type, doc=""):
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        obj.__doc__ = doc
        return obj

    @property
    def data_type(self):
        return self._data_type


class NeuronModelLeakyIntegrateAndFire(NeuronModelLeakyIntegrate):
    __slots__ = [
        "_my_units"]

    def __init__(
            self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac):
        # pylint: disable=too-many-arguments
        super(NeuronModelLeakyIntegrateAndFire, self).__init__(
            n_neurons, v_init, v_rest, tau_m, cm, i_offset)
        self._data[V_RESET] = v_reset
        self._data[TAU_REFRAC] = tau_refrac
        self._data[COUNTDOWN_TO_REFRACTORY_PERIOD] = 0
        self._my_units = {V_RESET: 'mV', TAU_REFRAC: 'ms'}

    @property
    def v_reset(self):
        return self._data[V_RESET]

    @v_reset.setter
    def v_reset(self, v_reset):
        self._data.set_value(key=V_RESET, value=v_reset)

    @property
    def tau_refrac(self):
        return self._data[TAU_REFRAC]

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self._data.set_value(key=TAU_REFRAC, value=tau_refrac)

    @overrides(NeuronModelLeakyIntegrate.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return super(NeuronModelLeakyIntegrateAndFire,
                     self).get_n_neural_parameters() + 3

    def _tau_refrac_timesteps(self, machine_time_step):
        return self._data[TAU_REFRAC].apply_operation(
            operation=lambda x: numpy.ceil(x / (machine_time_step / 1000.0)))

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_neural_parameters(self, machine_time_step):
        params = super(NeuronModelLeakyIntegrateAndFire,
                       self).get_neural_parameters()
        params.extend([

            # count down to end of next refractory period [timesteps]
            # int32_t  refract_timer;
            NeuronParameter(
                self._data[COUNTDOWN_TO_REFRACTORY_PERIOD],
                _LIF_TYPES.REFRACT_COUNT.data_type),

            # post-spike reset membrane voltage [mV]
            # REAL     V_reset;
            NeuronParameter(self._data[V_RESET],
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
        if_types = super(NeuronModelLeakyIntegrateAndFire,
                         self).get_neural_parameter_types()
        if_types.extend([item.data_type for item in _LIF_TYPES])
        return if_types

    def get_n_cpu_cycles_per_neuron(self):
        # A guess - 20 for the reset procedure
        return super(NeuronModelLeakyIntegrateAndFire,
                     self).get_n_cpu_cycles_per_neuron() + _CPU_RESET_CYCLES

    @overrides(NeuronModelLeakyIntegrate.get_units)
    def get_units(self, variable):
        if variable in self._my_units:
            return self._my_units[variable]
        return super(NeuronModelLeakyIntegrateAndFire,
                     self).get_units(variable)
