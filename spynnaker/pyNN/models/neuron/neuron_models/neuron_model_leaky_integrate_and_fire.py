from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.neuron_model_leaky_integrate \
    import NeuronModelLeakyIntegrate
from spynnaker.pyNN.utilities import utility_calls

from data_specification.enums.data_type import DataType

import numpy


class NeuronModelLeakyIntegrateAndFire(NeuronModelLeakyIntegrate):

    def __init__(self, n_neurons, machine_time_step, v_init, v_rest, tau_m, cm,
                 i_offset, v_reset, tau_refrac):
        NeuronModelLeakyIntegrate.__init__(
            self, n_neurons, machine_time_step, v_init, v_rest, tau_m, cm,
            i_offset)
        self._v_reset = utility_calls.convert_param_to_numpy(
            v_reset, n_neurons)
        self._tau_refrac = utility_calls.convert_param_to_numpy(
            tau_refrac, n_neurons)

    @property
    def v_reset(self):
        return self._v_reset

    @v_reset.setter
    def v_reset(self, v_reset):
        self._v_reset = utility_calls.convert_param_to_numpy(
            v_reset, self._n_neurons)

    @property
    def tau_refrac(self):
        return self._tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self._tau_refrac = utility_calls.convert_param_to_numpy(
            tau_refrac, self._n_neurons)

    def get_n_neural_parameters(self):
        return NeuronModelLeakyIntegrate.get_n_neural_parameters(self) + 3

    @property
    def _tau_refrac_timesteps(self):
        return numpy.ceil(self._tau_refrac /
                          (self._machine_time_step / 1000.0))

    def get_neural_parameters(self):
        params = NeuronModelLeakyIntegrate.get_neural_parameters(self)
        params.extend([

            # countdown to end of next refractory period [timesteps]
            # int32_t  refract_timer;
            NeuronParameter(0, DataType.INT32),

            # post-spike reset membrane voltage [mV]
            # REAL     V_reset;
            NeuronParameter(self._v_reset, DataType.S1615),

            # refractory time of neuron [timesteps]
            # int32_t  T_refract;
            NeuronParameter(self._tau_refrac_timesteps, DataType.INT32)
        ])
        return params

    def get_n_cpu_cycles_per_neuron(self):

        # A guess - 20 for the reset procedure
        return NeuronModelLeakyIntegrate.get_n_cpu_cycles_per_neuron(self) + 20
