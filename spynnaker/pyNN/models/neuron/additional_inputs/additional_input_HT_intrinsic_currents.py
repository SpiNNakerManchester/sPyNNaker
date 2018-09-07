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


class _INTRINSIC_CURRENTS_TYPES(Enum):
    # Pacemaker
    I_H = (1, DataType.S1615)
    g_H = (2, DataType.S1615)
    E_H = (3, DataType.S1615)
    m_H = (4, DataType.S1615)
    m_inf_H = (5, DataType.S1615)
    e_to_t_on_tau_m_H = (6, DataType.S1615)
    # Calcium
    I_T = (7, DataType.S1615)
    g_T = (8, DataType.S1615)
    E_T = (9, DataType.S1615)
    m_T = (10, DataType.S1615)
    m_inf_T = (11, DataType.S1615)
    e_to_t_on_tau_m_T = (12, DataType.S1615)
    h_T = (13, DataType.S1615)
    h_inf_T = (14, DataType.S1615)
    e_to_t_on_tau_h_T = (15, DataType.S1615)
    # Sodium
    I_NaP = (16, DataType.S1615)
    g_NaP = (17, DataType.S1615)
    E_NaP = (18, DataType.S1615)
    m_inf_NaP = (19, DataType.S1615)
    # Potassium
    I_DK = (20, DataType.S1615)
    g_DK = (21, DataType.S1615)
    E_DK = (22, DataType.S1615)
    m_inf_DK = (23, DataType.S1615)
    e_to_t_on_tau_m_DK = (24, DataType.S1615)
    D = (25, DataType.S1615)
    D_infinity = (26, DataType.S1615)
    # Voltage Clamp
    v_clamp = (27, DataType.S1615)
    s_clamp = (28, DataType.UINT32)
    t_clamp = (29, DataType.UINT32)
    dt = (30, DataType.S1615)

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


