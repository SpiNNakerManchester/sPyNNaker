from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AbstractAdditionalInput
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary
import numpy
from enum import Enum


DT = 0.1

# Ion-channel Current
I_ION = 'I_ion'
G = 'g'
E = 'E'
# activation parameters
M_K = 'm_K'
M_SIGMA = 'm_sigma'
M_DELTA_DIV_SIGMA = 'm_delta_div_sigma'
M_ONE_MINUS_DELTA_DIV_SIGMA = 'm_one_minus_delta_div_sigma'
M_V_HALF = 'm_v_half'
M_N = 'm_N'
# activation state variables
M = 'm'
M_POW = 'm_pow'
M_INF = 'm_inf'
TAU_M = 'tau_m'
E_TO_DT_ON_TAU_M = 'e_to_dt_on_tau_m'

# inactivation parameters
H_K = 'h_K'
H_SIGMA = 'h_sigma'
H_DELTA_DIV_SIGMA = 'h_delta_div_sigma'
H_ONE_MINUS_DELTA_DIV_SIGMA = 'h_one_minus_delta_div_sigma'
H_V_HALF = 'h_v_half'
H_N = 'h_N'
# inactivation state
H = 'h'
H_POW = 'h_pow'
H_INF = 'h_inf'
TAU_H = 'tau_h'
E_TO_DT_ON_TAU_H = 'e_to_dt_on_tau_h'


UNITS = {
    # Ion-channel Current
    I_ION: 'nA',
    G: 'uS',
    E: 'mV',
    # activation parameters
    M_K: '',
    M_SIGMA: '',
    M_DELTA_DIV_SIGMA: '',
    M_ONE_MINUS_DELTA_DIV_SIGMA: '',
    M_V_HALF: '',
    M_N: '',
    # activation state variables
    M: '',
    M_POW: '',
    M_INF: '',
    TAU_M: 'ms',
    E_TO_DT_ON_TAU_M: '',

    # inactivation parameters
    H_K: '',
    H_SIGMA: '',
    H_DELTA_DIV_SIGMA: '',
    H_ONE_MINUS_DELTA_DIV_SIGMA: '',
    H_V_HALF: '',
    H_N: '',
    # inactivation state
    H: '',
    H_POW: '',
    H_INF: '',
    TAU_H: 'ms',
    E_TO_DT_ON_TAU_H: '',
}


