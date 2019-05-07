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
M_DELTA = 'm_delta'
M_DELTA_DIV_SIGMA = 'm_delta_div_sigma'
M_ONE_MINUS_DELTA_DIV_SIGMA = 'm_one_minus_delta_div_sigma'
M_V_HALF = 'm_v_half'
M_N = 'm_N'
M_TAU_0 = 'm_tau_0'
# activation state variables
M = 'm'
M_POW = 'm_pow'
M_INF = 'm_inf'
M_TAU = 'm_tau'
E_TO_DT_ON_M_TAU = 'e_to_dt_on_m_tau'

# inactivation parameters
H_K = 'h_K'
H_SIGMA = 'h_sigma'
H_DELTA = 'h_delta'
H_DELTA_DIV_SIGMA = 'h_delta_div_sigma'
H_ONE_MINUS_DELTA_DIV_SIGMA = 'h_one_minus_delta_div_sigma'
H_V_HALF = 'h_v_half'
H_N = 'h_N'
H_TAU_0 = 'h_tau_0'
# inactivation state
H = 'h'
H_POW = 'h_pow'
H_INF = 'h_inf'
H_TAU = 'h_tau'
E_TO_DT_ON_H_TAU = 'e_to_dt_on_h_tau'


UNITS = {
    # Ion-channel Current
    I_ION: 'nA',
    G: 'uS',
    E: 'mV',
    # activation parameters
    M_K: '',
    M_SIGMA: '',
    M_DELTA: '',
    M_DELTA_DIV_SIGMA: '',
    M_ONE_MINUS_DELTA_DIV_SIGMA: '',
    M_V_HALF: '',
    M_N: '',
    M_TAU_0: '',
    # activation state variables
    M: '',
    M_POW: '',
    M_INF: '',
    M_TAU: 'ms',
    E_TO_DT_ON_M_TAU: '',

    # inactivation parameters
    H_K: '',
    H_SIGMA: '',
    M_DELTA: '',
    H_DELTA_DIV_SIGMA: '',
    H_ONE_MINUS_DELTA_DIV_SIGMA: '',
    H_V_HALF: '',
    H_N: '',
    H_TAU_0: '',
    # inactivation state
    H: '',
    H_POW: '',
    H_INF: '',
    H_TAU: 'ms',
    E_TO_DT_ON_H_TAU: '',
}


