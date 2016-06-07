from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.neuron_model_leaky_integrate \
    import NeuronModelLeakyIntegrate

from data_specification.enums.data_type import DataType

import numpy


class NeuronModelLeakyIntegrateAndFire(NeuronModelLeakyIntegrate):

    def __init__(self, bag_of_neurons):
        NeuronModelLeakyIntegrate.__init__(self, bag_of_neurons)

    @property
    def v_reset(self):
        return self._get_param('v_reset', self._atoms)

    @property
    def tau_refrac(self):
        return self._get_param('tau_refrac', self._atoms)

    def get_n_neural_parameters(self):
        return NeuronModelLeakyIntegrate.get_n_neural_parameters(self) + 3

    def _tau_refrac_timesteps(self, atom_id):
        return numpy.ceil(
            self._atoms[atom_id].get("tau_refrac") /
            (self._atoms[atom_id].population_parameters["machine_time_step"]
             / 1000.0))

    def get_neural_parameters(self, atom_id):
        params = NeuronModelLeakyIntegrate.get_neural_parameters(self, atom_id)
        params.extend([

            # countdown to end of next refractory period [timesteps]
            # int32_t  refract_timer;
            NeuronParameter(0, DataType.INT32),

            # post-spike reset membrane voltage [mV]
            # REAL     V_reset;
            NeuronParameter(self._atoms[atom_id].get("v_reset"),
                            DataType.S1615),

            # refractory time of neuron [timesteps]
            # int32_t  T_refract;
            NeuronParameter(self._tau_refrac_timesteps(atom_id),
                            DataType.INT32)
        ])
        return params

    def get_n_cpu_cycles_per_neuron(self):

        # A guess - 20 for the reset procedure
        return NeuronModelLeakyIntegrate.get_n_cpu_cycles_per_neuron(self) + 20
