from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AbstractAdditionalInput
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary
import numpy
from enum import Enum

# Pacemaker Current
I_H = "I_H"
G_H = "g_H"
E_H = "E_H"
M_H = "m_H"
M_INF_H = "m_inf_H"
E_TO_T_ON_TAU_M_H = "e_to_t_on_tau_m_H"
# Calcium Current
I_T = "I_T"
G_T = "g_T"
E_T = "E_T"
M_T = "m_T"
M_INF_T = "m_inf_T"
E_TO_T_ON_TAU_M_T = "e_to_t_on_tau_m_T"
H_T = "h_T"
H_INF_T = "h_inf_T"
E_TO_T_ON_TAU_H_T = "e_to_t_on_tau_h_T"
# Sodium Current
I_NAP = "I_NaP"
G_NAP = "g_NaP"
E_NAP = "E_NaP"
M_INF_NAP = "m_inf_NaP"
# Potassium Current
I_DK = "I_DK"
G_DK = "g_DK"
E_DK = "E_DK"
M_INF_DK = "m_inf_DK"
E_TO_T_ON_TAU_M_DK = "e_to_t_on_tau_m_DK"
D = "D"
D_INFINITY = "D_infinity"
# Voltage Clamp
V_CLAMP = "v_clamp"
S_CLAMP = "s_clamp"
T_CLAMP = "t_clamp"
# simulation. Maybe more efficient to get them from other parts of the software?
DT = "dt"

UNITS = {
    # Pacemaker Current
    I_H: "mA",
    G_H: "uS",
    E_H: "mV",
    M_H: "",
    M_INF_H: "",
    E_TO_T_ON_TAU_M_H: "ms",
    # Calcium Current
    I_T: "mA",
    G_T: "uS",
    E_T: "mV",
    M_T: "",
    M_INF_T: "",
    E_TO_T_ON_TAU_M_T: "ms",
    H_T: "",
    H_INF_T: "",
    E_TO_T_ON_TAU_H_T: "ms",
    # Sodium Current
    I_NAP: "mA",
    G_NAP: "uS",
    E_NAP: "mV",
    M_INF_NAP: "",
    # Potassium Current
    I_DK: "mA",
    G_DK: "uS",
    E_DK: "mV",
    M_INF_DK: "",
    E_TO_T_ON_TAU_M_DK: "ms",
    D: "",
    D_INFINITY: "",
    # Voltage Clamp
    V_CLAMP: "mV",
    S_CLAMP: "mV",
    T_CLAMP: "mV",
    # simulation. Maybe more efficient to get them from other parts of the software?
    DT: "ms"
    }

# class _INTRINSIC_CURRENTS_TYPES(Enum):
#     # Pacemaker
#     I_H = (1, DataType.S1615)
#     g_H = (2, DataType.S1615)
#     E_H = (3, DataType.S1615)
#     m_H = (4, DataType.S1615)
#     m_inf_H = (5, DataType.S1615)
#     e_to_t_on_tau_m_H = (6, DataType.S1615)
#     # Calcium
#     I_T = (7, DataType.S1615)
#     g_T = (8, DataType.S1615)
#     E_T = (9, DataType.S1615)
#     m_T = (10, DataType.S1615)
#     m_inf_T = (11, DataType.S1615)
#     e_to_t_on_tau_m_T = (12, DataType.S1615)
#     h_T = (13, DataType.S1615)
#     h_inf_T = (14, DataType.S1615)
#     e_to_t_on_tau_h_T = (15, DataType.S1615)
#     # Sodium
#     I_NaP = (16, DataType.S1615)
#     g_NaP = (17, DataType.S1615)
#     E_NaP = (18, DataType.S1615)
#     m_inf_NaP = (19, DataType.S1615)
#     # Potassium
#     I_DK = (20, DataType.S1615)
#     g_DK = (21, DataType.S1615)
#     E_DK = (22, DataType.S1615)
#     m_inf_DK = (23, DataType.S1615)
#     e_to_t_on_tau_m_DK = (24, DataType.S1615)
#     D = (25, DataType.S1615)
#     D_infinity = (26, DataType.S1615)
#     # Voltage Clamp
#     v_clamp = (27, DataType.S1615)
#     s_clamp = (28, DataType.UINT32)
#     t_clamp = (29, DataType.UINT32)
#     dt = (30, DataType.S1615)
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