class AdditionalInputSingleGenericIonChannel(AbstractAdditionalInput):
    __slots__ = [
    '_I_ion',
    '_g',
    '_E',

    # activation parameters

    '_m_K',
    '_m_delta',
    '_m_sigma',
    '_m_delta_div_sigma',
    '_m_one_minus_delta_div_sigma',
    '_m_v_half',
    '_m_N',
    '_m_tau_0',
    # activation state
    '_m',
    '_m_pow',
    '_m_inf',
    '_m_tau',
    '_e_to_dt_on_m_tau',

    # inactivation parameters
    '_h_K',
    '_h_sigma',
    '_h_delta',
    '_h_delta_div_sigma',
    '_h_one_minus_delta_div_sigma',
    '_h_v_half',
    '_h_N',
    '_h_tau_0',
    # inactivation state
    '_h',
    '_h_pow',
    '_h_inf',
    '_h_tau',
    '_e_to_dt_on_h_tau',
    ]

    def __init__(self, v,
                 I_ion,
                 g,
                 E,
                 # activation parameters
                 m_K,
                 m_v_half,
                 m_N,
                 m_sigma,
                 m_delta,
                 m_tau_0,
                 # activation state
                 m,
                 m_pow,
                 m_inf,
                 m_tau,

                 # inactivation parameters
                 h_K,
                 h_v_half,
                 h_N,
                 h_sigma,
                 h_delta,
                 h_tau_0,
                 # inactivation state
                 h,
                 h_pow,
                 h_inf,
                 h_tau,
                 ):

        super(AdditionalInputSingleGenericIonChannel, self).__init__(
           [
            DataType.S1615,  # I_ion
            DataType.S1615,  # g
            DataType.S1615,  # E

            DataType.S1615,  # m_K
            DataType.S1615,  # m_delta_div_sigma
            DataType.S1615,  # m_one_minus_delta_div_sigma
            DataType.S1615,  # m_v_half
            DataType.UINT32,  # m_N
            DataType.S1615,  # m_tau_0

            DataType.S1615,  # m
            DataType.S1615,  # m_pow
            DataType.S1615,  # m_inf
            DataType.S1615,  # m_tau
            DataType.S1615,  # e_to_dt_on_m_tau

            DataType.S1615,  # h_K
            DataType.S1615,  # h_delta_div_sigma
            DataType.S1615,  # h_one_minus_delta_div_sigma
            DataType.S1615,  # h_v_half
            DataType.UINT32,  # h_N
            DataType.S1615,  # h_tau_0

            DataType.S1615,  # h
            DataType.S1615,  # h_pow
            DataType.S1615,  # h_inf
            DataType.S1615,  # h_tau
            DataType.S1615,  # e_to_dt_on_h_tau
            ])

        v = v

        # Initialise parameters
        self._I_ion = I_ion
        self._g = g
        self._E = E

        # activation parameters
        self._m_K = m_K
        self._m_sigma = m_sigma
        self._m_delta = m_delta
        self._m_delta_div_sigma = m_delta / m_sigma
        self._m_one_minus_delta_div_sigma = (1 - m_delta) / m_sigma
        self._m_v_half = m_v_half
        self._m_N = m_N
        self._m_tau_0 = m_tau_0

        m_alpha = m_K * numpy.exp((m_delta/m_sigma) * (v - m_v_half))
        m_beta = m_K * numpy.exp(-((1 - m_delta)/m_sigma) * (v - m_v_half))

        # activation state
        self._m_pow = m_pow
        self._m_inf = m_alpha / (m_alpha + m_beta)
        self._m = self._m_inf
        self._m_tau = 1 / (m_alpha + m_beta)
        self._e_to_dt_on_m_tau =  numpy.exp(-DT/self._m_tau)




        # inactivation parameters
        self._h_K = h_K
        self._h_sigma = h_sigma
        self._h_delta = h_delta
        self._h_delta_div_sigma = h_delta / h_sigma
        self._h_one_minus_delta_div_sigma = (1 - h_delta)/h_sigma
        self._h_v_half = h_v_half
        self._h_N = h_N
        self._h_tau_0 = h_tau_0

        h_alpha = h_K * numpy.exp((h_delta/h_sigma) * (v - h_v_half))
        h_beta = h_K * numpy.exp(-((1 - h_delta)/h_sigma) * (v - h_v_half))

        # inactivation state
        self._h_pow = h_pow
        self._h_inf = h_alpha / (h_alpha + h_beta)
        self._h = self._h_inf
        self._h_tau = 1 / (h_alpha + h_beta)
        self._e_to_dt_on_h_tau = numpy.exp(-DT/self._h_tau)


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

            parameters[M_K] = self._m_K
            parameters[M_SIGMA] = self._m_sigma
            parameters[M_DELTA] = self._m_delta
            parameters[M_DELTA_DIV_SIGMA] = self._m_delta_div_sigma
            parameters[M_ONE_MINUS_DELTA_DIV_SIGMA] = self._m_one_minus_delta_div_sigma
            parameters[M_V_HALF] = self._m_v_half
            parameters[M_N] = self._m_N
            parameters[M_TAU_0] = self._m_tau_0

            # inactivation parameters

            parameters[H_K] = self._h_K
            parameters[H_SIGMA] = self._h_sigma
            parameters[H_DELTA] = self._h_delta
            parameters[H_DELTA_DIV_SIGMA] = self._h_delta_div_sigma
            parameters[H_ONE_MINUS_DELTA_DIV_SIGMA] = self._h_one_minus_delta_div_sigma
            parameters[H_V_HALF] = self._h_v_half
            parameters[H_N] = self._h_N
            parameters[H_TAU_0] = self._h_tau_0


    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):

            # activation state
            state_variables[M] = self._m
            state_variables[M_POW] = self._m_pow
            state_variables[M_INF] = self._m_inf
            state_variables[M_TAU] = self._m_tau
            state_variables[E_TO_DT_ON_M_TAU] = self._e_to_dt_on_m_tau

            # inactivation state
            state_variables[H] = self._h
            state_variables[H_POW] = self._h_pow
            state_variables[H_INF] = self._h_inf
            state_variables[H_TAU] = self._h_tau
            state_variables[E_TO_DT_ON_H_TAU] = self._e_to_dt_on_h_tau


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

                parameters[M_K],
                parameters[M_DELTA_DIV_SIGMA],
                parameters[M_ONE_MINUS_DELTA_DIV_SIGMA],
                parameters[M_V_HALF],
                parameters[M_N],
                parameters[M_TAU_0],

                state_variables[M],
                state_variables[M_POW],
                state_variables[M_INF],
                state_variables[M_TAU],
                state_variables[E_TO_DT_ON_M_TAU],


                parameters[H_K],
                parameters[H_DELTA_DIV_SIGMA],
                parameters[H_ONE_MINUS_DELTA_DIV_SIGMA],
                parameters[H_V_HALF],
                parameters[H_N],
                parameters[H_TAU_0],

                state_variables[H],
                state_variables[H_POW],
                state_variables[H_INF],
                state_variables[H_TAU],
                state_variables[E_TO_DT_ON_H_TAU]
                ]

    @overrides(AbstractAdditionalInput.update_values)
    def update_values(self, values, parameters, state_variables):
        (
            _I_ion,
            _g,
            _E,

            # activation parameters
            _m_K,
            _m_delta_div_sigma,
            _m_one_minus_delta_div_sigma,
            _m_v_half,
            _m_N,
            _m_tau_0,
            # activation state
            m,
            m_pow, # don't actually need to read this
            m_inf,
            m_tau,
            e_to_dt_on_m_tau,

            # inactivation parameters
            _h_K,
            _h_delta_div_sigma,
            _h_one_minus_delta_div_sigma,
            _h_v_half,
            _h_N,
            _h_tau_0,

            # inactivation state
            h,
            h_pow, # don't actually need to read this
            h_inf,
            h_tau,
            e_to_dt_on_h_tau
        ) = values


        state_variables[M] = m
        state_variables[M_INF] = m_inf
        state_variables[M_TAU] = m_tau
        state_variables[E_TO_DT_ON_M_TAU] = e_to_dt_on_m_tau

        state_variables[H] = h
        state_variables[H_INF] = h_inf
        state_variables[H_TAU] = h_tau
        state_variables[E_TO_DT_ON_H_TAU] = e_to_dt_on_h_tau


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
    def m_tau(self):
        return self._m_tau

    @m_tau.setter
    def m_tau(self, new_m_tau):
        self._m_tau = new_m_tau

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
    def h_tau(self):
        return self._h_tau

    @h_tau.setter
    def h_tau(self, new_h_tau):
        self._h_tau = new_h_tau

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