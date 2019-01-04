from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from .abstract_neuron_model import AbstractNeuronModel
from data_specification.enums import DataType

import numpy
#from objc._properties import attrsetter

V = "v_init"
G_NA = "g_Na"
E_NA = "E_Na"
G_K = "g_K"
E_K = "E_K"
TAU_M = "tau_m"
G_SPIKE = "g_spike"
G_SPIKE_VAR = "g_spike_var"
TAU_SPIKE = "tau_spike"
T_SPIKE = "t_spike"
I_OFFSET = "i_offset"
REF_COUNTER = "refractory_counter"
A = "a"
B = "b"
A_SPIKE = "a_spike"
B_SPIKE = "b_spike"
A_INV = "a_inv"
A_SPIKE_INV = "a_spike_inv"
EXPONENT = "exponent"
EXPONENT_SPIKE = "exponent_spike"

UNITS = {
    V: "mV" ,
    G_NA: "uS",
    E_NA: "mV",
    G_K: "uS",
    E_K: "mV",
    TAU_M: "ms",
    G_SPIKE: "uS",
    G_SPIKE_VAR: "uS",
    TAU_SPIKE: "ms",
    T_SPIKE: "ms",
    I_OFFSET: "nA",
    REF_COUNTER: "ms",
    A: "N/A",
    B: "N/A",
    A_SPIKE: "N/A",
    B_SPIKE: "N/A",
    A_INV: "N/A",
    A_SPIKE_INV: "N/A",
    EXPONENT: "N/A",
    EXPONENT_SPIKE: "N/A"
}


# class _HT_TYPES(Enum):
#     V_INIT = (1, DataType.S1615)
#     G_NA = (2, DataType.S1615)
#     E_NA = (3, DataType.S1615)
#     G_K = (4, DataType.S1615)
#     E_K = (5, DataType.S1615)
#     EXP_TC = (6, DataType.S1615)
#     TAU_M = (7, DataType.S1615)
#     EXP_TC_SPIKE = (8, DataType.S1615)
#     TAU_SPIKE = (9, DataType.S1615)
#     G_SPIKE = (10, DataType.S1615)
#     T_SPIKE = (11, DataType.S1615)
#     I_OFFSET = (12, DataType.S1615)
#     REF_COUNTER = (13, DataType.INT32)
#     A = (14, DataType.S1615)
#     B = (15, DataType.S1615)
#     A_SPIKE = (16, DataType.S1615)
#     B_SPIKE = (17, DataType.S1615)
#     A_INV = (18, DataType.S1615)
#     A_SPIKE_INV = (19, DataType.S1615)
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


