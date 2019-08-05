from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from .abstract_neuron_model import AbstractNeuronModel
from data_specification.enums import DataType

import numpy

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"
Z = "z"
A = "a"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms',
    Z: 'N/A',
    A: 'N/A'
}


class NeuronModelLeakyIntegrateAndFireGrazAdaptive(AbstractNeuronModel):
    __slots__ = [
        "_v_init",
        "_v_rest",
        "_tau_m",
        "_cm",
        "_i_offset",
        "_v_reset",
        "_tau_refrac",
        "_z",
        "_a"
        ]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac):
        super(NeuronModelLeakyIntegrateAndFireGrazAdaptive, self).__init__(
            [DataType.S1615,   # v
             DataType.S1615,   # v_rest
             DataType.S1615,   # r_membrane (= tau_m / cm)
             DataType.S1615,   # exp_tc (= e^(-ts / tau_m))
             DataType.S1615,   # i_offset
             DataType.INT32,   # count_refrac
             DataType.S1615,   # v_reset
             DataType.INT32,
             DataType.S1615,   # Z
             DataType.S1615    # A
             ])  # tau_refrac

        if v_init is None:
            v_init = v_rest
        self._v_init = v_init
        self._v_rest = v_rest
        self._tau_m = tau_m
        self._cm = cm
        self._i_offset = i_offset
        self._v_reset = v_reset
        self._tau_refrac = tau_refrac

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self._v_rest
        parameters[TAU_M] = self._tau_m
        parameters[CM] = self._cm
        parameters[I_OFFSET] = self._i_offset
        parameters[V_RESET] = self._v_reset
        parameters[TAU_REFRAC] = self._tau_refrac

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self._v_init
        state_variables[COUNT_REFRAC] = 0
        state_variables[Z] = 0
        state_variables[A] = 0

    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [state_variables[V],
                parameters[V_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET],
                state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0)))),
                state_variables[Z],
                state_variables[A]
                ]

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac, z, a) = values

        # Copy the changed data only
        state_variables[V] = v
        state_variables[COUNT_REFRAC] = count_refrac
        state_variables[Z] = z
        state_variables[A] = a

    @property
    def v_init(self):
        return self._v

    @v_init.setter
    def v_init(self, v_init):
        self._v = v_init

    @property
    def v_rest(self):
        return self._v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self._v_rest = v_rest

    @property
    def tau_m(self):
        return self._tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self._tau_m = tau_m

    @property
    def cm(self):
        return self._cm

    @cm.setter
    def cm(self, cm):
        self._cm = cm

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self._i_offset = i_offset

    @property
    def v_reset(self):
        return self._v_reset

    @v_reset.setter
    def v_reset(self, v_reset):
        self._v_reset = v_reset

    @property
    def tau_refrac(self):
        return self._tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self._tau_refrac = tau_refrac




# V_RESET = "v_reset"
# TAU_REFRAC = "tau_refrac"
# COUNTDOWN_TO_REFRACTORY_PERIOD = "countdown_to_refactory_period"
# _CPU_RESET_CYCLES = 20  # pure guesswork
#
#
# class _LIF_TYPES(Enum):
#     REFRACT_COUNT = (1, DataType.INT32)
#     V_RESET = (2, DataType.S1615)
#     TAU_REFRACT = (3, DataType.INT32)
#     Z = (4, DataType.S1615)
#     A = (5, DataType.S1615)
#
#     def __new__(cls, value, data_type, doc=""):
#         # pylint: disable=protected-access
#         obj = object.__new__(cls)
#         obj._value_ = value
#         obj._data_type = data_type
#         obj.__doc__ = doc
#         return obj
#
#     @property
#     def data_type(self):
#         return self._data_type
#
#
# class NeuronModelLeakyIntegrateAndFireGrazAdaptive(NeuronModelLeakyIntegrate):
#     __slots__ = [
#         "_my_units"]
#
#     def __init__(
#             self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
#             tau_refrac):
#         # pylint: disable=too-many-arguments
#         super(NeuronModelLeakyIntegrateAndFireGrazAdaptive, self).__init__(
#             n_neurons, v_init, v_rest, tau_m, cm, i_offset)
#         self._data[V_RESET] = v_reset
#         self._data[TAU_REFRAC] = tau_refrac
#         self._data[COUNTDOWN_TO_REFRACTORY_PERIOD] = 0
#         self._my_units = {V_RESET: 'mV', TAU_REFRAC: 'ms'}
#
#     @property
#     def v_reset(self):
#         return self._data[V_RESET]
#
#     @v_reset.setter
#     def v_reset(self, v_reset):
#         self._data.set_value(key=V_RESET, value=v_reset)
#
#     @property
#     def tau_refrac(self):
#         return self._data[TAU_REFRAC]
#
#     @tau_refrac.setter
#     def tau_refrac(self, tau_refrac):
#         self._data.set_value(key=TAU_REFRAC, value=tau_refrac)
#
#     @overrides(NeuronModelLeakyIntegrate.get_n_neural_parameters)
#     def get_n_neural_parameters(self):
#         return super(NeuronModelLeakyIntegrateAndFireGrazAdaptive,
#                      self).get_n_neural_parameters() + 5 # added two extra
#
#     def _tau_refrac_timesteps(self, machine_time_step):
#         return self._data[TAU_REFRAC].apply_operation(
#             operation=lambda x: numpy.ceil(x / (machine_time_step / 1000.0)))
#
#     @inject_items({"machine_time_step": "MachineTimeStep"})
#     def get_neural_parameters(self, machine_time_step):
#         params = super(NeuronModelLeakyIntegrateAndFireGrazAdaptive,
#                        self).get_neural_parameters()
#         params.extend([
#
#             # count down to end of next refractory period [timesteps]
#             # int32_t  refract_timer;
#             NeuronParameter(
#                 self._data[COUNTDOWN_TO_REFRACTORY_PERIOD],
#                 _LIF_TYPES.REFRACT_COUNT.data_type),
#
#             # post-spike reset membrane voltage [mV]
#             # REAL     V_reset;
#             NeuronParameter(self._data[V_RESET],
#                             _LIF_TYPES.V_RESET.data_type),
#
#             # refractory time of neuron [timesteps]
#             # int32_t  T_refract;
#             NeuronParameter(
#                 self._tau_refrac_timesteps(machine_time_step),
#                 _LIF_TYPES.TAU_REFRACT.data_type),
#
#             NeuronParameter(
#                 0,
#                 _LIF_TYPES.Z.data_type),
#
#             NeuronParameter(
#                 0,
#                 _LIF_TYPES.A.data_type)
#         ])
#         return params
#
#     @overrides(NeuronModelLeakyIntegrate.get_neural_parameter_types)
#     def get_neural_parameter_types(self):
#         if_types = super(NeuronModelLeakyIntegrateAndFireGrazAdaptive,
#                          self).get_neural_parameter_types()
#         if_types.extend([item.data_type for item in _LIF_TYPES])
#         return if_types
#
#     def get_n_cpu_cycles_per_neuron(self):
#         # A guess - 20 for the reset procedure
#         return super(NeuronModelLeakyIntegrateAndFireGrazAdaptive,
#                      self).get_n_cpu_cycles_per_neuron() + _CPU_RESET_CYCLES
#
#     @overrides(NeuronModelLeakyIntegrate.get_units)
#     def get_units(self, variable):
#         if variable in self._my_units:
#             return self._my_units[variable]
#         return super(NeuronModelLeakyIntegrateAndFire,
#                      self).get_units(variable)