class AdditionalInputHTIntrinsicCurrents(AbstractAdditionalInput):
    __slots__ = [
        "_data",
        "_n_neurons"
        ]

    def __init__(self,
                 n_neurons,
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
        self._n_neurons = n_neurons
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data['I_H'] = I_H
        self._data['g_H'] = g_H
        self._data['E_H'] = E_H
        self._data['m_H'] = m_H
        self._data['m_inf_H'] = m_inf_H
        self._data['e_to_t_on_tau_m_H'] = e_to_t_on_tau_m_H
        self._data['I_T'] = I_T
        self._data['g_T'] = g_T
        self._data['E_T'] = E_T
        self._data['m_T'] = m_T
        self._data['m_inf_T'] = m_inf_T
        self._data['e_to_t_on_tau_m_T'] = e_to_t_on_tau_m_T
        self._data['h_T'] = h_T
        self._data['h_inf_T'] = h_inf_T
        self._data['e_to_t_on_tau_h_T'] = e_to_t_on_tau_h_T
        self._data['I_NaP'] = I_NaP
        self._data['g_NaP'] = g_NaP
        self._data['E_NaP'] = E_NaP
        self._data['m_inf_NaP'] = m_inf_NaP
        self._data['I_DK'] = I_DK
        self._data['g_DK'] = g_DK
        self._data['E_DK'] = E_DK
        self._data['m_inf_DK'] = m_inf_DK
        self._data['e_to_t_on_tau_m_DK'] = e_to_t_on_tau_m_DK
        self._data['D'] = D
        self._data['D_infinity'] = D_infinity
        self._data['v_clamp'] = v_clamp
        self._data['s_clamp'] = s_clamp
        self._data['t_clamp'] = t_clamp
        self._data['dt'] = dt

    @property
    def I_H(self):
        return self._data[I_H]
    @ I_H.setter
    def I_H(self, new_I_H):
        self._data.set_value(key=I_H, value=new_I_H)

    @property
    def g_H(self):
        return self._data[G_H]
    @ g_H.setter
    def g_H(self, new_g_H):
        self._data.set_value(key=G_H, value=new_g_H)

    @property
    def E_H(self):
        return self._data[E_H]
    @ E_H.setter
    def E_H(self, new_E_H):
        self._data.set_value(key=E_H, value=new_E_H)

    @property
    def m_H(self):
        return self._data[M_H]
    @ m_H.setter
    def m_H(self, new_m_H):
        self._data.set_value(key=M_H, value=new_m_H)

    @property
    def m_inf_H(self):
        return self._data[M_INF_H]
    @ m_inf_H.setter
    def m_inf_H(self, new_m_inf_H):
        self._data.set_value(key=M_INF_H, value=new_m_inf_H)

    @property
    def e_to_t_on_tau_m_H(self):
        return self._data[E_TO_T_ON_TAU_M_H]
    @ e_to_t_on_tau_m_H.setter
    def e_to_t_on_tau_m_H(self, new_e_to_t_on_tau_m_H):
        self._data.set_value(key=E_TO_T_ON_TAU_M_H, value=new_e_to_t_on_tau_m_H)

    @property
    def I_T(self):
        return self._data[I_T]
    @ I_T.setter
    def I_T(self, new_I_T):
        self._data.set_value(key=I_T, value=new_I_T)

    @property
    def g_T(self):
        return self._data[G_T]
    @ g_T.setter
    def g_T(self, new_g_T):
        self._data.set_value(key=G_T, value=new_g_T)

    @property
    def E_T(self):
        return self._data[E_T]
    @ E_T.setter
    def E_T(self, new_E_T):
        self._data.set_value(key=E_T, value=new_E_T)

    @property
    def m_T(self):
        return self._data[M_T]
    @ m_T.setter
    def m_T(self, new_m_T):
        self._data.set_value(key=M_T, value=new_m_T)

    @property
    def m_inf_T(self):
        return self._data[M_INF_T]
    @ m_inf_T.setter
    def m_inf_T(self, new_m_inf_T):
        self._data.set_value(key=M_INF_T, value=new_m_inf_T)

    @property
    def e_to_t_on_tau_m_T(self):
        return self._data[E_TO_T_ON_TAU_M_T]

    @ e_to_t_on_tau_m_T.setter
    def e_to_t_on_tau_m_T(self, new_e_to_t_on_tau_m_T):
        self._data.set_value(key=E_TO_T_ON_TAU_M_T, value=new_e_to_t_on_tau_m_T)

    @property
    def h_T(self):
        return self._data[H_T]

    @ h_T.setter
    def h_T(self, new_h_T):
        self._data.set_value(key=H_T, value=new_h_T)

    @property
    def h_inf_T(self):
        return self._data[H_INF_T]

    @ h_inf_T.setter
    def h_inf_T(self, new_h_inf_T):
        self._data.set_value(key=H_INF_T, value=new_h_inf_T)

    @property
    def e_to_t_on_tau_h_T(self):
        return self._data[E_TO_T_ON_TAU_H_T]

    @ e_to_t_on_tau_h_T.setter
    def e_to_t_on_tau_h_T(self, new_e_to_t_on_tau_h_T):
        self._data.set_value(key=E_TO_T_ON_TAU_H_T, value=new_e_to_t_on_tau_h_T)

    @property
    def I_NaP(self):
        return self._data[I_NAP]

    @ I_NaP.setter
    def I_NaP(self, new_I_NaP):
        self._data.set_value(key=I_NAP, value=new_I_NaP)

    @property
    def g_NaP(self):
        return self._data[G_NAP]

    @ g_NaP.setter
    def g_NaP(self, new_g_NaP):
        self._data.set_value(key=G_NAP, value=new_g_NaP)

    @property
    def E_NaP(self):
        return self._data[E_NAP]

    @ E_NaP.setter
    def E_NaP(self, new_E_NaP):
        self._data.set_value(key=E_NAP, value=new_E_NaP)

    @property
    def m_inf_NaP(self):
        return self._data[M_INF_NAP]

    @ m_inf_NaP.setter
    def m_inf_NaP(self, new_m_inf_NaP):
        self._data.set_value(key=M_INF_NAP, value=new_m_inf_NaP)

    @property
    def I_DK(self):
        return self._data[I_DK]

    @ I_DK.setter
    def I_DK(self, new_I_DK):
        self._data.set_value(key=I_DK, value=new_I_DK)

    @property
    def g_DK(self):
        return self._data[G_DK]

    @ g_DK.setter
    def g_DK(self, new_g_DK):
        self._data.set_value(key=G_DK, value=new_g_DK)

    @property
    def E_DK(self):
        return self._data[E_DK]

    @ E_DK.setter
    def E_DK(self, new_E_DK):
        self._data.set_value(key=E_DK, value=new_E_DK)

    @property
    def m_inf_DK(self):
        return self._data[M_INF_DK]

    @ m_inf_DK.setter
    def m_inf_DK(self, new_m_inf_DK):
        self._data.set_value(key=M_INF_DK, value=new_m_inf_DK)

    @property
    def e_to_t_on_tau_m_DK(self):
        return self._data[E_TO_T_ON_TAU_M_DK]

    @ e_to_t_on_tau_m_DK.setter
    def e_to_t_on_tau_m_DK(self, new_e_to_t_on_tau_m_DK):
        self._data.set_value(key=E_TO_T_ON_TAU_M_DK, value=new_e_to_t_on_tau_m_DK)

    @property
    def D(self):
        return self._data[D]

    @ D.setter
    def D(self, new_D):
        self._data.set_value(key=D, value=new_D)

    @property
    def D_infinity(self):
        return self._data[D_INFINITY]

    @ D_infinity.setter
    def D_infinity(self, new_D_infinity):
        self._data.set_value(key=D_INFINITY, value=new_D_infinity)

    @property
    def e_to_t_on_tau_h_DK(self):
        return self._data[E_TO_T_ON_TAU_H_DK]

    @property
    def v_clamp(self):
        return self._data[V_CLAMP]

    @ v_clamp.setter
    def v_clamp(self, new_v_clamp):
        self._data.set_value(key=V_CLAMP, value=new_v_clamp)

    @property
    def s_clamp(self):
        return self._data[S_CLAMP]

    @ s_clamp.setter
    def s_clamp(self, new_s_clamp):
        self._data.set_value(key=S_CLAMP, value=new_s_clamp)

    @property
    def t_clamp(self):
        return self._data[T_CLAMP]

    @ t_clamp.setter
    def t_clamp(self, new_t_clamp):
        self._data.set_value(key=T_CLAMP, value=new_t_clamp)

    @property
    def dt(self):
        return self._data[DT]

    @ dt.setter
    def dt(self, new_dt):
        self._data.set_value(key=DT, value=new_dt)

    def get_n_parameters(self):
        return 30

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_parameters(self, machine_time_step):
        # pylint: disable=arguments-differ
        return [NeuronParameter(self._data[I_H],_INTRINSIC_CURRENTS_TYPES.I_H.data_type),
               NeuronParameter(self._data[G_H],_INTRINSIC_CURRENTS_TYPES.g_H.data_type),
               NeuronParameter(self._data[E_H],_INTRINSIC_CURRENTS_TYPES.E_H.data_type),
               NeuronParameter(self._data[M_H],_INTRINSIC_CURRENTS_TYPES.m_H.data_type),
               NeuronParameter(self._data[M_INF_H],_INTRINSIC_CURRENTS_TYPES.m_inf_H.data_type),
               NeuronParameter(self._data[E_TO_T_ON_TAU_M_H],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_m_H.data_type),
               NeuronParameter(self._data[I_T],_INTRINSIC_CURRENTS_TYPES.I_T.data_type),
               NeuronParameter(self._data[G_T],_INTRINSIC_CURRENTS_TYPES.g_T.data_type),
               NeuronParameter(self._data[E_T],_INTRINSIC_CURRENTS_TYPES.E_T.data_type),
               NeuronParameter(self._data[M_T],_INTRINSIC_CURRENTS_TYPES.m_T.data_type),
               NeuronParameter(self._data[M_INF_T],_INTRINSIC_CURRENTS_TYPES.m_inf_T.data_type),
               NeuronParameter(self._data[E_TO_T_ON_TAU_M_T],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_m_T.data_type),
               NeuronParameter(self._data[H_T],_INTRINSIC_CURRENTS_TYPES.h_T.data_type),
               NeuronParameter(self._data[H_INF_T],_INTRINSIC_CURRENTS_TYPES.h_inf_T.data_type),
               NeuronParameter(self._data[E_TO_T_ON_TAU_H_T],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_h_T.data_type),
               NeuronParameter(self._data[I_NAP],_INTRINSIC_CURRENTS_TYPES.I_NaP.data_type),
               NeuronParameter(self._data[G_NAP],_INTRINSIC_CURRENTS_TYPES.g_NaP.data_type),
               NeuronParameter(self._data[E_NAP],_INTRINSIC_CURRENTS_TYPES.E_NaP.data_type),
               NeuronParameter(self._data[M_INF_NAP],_INTRINSIC_CURRENTS_TYPES.m_inf_NaP.data_type),
               NeuronParameter(self._data[I_DK],_INTRINSIC_CURRENTS_TYPES.I_DK.data_type),
               NeuronParameter(self._data[G_DK],_INTRINSIC_CURRENTS_TYPES.g_DK.data_type),
               NeuronParameter(self._data[E_DK],_INTRINSIC_CURRENTS_TYPES.E_DK.data_type),
               NeuronParameter(self._data[M_INF_DK],_INTRINSIC_CURRENTS_TYPES.m_inf_DK.data_type),
               NeuronParameter(self._data[E_TO_T_ON_TAU_M_DK],_INTRINSIC_CURRENTS_TYPES.e_to_t_on_tau_m_DK.data_type),
               NeuronParameter(self._data[D],_INTRINSIC_CURRENTS_TYPES.D.data_type),
               NeuronParameter(self._data[D_INFINITY],_INTRINSIC_CURRENTS_TYPES.D_infinity.data_type),
               NeuronParameter(self._data[V_CLAMP],_INTRINSIC_CURRENTS_TYPES.v_clamp.data_type),
               NeuronParameter(self._data[S_CLAMP],_INTRINSIC_CURRENTS_TYPES.s_clamp.data_type),
               NeuronParameter(self._data[T_CLAMP],_INTRINSIC_CURRENTS_TYPES.t_clamp.data_type),
               NeuronParameter(self._data[DT],_INTRINSIC_CURRENTS_TYPES.dt.data_type)
               ]

    def get_parameter_types(self):
        return [item.data_type for item in _INTRINSIC_CURRENTS_TYPES]

    def set_parameters(self, parameters, vertex_slice):
        pass

    def get_n_cpu_cycles_per_neuron(self):
        return 100