class NeuronModelHT(AbstractNeuronModel):
    __slots__ = [
        "_v",
        "_g_Na",
        "_E_rev_Na",
        "_g_K",
        "_E_rev_K",
        "_tau_m",
        "_g_spike_var",
        "_g_spike",
        "_tau_spike",
        "_t_spike",
        "_i_offset",
        "_refractory_counter",
        "_a",
        "_b",
        "_a_spike",
        "_b_spike",
        "_a_inv",
        "_a_spike_inv",
        "_exponent",
        "_exponent_spike"
        ]


    def __init__(
            self,
            v,
            g_Na, E_rev_Na,
            g_K, E_rev_K,
            tau_m,
            g_spike, tau_spike, t_spike,
            i_offset):

        super(NeuronModelHT, self).__init__(
            [                # parameters match c struct
             DataType.S1615, # V_membrane
             DataType.S1615, # g_Na
             DataType.S1615, # E_Na
             DataType.S1615, # g_K
             DataType.S1615, # E_K
             DataType.S1615, # exp_TC
             DataType.S1615, # tau_m
             DataType.S1615, # exp_TC_spike
             DataType.S1615, # tau_spike
             DataType.S1615, # g_spike_var
             DataType.S1615, # g_spike
             DataType.S1615, # t_spike
             DataType.S1615, # I_offset
             DataType.INT32, # ref_counter
             DataType.S1615, # A
             DataType.S1615, # B
             DataType.S1615, # A_SPIKE
             DataType.S1615, # B_SPIKE
             DataType.S1615, # A_INV
             DataType.S1615  # A_SPIKE_INV
             ])

        # pylint: disable=too-many-arguments
        self._v = v,
        self._g_Na = g_Na
        self._E_rev_Na = E_rev_Na
        self._g_K = g_K
        self._E_rev_K = E_rev_K
        self._tau_m = tau_m
        self._g_spike_var = 0
        self._g_spike = g_spike
        self._tau_spike = tau_spike
        self._t_spike = t_spike
        self._i_offset = i_offset
        self._refractory_counter = 0

        # These parameters should be set by lambda functions, but for now
        # expose them to outside world.

        self._a = (self._tau_spike *
                         (self._g_Na + self._g_K))
        self._b = (self._tau_spike *
                         (self._g_Na * self._E_rev_Na +
                         self._g_K * self._E_rev_K))

        self._a_spike = (self._tau_spike *
                               (self._g_Na + self._g_K) +
                               (self._tau_m * self._g_spike))
        self._b_spike = (self._tau_spike *
                               (self._g_Na * self._E_rev_Na +
                               self._g_K * self._E_rev_K) +
                               self._tau_m * self._g_spike
                               * self._E_rev_K)

        # initialise now, and invert with lambda
        self._a_inv = 1/self._a

        # initialise now, and invert with lambda
        self._a_spike_inv = 1/self._a_spike

        self._exponent = (self._a /
                                (self._tau_m * self._tau_spike))

        self._exponent_spike = (self._a_spike /
                                      (self._tau_m *
                                       self._tau_spike))

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[G_NA] = self._g_Na
        parameters[E_NA] = self._E_rev_Na
        parameters[G_K] = self._g_K
        parameters[E_K] = self._E_rev_K
        parameters[TAU_M] = self._tau_m
        parameters[G_SPIKE_VAR] = self._g_spike_var
        parameters[G_SPIKE] = self._g_spike
        parameters[TAU_SPIKE] = self._tau_spike
        parameters[T_SPIKE] = self._t_spike
        parameters[I_OFFSET] = self._i_offset
        parameters[A] = self._a
        parameters[B]= self._b
        parameters[A_SPIKE] = self._a_spike
        parameters[B_SPIKE] = self._b_spike
        parameters[A_INV] = self._a_inv
        parameters[A_SPIKE_INV] = self._a_spike_inv
        parameters[EXPONENT] = self._exponent
        parameters[EXPONENT_SPIKE] = self._exponent_spike

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self._v
        state_variables[REF_COUNTER] = self._refractory_counter
#         state_variables[REF_COUNTER] = 0

    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add lambda functions here to enable heterogeneous parameter setting
        tsfloat = float(ts) / 1000.0
        convert_to_machine_timesteps = lambda x: int(x*1000/ts)
        decay_tau = lambda x: numpy.exp(-tsfloat * x)

        return [
            state_variables[V],
            parameters[G_NA],
            parameters[E_NA],
            parameters[G_K],
            parameters[E_K],
            parameters[EXPONENT].apply_operation(decay_tau),
            parameters[TAU_M],
            parameters[EXPONENT_SPIKE].apply_operation(decay_tau),
            parameters[TAU_SPIKE],
            parameters[G_SPIKE_VAR],
            parameters[G_SPIKE],
            parameters[T_SPIKE].apply_operation(convert_to_machine_timesteps),
            parameters[I_OFFSET],
            state_variables[REF_COUNTER],
            parameters[A],
            parameters[B],
            parameters[A_SPIKE],
            parameters[B_SPIKE],
            parameters[A_INV],
            parameters[A_SPIKE_INV]
            ]


    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        (v, _g_Na, _E_rev_Na, _g_Na, _E_rev_K, _tau_m, _exp_tau_m,
         _exp_tau_spike, _tau_spike, g_spike_var, _g_spike, _t_spike,
         _i_offset, ref_counter, _a, _b, _a_spike, _b_spike, _a_inv,
         _a_spike_inv) = values

        state_variables[V] = v
        state_variables[REF_COUNTER] = ref_counter