class AdditionalInputHTIntrinsicCurrents(AbstractAdditionalInput):
    __slots__ = [
        "_v_init",
        "_I_H",
        "_g_H",
        "_E_H",
        "_m_H",
        "_m_inf_H",
        "_e_to_t_on_tau_m_H",
        "_I_T",
        "_g_T",
        "_E_T",
        "_m_T",
        "_m_inf_T",
        "_e_to_t_on_tau_m_T",
        "_h_T",
        "_h_inf_T",
        "_e_to_t_on_tau_h_T",
        "_I_NaP",
        "_g_NaP",
        "_E_NaP",
        "_m_inf_NaP",
        "_I_DK",
        "_g_DK",
        "_E_DK",
        "_m_inf_DK",
        "_e_to_t_on_tau_m_DK",
        "_D",
        "_D_infinity",
        "_v_clamp",
        "_s_clamp",
        "_t_clamp",
        "_dt"
        ]

    def __init__(self,
                 # Pacemaker
                 I_H,
                 g_H,
                 E_H,
                 m_H,
                 m_inf_H,
                 e_to_t_on_tau_m_H,
                 # Calcium
                 I_T,
                 g_T,
                 E_T,
                 m_T,
                 m_inf_T,
                 e_to_t_on_tau_m_T,
                 h_T,
                 h_inf_T,
                 e_to_t_on_tau_h_T,
                 # Sodium
                 I_NaP,
                 g_NaP,
                 E_NaP,
                 m_inf_NaP,
                 # Potassium
                 I_DK,
                 g_DK,
                 E_DK,
                 m_inf_DK,
                 e_to_t_on_tau_m_DK,
                 D,
                 D_infinity,
                 # Voltage Clamp
                 v_clamp, s_clamp, t_clamp,

                 # Other
                 dt
                 ):

        super(AdditionalInputHTIntrinsicCurrents, self).__init__(
           [
            DataType.S1615, #I_H = (1, )
            DataType.S1615, #g_H = (2, )
            DataType.S1615, #E_H = (3, )
            DataType.S1615, #m_H = (4, )
            DataType.S1615, #m_inf_H = (5, )
            DataType.S1615, #e_to_t_on_tau_m_H = (6, )
            # Calcium
            DataType.S1615, #I_T = (7, )
            DataType.S1615, #g_T = (8, )
            DataType.S1615, #E_T = (9, )
            DataType.S1615, #m_T = (10, )
            DataType.S1615, #m_inf_T = (11, )
            DataType.S1615, #e_to_t_on_tau_m_T = (12, )
            DataType.S1615, #h_T = (13, )
            DataType.S1615, #h_inf_T = (14, )
            DataType.S1615, #e_to_t_on_tau_h_T = (15, )
            # Sodium
            DataType.S1615, #I_NaP = (16, )
            DataType.S1615, #g_NaP = (17, )
            DataType.S1615, #E_NaP = (18, )
            DataType.S1615, #m_inf_NaP = (19, )
            # Potassium
            DataType.S1615, #I_DK = (20, )
            DataType.S1615, #g_DK = (21, )
            DataType.S1615, #E_DK = (22, )
            DataType.S1615, #m_inf_DK = (23, )
            DataType.S1615, #e_to_t_on_tau_m_DK = (24, )
            DataType.S1615, #D = (25, )
            DataType.S1615, #D_infinity = (26, )
            # Voltage Clamp
            DataType.S1615, #v_clamp = (27, )
            DataType.UINT32, #s_clamp = (28, )
            DataType.UINT32, #t_clamp = (29, )
            DataType.S1615 #dt = (30, )
            ])

        self._v_init = -69.9

        self._I_H = I_H
        self._g_H = g_H
        self._E_H = E_H
        self._m_inf_H = 1 / (1 + numpy.exp((self._v_init +75) / 5.5) )      #m_inf_H
        self._m_H = self._m_inf_H # initialise to m_inf_h
        self._e_to_t_on_tau_m_H = \
            numpy.exp(-0.1 * # this is dt - needs substituing for variable
                      (numpy.exp(-14.59 - 0.086 * self._v_init) +
                             numpy.exp(-1.87 + 0.0701 * self._v_init)))


        self._I_T = I_T
        self._g_T = g_T
        self._E_T = E_T
        self._m_inf_T = 1 / (1 + numpy.exp(-(self._v_init + 59) * 0.16129)) #m_inf_T
        self._m_T = self._m_inf_T # initialise to m_inf_T
        self._e_to_t_on_tau_m_T = numpy.exp(
          -0.1 / (# this is dt
                  0.13 + (0.22 / numpy.exp(-0.05988 * (self._v_init + 132))             #// 1/16.7=0.05988023952
                             + numpy.exp(0.054945 * (self._v_init + 16.8)))))
        self._h_inf_T = 1 / (1 + numpy.exp((self._v_init + 83.0) * 0.25)) # h_inf_T
        self._h_T = self._h_inf_T
        self._e_to_t_on_tau_h_T = numpy.exp(
           -0.1 / ( # This is dt - substitute for variable
                    8.2 +
                    (56.6 + 0.27 * numpy.exp((self._v_init + 115.2) * 0.2)) /            #// 1/5.0=0.2
                    (1.0 + numpy.exp((self._v_init + 86.0) * 0.3125))))


        self._I_NaP = I_NaP
        self._g_NaP = g_NaP
        self._E_NaP = E_NaP
        self._m_inf_NaP = 1 / (1 + numpy.exp(-(self._v_init + 55.7) * 0.12987))

        self._I_DK = I_DK
        self._g_DK = g_DK
        self._E_DK = E_DK


        self._e_to_t_on_tau_m_DK = numpy.exp(-0.1/1250)
        self._D_infinity = 0.001 + ((1250.0 * 0.025)
                                       / (1.0 + numpy.exp(-(self._v_init - -10.0) * 0.2)))
        self._D = self._D_infinity
        self._m_inf_DK = 1 / (1 + (0.25 / self._D)**3)
        self._v_clamp = v_clamp
        self._s_clamp = s_clamp
        self._t_clamp = t_clamp
        self._dt = dt

    @overrides(AbstractAdditionalInput.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 300 * n_neurons

    @overrides(AbstractAdditionalInput.add_parameters)
    def add_parameters(self, parameters):
        parameters[G_H] = self._g_H
        parameters[E_H] = self._E_H
        parameters[M_H] = self._m_H
        parameters[M_INF_H] = self._m_inf_H
        parameters[E_TO_T_ON_TAU_M_H] = self._e_to_t_on_tau_m_H
        parameters[G_T] = self._g_T
        parameters[E_T] = self._E_T
        parameters[M_T] = self._m_T
        parameters[M_INF_T] = self._m_inf_T
        parameters[E_TO_T_ON_TAU_M_T] = self._e_to_t_on_tau_m_T
        parameters[H_T] = self._h_T
        parameters[H_INF_T] = self._h_inf_T
        parameters[E_TO_T_ON_TAU_H_T] = self._e_to_t_on_tau_h_T
        parameters[G_NAP] = self._g_NaP
        parameters[E_NAP] = self._E_NaP
        parameters[M_INF_NAP] = self._m_inf_NaP
        parameters[G_DK] = self._g_DK
        parameters[E_DK] = self._E_DK
        parameters[M_INF_DK] = self._m_inf_DK
        parameters[E_TO_T_ON_TAU_M_DK] = self._e_to_t_on_tau_m_DK
        parameters[D] = self._D
        parameters[D_INFINITY] = self._D_infinity
        parameters[V_CLAMP] = self._v_clamp
        parameters[S_CLAMP] = self._s_clamp
        parameters[T_CLAMP] = self._t_clamp
        parameters[DT] = self._dt


    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[I_H] = self._I_H
        state_variables[I_T] = self._I_T
        state_variables[I_NAP] = self._I_NaP
        state_variables[I_DK] = self._I_DK

    @overrides(AbstractAdditionalInput.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractAdditionalInput.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractAdditionalInput.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [
                state_variables[I_H],
                parameters[G_H],
                parameters[E_H],
                parameters[M_H],
                parameters[M_INF_H],
                parameters[E_TO_T_ON_TAU_M_H],

                state_variables[I_T],
                parameters[G_T],
                parameters[E_T],
                parameters[M_T], # state variable
                parameters[M_INF_T], # state variable
                parameters[E_TO_T_ON_TAU_M_T], # state variable
                parameters[H_T], # state variable
                parameters[H_INF_T], # state variable
                parameters[E_TO_T_ON_TAU_H_T], # state variable

                state_variables[I_NAP],
                parameters[G_NAP],
                parameters[E_NAP],
                parameters[M_INF_NAP], # state variable

                state_variables[I_DK],
                parameters[G_DK],
                parameters[E_DK],
                parameters[M_INF_DK], # state variable
                parameters[E_TO_T_ON_TAU_M_DK], # state variable
                parameters[D], # state variable
                parameters[D_INFINITY], # state variable

                parameters[V_CLAMP],
                parameters[S_CLAMP],
                parameters[T_CLAMP],

                ts
                ]

    @overrides(AbstractAdditionalInput.update_values)
    def update_values(self, values, parameters, state_variables):
        (_I_H,
        _g_H,
        _E_H,
        _m_H,
        _m_inf_H,
        _e_to_t_on_tau_m_H,
        _I_T,
        _g_T,
        _E_T,
        _m_T,
        _m_inf_T,
        _e_to_t_on_tau_m_T,
        _h_T,
        _h_inf_T,
        _e_to_t_on_tau_h_T,
        _I_NaP,
        _g_NaP,
        _E_NaP,
        _m_inf_NaP,
        _I_DK,
        _g_DK,
        _E_DK,
        _m_inf_DK,
        _e_to_t_on_tau_m_DK,
        _D,
        _D_infinity,
        _v_clamp,
        _s_clamp,
        _t_clamp,
        _dt) = values

        state_variables[I_H] = _I_H
        state_variables[I_T] = _I_T
        state_variables[I_DK] = _I_DK
        state_variables[I_NAP] = _I_NaP

        # Need to add additional state variables for m and h, D_cube, etc,
        # such that state is maintained across restarts

    @property
    def I_H(self):
        return self._I_H
    @ I_H.setter
    def I_H(self, new_I_H):
        self._I_H = new_I_H

    @property
    def g_H(self):
        return self._g_H
    @ g_H.setter
    def g_H(self, new_g_H):
        self._g_H = new_g_H

    @property
    def E_H(self):
        return self._E_H
    @ E_H.setter
    def E_H(self, new_E_H):
        self._E_H = new_E_H

    @property
    def m_H(self):
        return self._m_H
    @ m_H.setter
    def m_H(self, new_m_H):
        self._m_H = new_m_H

    @property
    def m_inf_H(self):
        return self._m_inf_H
    @ m_inf_H.setter
    def m_inf_H(self, new_m_inf_H):
        self._m_inf_H = new_m_inf_H

    @property
    def e_to_t_on_tau_m_H(self):
        return self._e_to_t_on_tau_m_H
    @ e_to_t_on_tau_m_H.setter
    def e_to_t_on_tau_m_H(self, new_e_to_t_on_tau_m_H):
        self._e_to_t_on_tau_m_H = new_e_to_t_on_tau_m_H

    @property
    def I_T(self):
        return self._I_T
    @ I_T.setter
    def I_T(self, new_I_T):
        self._I_T = new_I_T

    @property
    def g_T(self):
        return self._g_T
    @ g_T.setter
    def g_T(self, new_g_T):
        self._g_T = new_g_T

    @property
    def E_T(self):
        return self._E_T
    @ E_T.setter
    def E_T(self, new_E_T):
        self._E_T = new_E_T

    @property
    def m_T(self):
        return self._m_T
    @ m_T.setter
    def m_T(self, new_m_T):
        self._m_T = new_m_T

    @property
    def m_inf_T(self):
        return self._m_inf_T
    @ m_inf_T.setter
    def m_inf_T(self, new_m_inf_T):
        self._m_inf_T = new_m_inf_T

    @property
    def e_to_t_on_tau_m_T(self):
        return self._e_to_t_on_tau_m_T
    @ e_to_t_on_tau_m_T.setter
    def e_to_t_on_tau_m_T(self, new_e_to_t_on_tau_m_T):
        self._e_to_t_on_tau_m_T = new_e_to_t_on_tau_m_T

    @property
    def h_T(self):
        return self._h_T
    @ h_T.setter
    def h_T(self, new_h_T):
        self._h_T = new_h_T

    @property
    def h_inf_T(self):
        return self._h_inf_T
    @ h_inf_T.setter
    def h_inf_T(self, new_h_inf_T):
        self._h_inf_T = new_h_inf_T

    @property
    def e_to_t_on_tau_h_T(self):
        return self._e_to_t_on_tau_h_T
    @ e_to_t_on_tau_h_T.setter
    def e_to_t_on_tau_h_T(self, new_e_to_t_on_tau_h_T):
        self._e_to_t_on_tau_h_T = new_e_to_t_on_tau_h_T

    @property
    def I_NaP(self):
        return self._I_NaP
    @ I_NaP.setter
    def I_NaP(self, new_I_NaP):
        self._I_NaP = new_I_NaP

    @property
    def g_NaP(self):
        return self._g_NaP
    @ g_NaP.setter
    def g_NaP(self, new_g_NaP):
        self._g_NaP = new_g_NaP

    @property
    def E_NaP(self):
        return self._E_NaP
    @E_NaP.setter
    def E_NaP(self, new_E_NaP):
        self._E_NaP = new_E_NaP

    @property
    def m_inf_NaP(self):
        return self._m_inf_NaP
    @ m_inf_NaP.setter
    def m_inf_NaP(self, new_m_inf_NaP):
        self._m_inf_NaP = new_m_inf_NaP

    @property
    def I_DK(self):
        return self._I_DK
    @ I_DK.setter
    def I_DK(self, new_I_DK):
        self._I_DK = new_I_DK

    @property
    def g_DK(self):
        return self._g_DK
    @ g_DK.setter
    def g_DK(self, new_g_DK):
        self._g_DK = new_g_DK

    @property
    def E_DK(self):
        return self._E_DK
    @ E_DK.setter
    def E_DK(self, new_E_DK):
        self._E_DK = new_E_DK

    @property
    def m_inf_DK(self):
        return self._m_inf_DK
    @ m_inf_DK.setter
    def m_inf_DK(self, new_m_inf_DK):
        self._m_inf_DK = new_m_inf_DK

    @property
    def e_to_t_on_tau_m_DK(self):
        return self._e_to_t_on_tau_m_DK
    @ e_to_t_on_tau_m_DK.setter
    def e_to_t_on_tau_m_DK(self, new_e_to_t_on_tau_m_DK):
        self._e_to_t_on_tau_m_DK = new_e_to_t_on_tau_m_DK

    @property
    def D(self):
        return self._D
    @ D.setter
    def D(self, new_D):
        self._D = new_D

    @property
    def D_infinity(self):
        return self._D_infinity
    @ D_infinity.setter
    def D_infinity(self, new_D_infinity):
        self._D_infinity = new_D_infinity

    @property
    def e_to_t_on_tau_h_DK(self):
        return self._e_to_t_on_tau_h_DK
    @e_to_t_on_tau_h_DK.setter
    def e_to_t_on_tau_h_DK(self, new_e_to_t_on_tau_h_DK):
        self._e_to_t_on_tau_h_DK = new_e_to_t_on_tau_h_DK

    @property
    def v_clamp(self):
        return self._v_clamp
    @ v_clamp.setter
    def v_clamp(self, new_v_clamp):
        self._v_clamp = new_v_clamp

    @property
    def s_clamp(self):
        return self._s_clamp
    @ s_clamp.setter
    def s_clamp(self, new_s_clamp):
        self._s_clamp = new_s_clamp

    @property
    def t_clamp(self):
        return self._t_clamp
    @ t_clamp.setter
    def t_clamp(self, new_t_clamp):
        self._t_clamp = new_t_clamp

    @property
    def dt(self):
        return self._dt
    @ dt.setter
    def dt(self, new_dt):
        self._dt = new_dt










#
#     def get_n_parameters(self):
#         return 30
#
#     @inject_items({"machine_time_step": "MachineTimeStep"})
#     def get_parameters(self, machine_time_step):
#         # pylint: disable=arguments-differ
#         return [NeuronParameter(self._data[I_H],_INTRINSIC_CURRENTS_TYPES.I_H.data_type),
#                NeuronParameter(self._data[G_H],_INTRINSIC_CURRENTS_TYPES.g_H.data_type),
#                NeuronParameter(self._data[E_H],_INTRINSIC_CURRENTS_TYPES.E_H.data_type),
#                NeuronParameter(self._data[M_H],_INTRINSIC_CURRENTS_TYPES.m_H.data_type),
#                NeuronParameter(self._data[M_INF_H],_INTRINSIC_CURRENTS_TYPES.m_inf_H.data_type),
#                NeuronParameter(self._data[E_TO_T_ON_TAU_M_H],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_m_H.data_type),
#                NeuronParameter(self._data[I_T],_INTRINSIC_CURRENTS_TYPES.I_T.data_type),
#                NeuronParameter(self._data[G_T],_INTRINSIC_CURRENTS_TYPES.g_T.data_type),
#                NeuronParameter(self._data[E_T],_INTRINSIC_CURRENTS_TYPES.E_T.data_type),
#                NeuronParameter(self._data[M_T],_INTRINSIC_CURRENTS_TYPES.m_T.data_type),
#                NeuronParameter(self._data[M_INF_T],_INTRINSIC_CURRENTS_TYPES.m_inf_T.data_type),
#                NeuronParameter(self._data[E_TO_T_ON_TAU_M_T],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_m_T.data_type),
#                NeuronParameter(self._data[H_T],_INTRINSIC_CURRENTS_TYPES.h_T.data_type),
#                NeuronParameter(self._data[H_INF_T],_INTRINSIC_CURRENTS_TYPES.h_inf_T.data_type),
#                NeuronParameter(self._data[E_TO_T_ON_TAU_H_T],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_h_T.data_type),
#                NeuronParameter(self._data[I_NAP],_INTRINSIC_CURRENTS_TYPES.I_NaP.data_type),
#                NeuronParameter(self._data[G_NAP],_INTRINSIC_CURRENTS_TYPES.g_NaP.data_type),
#                NeuronParameter(self._data[E_NAP],_INTRINSIC_CURRENTS_TYPES.E_NaP.data_type),
#                NeuronParameter(self._data[M_INF_NAP],_INTRINSIC_CURRENTS_TYPES.m_inf_NaP.data_type),
#                NeuronParameter(self._data[I_DK],_INTRINSIC_CURRENTS_TYPES.I_DK.data_type),
#                NeuronParameter(self._data[G_DK],_INTRINSIC_CURRENTS_TYPES.g_DK.data_type),
#                NeuronParameter(self._data[E_DK],_INTRINSIC_CURRENTS_TYPES.E_DK.data_type),
#                NeuronParameter(self._data[M_INF_DK],_INTRINSIC_CURRENTS_TYPES.m_inf_DK.data_type),
#                NeuronParameter(self._data[E_TO_T_ON_TAU_M_DK],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_m_DK.data_type),
#                NeuronParameter(self._data[D],_INTRINSIC_CURRENTS_TYPES.D.data_type),
#                NeuronParameter(self._data[D_INFINITY],_INTRINSIC_CURRENTS_TYPES.D_infinity.data_type),
#                NeuronParameter(self._data[V_CLAMP],_INTRINSIC_CURRENTS_TYPES.v_clamp.data_type),
#                NeuronParameter(self._data[S_CLAMP],_INTRINSIC_CURRENTS_TYPES.s_clamp.data_type),
#                NeuronParameter(self._data[T_CLAMP],_INTRINSIC_CURRENTS_TYPES.t_clamp.data_type),
#                NeuronParameter(self._data[DT],_INTRINSIC_CURRENTS_TYPES.dt.data_type)
#                ]
#
#     def get_parameter_types(self):
#         return [item.data_type for item in _INTRINSIC_CURRENTS_TYPES]
#
#     def set_parameters(self, parameters, vertex_slice):
#         pass
#
#     def get_n_cpu_cycles_per_neuron(self):
#         return 100