class AdditionalInputSingleGenericIonChannel(AbstractAdditionalInput):
    __slots__ = [
    '_I_ion',
    '_g',
    '_E',

    # activation parameters
    '_m_pow',
    '_m_K',
    '_m_delta_div_sigma',
    '_m_one_minus_delta_div_sigma',
    '_m_v_half',
    '_m_N',
    # activation state
    '_m',
    '_m_inf',
    '_tau_m',
    '_e_to_dt_on_tau_m',

    # inactivation parameters
    '_h_pow',
    '_h_K',
    '_h_delta_div_sigma',
    '_h_one_minus_delta_div_sigma',
    '_h_v_half',
    '_h_N',
    # inactivation state
    '_h',
    '_h_inf',
    '_tau_h',
    '_e_to_dt_on_tau_h',
    ]

    def __init__(self, v,
                 I_ion,
                 g,
                 E,
                 # activation parameters
                 m_pow,
                 m_K,
                 m_v_half,
                 m_N,
                 m_sigma,
                 m_delta,
                 # activation state
                 m,
                 m_inf,
                 tau_m,

                 # inactivation parameters
                 h_pow,
                 h_K,
                 h_v_half,
                 h_N,
                 h_sigma,
                 h_delta,
                 # inactivation state
                 h,
                 h_inf,
                 tau_h,
                 ):

        super(AdditionalInputSingleGenericIonChannel, self).__init__(
           [
            DataType.S1615,  # I_ion
            DataType.S1615,  # g
            DataType.S1615,  # E

            DataType.S1615,  # m_pow
            DataType.S1615,  # m_K
            DataType.S1615,  # m_delta_div_sigma
            DataType.S1615,  # m_one_minus_delta_div_sigma
            DataType.S1615,  # m_v_half
            DataType.UINT32,  # m_N

            DataType.S1615,  # m
            DataType.S1615,  # m_inf
            DataType.S1615,  # tau_m
            DataType.S1615,  # e_to_dt_on_tau_m

            DataType.S1615,  # h_pow
            DataType.S1615,  # h_K
            DataType.S1615,  # h_delta_div_sigma
            DataType.S1615,  # h_one_minus_delta_div_sigma
            DataType.S1615,  # h_v_half
            DataType.UINT32,  # h_N

            DataType.S1615,  # h
            DataType.S1615,  # h_inf
            DataType.S1615,  # tau_h
            DataType.S1615,  # e_to_dt_on_tau_h
            ])

        v = v

        # Initialise parameters
        self._I_ion = I_ion
        self._g = g
        self._E = E
        # activation parameters
        self._m_pow = m_pow
        self._m_K = m_K
        self._m_delta_div_sigma = m_delta / m_sigma
        self._m_one_minus_delta_div_sigma = (1 - m_delta) / m_sigma
        self._m_v_half = m_v_half
        self._m_N = m_N
        # activation state
        self._m = m
        self._m_inf = m_inf
        self._tau_m = tau_m
        self._e_to_dt_on_tau_m =  numpy.exp(-DT/self._tau_m)
        # inactivation parameters
        self._h_pow = h_pow
        self._h_K = h_K
        self._h_delta_div_sigma = h_delta / d_sigma
        self._h_one_minus_delta_div_sigma = (1 - h_delta)/d_sigma
        self._h_v_half = h_v_half
        self._h_N = h_N
        # inactivation state
        self._h = h
        self._h_inf = h_inf
        self._tau_h = tau_h
        self._e_to_dt_on_tau_h = numpy.exp(-DT/self._tau_h)








    @overrides(AbstractAdditionalInput.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 300 * n_neurons

    @overrides(AbstractAdditionalInput.add_parameters)
    def add_parameters(self, parameters):

            parameters[I_ION] = self._I_ion
            parameters[G] = self._g
            parameters[E] = self._E

            # activation parameters
            parameters[M_POW] = self._m_pow
            parameters[M_K] = self._m_K
            parameters[M_DELTA_DIV_SIGMA] = self._m_delta_div_sigma
            parameters[M_ONE_MINUS_DELTA_DIV_SIGMA] = self._m_one_minus_delta_div_sigma
            parameters[M_V_HALF] = self._m_v_half
            parameters[M_N] = self._m_N

            # inactivation parameters
            parameters[H_POW] = self._h_pow
            parameters[H_K] = self._h_K
            parameters[H_DELTA_DIV_SIGMA] = self._h_delta_div_sigma
            parameters[H_ONE_MINUS_DELTA_DIV_SIGMA] = self._h_one_minus_delta_div_sigma
            parameters[H_V_HALF] = self._h_v_half
            parameters[H_N] = self._h_N




    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):
            # activation state
            state_variables[M] = self._m
            state_variables[M_INF] = self._m_inf
            state_variables[TAU_M] = self._tau_m
            state_variables[E_TO_DT_ON_TAU_M] = self._e_to_dt_on_tau_m
            # inactivation state
            state_variables[H] = self._h
            state_variables[H_INF] = self._h_inf
            state_variables[TAU_H] = self._tau_h
            state_variables[E_TO_DT_ON_TAU_H] = self._e_to_dt_on_tau_h


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
                parameters[I_ION],
                parameters[G],
                parameters[E],

                parameters[M_POW],
                parameters[M_K],
                parameters[M_DELTA_DIV_SIGMA],
                parameters[M_ONE_MINUS_DELTA_DIV_SIGMA],
                parameters[M_V_HALF],
                parameters[M_N],

                state_variables[M],
                state_variables[M_INF],
                state_variables[TAU_M],
                state_variables[E_TO_DT_ON_TAU_M],

                parameters[H_POW],
                parameters[H_K],
                parameters[H_DELTA_DIV_SIGMA],
                parameters[H_ONE_MINUS_DELTA_DIV_SIGMA],
                parameters[H_V_HALF],
                parameters[H_N],

                state_variables[H],
                state_variables[H_INF],
                state_variables[TAU_H],
                tate_variables[E_TO_DT_ON_TAU_H]
                ]

    @overrides(AbstractAdditionalInput.update_values)
    def update_values(self, values, parameters, state_variables):
        (
            _I_ion,
            _g,
            _E,

            # activation parameters
            _m_pow,
            _m_K,
            _m_delta_div_sigma,
            _m_one_minus_delta_div_sigma,
            _m_v_half,
            _m_N,
            # activation state
            m,
            m_inf,
            tau_m,
            e_to_dt_on_tau_m,

            # inactivation parameters
            _h_pow,
            _h_K,
            _h_delta_div_sigma,
            _h_one_minus_delta_div_sigma,
            _h_v_half,
            _h_N,
            # inactivation state
            h,
            h_inf,
            tau_h,
            e_to_dt_on_tau_h
        ) = values


        self._m = m
        self._m_inf = m_inf
        self._tau_m = tau_m
        self._e_to_dt_on_tau_m = e_to_dt_on_tau_m

        self._h = h
        self._h_inf = h_inf
        self._tau_h = tau_h
        self._e_to_dt_on_tau_h = e_to_dt_on_tau_h


    @property
    def I_ion(self):
        return self._I_ion

    @I_ion.setter
    def I_ion(self, new_I_ion):
        self._I_ion = new_I_ion

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, new_g):
        self._g = new_g


    @property
    def E(self):
        return self._E

    @E.setter
    def E(self, new_E):
        self._E = new_E

    @property
    def m_pow(self):
        return self._m_pow

    @m_pow.setter
    def m_pow(self, new_m_pow):
        self._m_pow = new_m_pow

    @property
    def m_K(self):
        return self._m_K

    @m_K.setter
    def m_K(self, new_m_K):
        self._m_K = new_m_K

    @property
    def m_v_half(self):
        return self._m_v_half

    @m_v_half.setter
    def m_v_half(self, new_m_v_half):
        self._m_v_half = new_m_v_half

    @property
    def tau_m(self):
        return self._tau_m

    @tau_m.setter
    def tau_m(self, new_tau_m):
        self._tau_m = new_tau_m

    @property
    def m_delta(self):
        return self._m_delta

    @m_delta.setter
    def m_delta(self, new_m_delta):
        self._m_delta = new_m_delta

    @property
    def m_sigma(self):
        return self._m_sigma

    @m_sigma.setter
    def m_sigma(self, new_m_sigma):
        self._m_sigma = new_m_sigma

    @property
    def h_pow(self):
        return self._h_pow

    @h_pow.setter
    def h_pow(self, new_h_pow):
        self._h_pow = new_h_pow

    @property
    def h_K(self):
        return self._h_K

    @h_K.setter
    def h_K(self, new_h_K):
        self._h_K = new_h_K

    @property
    def h_v_half(self):
        return self._h_v_half

    @h_v_half.setter
    def h_v_half(self, new_h_v_half):
        self._h_v_half = new_h_v_half

    @property
    def tau_h(self):
        return self._tau_h

    @tau_h.setter
    def tau_h(self, new_tau_h):
        self._tau_h = new_tau_h

    @property
    def h_delta(self):
        return self._h_delta

    @h_delta.setter
    def h_delta(self, new_h_delta):
        self._h_delta = new_h_delta

    @property
    def h_sigma(self):
        return self._h_sigma

    @h_sigma.setter
    def h_sigma(self, new_h_sigma):
        self._h_sigma = new_h_sigma