#         state_variables[G_SPIKE_VAR] = g_spike_var


    @property
    def v(self):
        return self._v

    @v.setter
    def v(self, v):
        self._v = v

    @property
    def g_Na(self):
        return self._g_Na

    @g_Na.setter
    def g_Na(self, g_Na):
        self._g_Na = g_Na

    @property
    def E_Na(self):
        return self._E_Na

    @E_Na.setter
    def E_Na(self, E_Na):
        self._E_Na = E_Na

    @property
    def g_K(self):
        return self._g_K

    @g_K.setter
    def g_K(self, g_K):
        self._g_K = g_K

    @property
    def E_K(self):
        return self._E_K

    @E_K.setter
    def E_K(self, E_rev_K):
        self._E_K = E_K

    @property
    def tau_m(self):
        return self._tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self._tau_m = tau_m

    @property
    def g_spike_var(self):
        return self._g_spike_var

    @g_spike_var.setter
    def g_spike_var(self, g_spike_var):
        self._g_spike_var = g_spike_var

    @property
    def g_spike(self):
        return self._g_spike

    @g_spike.setter
    def g_spike(self, g_spike):
        self._g_spike = g_spike

    @property
    def tau_spike(self):
        return self._tau_spike

    @tau_spike.setter
    def tau_spike(self, tau_spike):
        self._tau_spike = tau_spike

    @property
    def t_spike(self):
        return self._t_spike

    @t_spike.setter
    def t_spike(self, t_spike):
        self._t_spike = t_spike

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self._i_offset = i_offset

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, a):
        self._a = a

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, b):
        self._b = b

    @property
    def a_spike(self):
        return self._a_spike

    @a_spike.setter
    def a_spike(self, a_spike):
        self._a_spike = a_spike

    @property
    def b_spike(self):
        return self._b_spike

    @b_spike.setter
    def b_spike(self, b_spike):
        self._b_spike = b_spike
    @property
    def a_inv(self):
        return self._a_inv

    @a_inv.setter
    def a_inv(self, a_inv):
        self._a_inv = a_inv

    @property
    def a_spike_inv(self):
        return self._a_spike_inv

    @a_spike_inv.setter
    def a_spike_inv(self, a_spike_inv):
        self._a_spike_inv = a_spike_inv

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, exponent):
        self._exponent = exponent

    @property
    def exponent_spike(self):
        return self._exponent_spike

    @exponent_spike.setter
    def exponent_spike(self, exponent_spike):
        self._exponent_spike = exponent_spike

#     @property
#     def (self):
#         return self._
#
#     @.setter
#     def (self, ):
#         self._ =

# A = "a"
# B = "b"
# A_SPIKE = "a_spike"
# B_SPIKE = "b_spike"
# A_INV = "a_inv"
# A_SPIKE_INV = "a_spike_inv"
# EXPONENT = "exponent"
# EXPONENT_SPIKE = "exponent_spike"
#
#
#         params.extend([
#
#             NeuronParameter(
#                 self._data[V_INIT],
#                 _HT_TYPES.V_INIT.data_type),
#
#             NeuronParameter(
#                 self._data[G_NA],
#                 _HT_TYPES.G_NA.data_type),
#
#             NeuronParameter(
#                 self._data[E_NA],
#                 _HT_TYPES.E_NA.data_type),
#
#             NeuronParameter(
#                 self._data[G_K],
#                 _HT_TYPES.G_K.data_type),
#
#             NeuronParameter(
#                 self._data[E_K],
#                 _HT_TYPES.E_K.data_type),
#
#             # No-spike time constant multiplier
#             NeuronParameter(
#                 self._exp_tc(machine_time_step),
#                 _HT_TYPES.EXP_TC.data_type),
#
#             NeuronParameter(
#                 self._data[TAU_M],
#                 _HT_TYPES.TAU_M.data_type),
#
#             # Including spike multiplier
#             NeuronParameter(
#                 self._exp_tc_spike(machine_time_step),
#                 _HT_TYPES.EXP_TC_SPIKE.data_type),
#
#             NeuronParameter(
#                 self._data[TAU_SPIKE],
#                 _HT_TYPES.TAU_SPIKE.data_type),
#
#             # variable
#             NeuronParameter(
#                 0,
#                 _HT_TYPES.G_SPIKE.data_type),
#
#             # value to switch to
#             NeuronParameter(
#                 self._data[G_SPIKE],
#                 _HT_TYPES.G_SPIKE.data_type),
#
#             NeuronParameter(
#                 self._tau_refrac_timesteps(machine_time_step),
#                 _HT_TYPES.T_SPIKE.data_type),
#
#             NeuronParameter(
#                 self._data[I_OFFSET],
#                 _HT_TYPES.I_OFFSET.data_type),
#
#             NeuronParameter(
#                 0, _HT_TYPES.REF_COUNTER.data_type),
#
#             NeuronParameter(
#                 self._data[A],
#                 _HT_TYPES.A.data_type),
#
#             NeuronParameter(
#                 self._data[B],
#                 _HT_TYPES.B.data_type),
#
#             NeuronParameter(
#                 self._data[A_SPIKE],
#                 _HT_TYPES.A_SPIKE.data_type),
#
#             NeuronParameter(
#                 self._data[B_SPIKE],
#                 _HT_TYPES.B_SPIKE.data_type),
#
#             NeuronParameter(
#                 self._inv_A(),
#                 _HT_TYPES.A_INV.data_type),
#
#             NeuronParameter(
#                 self._inv_A_SPIKE(),
#                 _HT_TYPES.A_SPIKE_INV.data_type)
#         ])
#         return params
