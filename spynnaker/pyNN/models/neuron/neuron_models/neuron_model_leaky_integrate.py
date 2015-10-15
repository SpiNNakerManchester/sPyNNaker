from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel
from spynnaker.pyNN.utilities import utility_calls

from data_specification.enums.data_type import DataType

import numpy


class NeuronModelLeakyIntegrate(AbstractNeuronModel):

    def __init__(self, n_neurons, machine_time_step, v_init, v_rest, tau_m, cm,
                 i_offset):
        AbstractNeuronModel.__init__(self)
        self._n_neurons = n_neurons
        self._machine_time_step = machine_time_step
        self._v_init = utility_calls.convert_param_to_numpy(v_init, n_neurons)
        self._v_rest = utility_calls.convert_param_to_numpy(v_rest, n_neurons)
        self._tau_m = utility_calls.convert_param_to_numpy(tau_m, n_neurons)
        self._cm = utility_calls.convert_param_to_numpy(cm, n_neurons)
        self._i_offset = utility_calls.convert_param_to_numpy(
            i_offset, n_neurons)

        if v_init is None:
            self._v_init = v_rest

    def initialize_v(self, v_init):
        self._v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)

    @property
    def v_init(self):
        return self._v_init

    @v_init.setter
    def v_init(self, v_init):
        self._v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)

    @property
    def v_rest(self):
        return self._v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self._v_rest = utility_calls.convert_param_to_numpy(
            v_rest, self._n_neurons)

    @property
    def tau_m(self):
        return self._tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self._tau_m = utility_calls.convert_param_to_numpy(
            tau_m, self._n_neurons)

    @property
    def cm(self):
        return self._cm

    @cm.setter
    def cm(self, cm):
        self._cm = utility_calls.convert_param_to_numpy(cm, self._n_neurons)

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self._i_offset = utility_calls.convert_param_to_numpy(
            i_offset, self._n_neurons)

    @property
    def _r_membrane(self):
        return self._tau_m / self._cm

    @property
    def _exp_tc(self):
        return numpy.exp(float(-self._machine_time_step) /
                         (1000.0 * self._tau_m))

    def get_n_neural_parameters(self):
        return 5

    def get_neural_parameters(self):
        return [

            # membrane voltage [mV]
            # REAL     V_membrane;
            NeuronParameter(self._v_init, DataType.S1615),

            # membrane resting voltage [mV]
            # REAL     V_rest;
            NeuronParameter(self._v_rest, DataType.S1615),

            # membrane resistance [MOhm]
            # REAL     R_membrane;
            NeuronParameter(self._r_membrane, DataType.S1615),

            # 'fixed' computation parameter - time constant multiplier for
            # closed-form solution
            # exp( -(machine time step in ms)/(R * C) ) [.]
            # REAL     exp_TC;
            NeuronParameter(self._exp_tc, DataType.S1615),

            # offset current [nA]
            # REAL     I_offset;
            NeuronParameter(self._i_offset, DataType.S1615)
        ]

    def get_n_global_parameters(self):
        return 0

    def get_global_parameters(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):

        # A bit of a guess
        return 80
