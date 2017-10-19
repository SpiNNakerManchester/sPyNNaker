from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .neuron_model_leaky_integrate_and_fire import NeuronModelLeakyIntegrateAndFire
from spynnaker.pyNN.utilities import utility_calls
from data_specification.enums import DataType


class _LIF_US_TYPES(Enum):
    V_COMPARTMENT = (1, DataType.S1615)
    C_COMPARTMENT = (2, DataType.S1615)

class NeuronModelLeakyIntegrateAndFireUS(NeuronModelLeakyIntegrateAndFire):
    def __init__(self, n_neurons, v_init, v_rest, tau_m, cm, i_offset, v_reset,
            tau_refrac, V_compartment1, C_compartment1, V_compartment2, C_compartment2):

        NeuronModelLeakyIntegrateAndFire(self, n_neurons, v_init,
            v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        self._V_compartment1 = utility_calls.convert_param_to_numpy(
            V_compartment1, n_neurons)

        self._C_compartment1 = utility_calls.convert_param_to_numpy(
            C_compartment1, n_neurons)

        self._V_compartment2 = utility_calls.convert_param_to_numpy(
            V_compartment2, n_neurons)

        self._C_compartment2 = utility_calls.convert_param_to_numpy(
            C_compartment2, n_neurons)

        self._my_units = {'V_compartment1': 'mV', 'C_compartment1': 'nF',
                          'V_compartment2': 'mV', 'C_compartment2': 'nF'}

    @property
    def V_compartment1(self):
        return self._V_compartment1

    @V_compartmemt1.setter
    def V_compartment1(self, V_compartmemt1):
        self._V_compartment1 = utility_calls.convert_param_to_numpy(
            V_compartment1, self._n_neurons)

    @property
    def C_compartment1(self):
        return self._C_compartment1

    @C_compartmemt1.setter
    def C_compartment1(self, C_compartmemt1):
        self._C_compartment1 = utility_calls.convert_param_to_numpy(
            C_compartment1, self._n_neurons)

    @property
    def V_compartment2(self):
        return self._V_compartment1

    @V_compartmemt2.setter
    def V_compartment2(self, V_compartmemt2):
        self._V_compartment1 = utility_calls.convert_param_to_numpy(
            V_compartment2, self._n_neurons)

    @property
    def C_compartment2(self):
        return self._C_compartment2

    @C_compartmemt2.setter
    def C_compartment2(self, C_compartmemt1):
        self._C_compartment2 = utility_calls.convert_param_to_numpy(
            C_compartment2, self._n_neurons)

    @overrides(NeuronModelLeakyIntegrateAndFire.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return NeuronModelLeakyIntegrateAndFire.get_n_neural_parameters(self) + 4

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_neural_parameters(self, machine_time_step):
        params = NeuronModelLeakyIntegrateAndFire.get_neural_parameters(self)
        params.extend([
            NeuronParameter(self._V_compartment1, _LIF_US_TYPES.V_COMPARTMENT.data_type),
            NeuronParameter(self._C_compartment1, _LIF_US_TYPES.C_COMPARTMENT.data_type),
            NeuronParameter(self._V_compartment2, _LIF_US_TYPES.V_COMPARTMENT.data_type),
            NeuronParameter(self._C_compartment2, _LIF_US_TYPES.C_COMPARTMENT.data_type)
        ])
        return params

    @overrides(NeuronModelLeakyIntegrateAndFire.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        lif_US_types = NeuronModelLeakyIntegrateAndFire.get_neural_parameter_types(self)
        lif_US_types.extend([item.data_type for item in _LIF_US_TYPES])
        return lif_US_types

    def get_n_cpu_cycles_per_neuron(self):
        return NeuronModelLeakyIntegrateAndFire.get_n_cpu_cycles_per_neuron(self) + 20

    @overrides(NeuronModelLeakyIntegrateAndFire.get_units)
    def get_units(self, variable):
        if variable in self._my_units:
            return self._my_units[variable]
        else:
            return NeuronModelLeakyIntegrateAndFire.get_units(variable)
