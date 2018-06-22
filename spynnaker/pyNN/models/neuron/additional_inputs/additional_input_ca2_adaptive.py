from pacman.executor.injection_decorator import inject_items
from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neuron.additional_inputs \
    import AbstractAdditionalInput

import numpy

I_ALPHA = "i_alpha"
I_CA2 = "i_ca2"
TAU_CA2 = "tau_ca2"

UNITS = {
    I_ALPHA: "nA",
    I_CA2: "nA",
    TAU_CA2: "ms"
}


class AdditionalInputCa2Adaptive(AbstractAdditionalInput):
    __slots__ = [
        "_tau_ca2",
        "_i_ca2",
        "_i_alpha"]

    def __init__(self,  tau_ca2, i_ca2, i_alpha):
        self._tau_ca2 = tau_ca2
        self._i_ca2 = i_ca2
        self._i_alpha = i_alpha

    @overrides(AbstractAdditionalInput.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 3 * n_neurons

    @overrides(AbstractAdditionalInput.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 3 parameters per neuron (4 bytes each)
        return (3 * 4 * n_neurons)

    @overrides(AbstractAdditionalInput.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 3 parameters per neuron (4 bytes each)
        return (3 * 4 * n_neurons)

    @overrides(AbstractAdditionalInput.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(TAU_CA2, self._tau_ca2)
        parameters.set_value(I_ALPHA, self._i_alpha)

    @overrides(AbstractAdditionalInput.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables.set_value(I_CA2, self._i_ca2)

    @overrides(AbstractAdditionalInput.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractAdditionalInput.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractAdditionalInput.get_data,
               additional_arguments={'machine_time_step'})
    def get_data(
            self, parameters, state_variables, vertex_slice,
            machine_time_step):

        # Add the rest of the data
        items = [
            (parameters[TAU_CA2].apply_operation(
                operation=lambda x:
                    numpy.exp(float(-machine_time_step) / (1000.0 * x))),
             DataType.S1615),
            (state_variables[I_CA2], DataType.S1615),
            (parameters[I_ALPHA], DataType.S1615)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractAdditionalInput.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.S1615 * 3]
        offset, (_exp_tau_ca2, i_ca2, _i_alpha) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        # Copy the changed data only
        utility_calls.copy_values(i_ca2, state_variables[I_CA2], vertex_slice)
        return offset

    @property
    def tau_ca2(self):
        return self._tau_ca2

    @tau_ca2.setter
    def tau_ca2(self, tau_ca2):
        self._tau_ca2 = tau_ca2

    @property
    def i_ca2(self):
        return self._i_ca2

    @i_ca2.setter
    def i_ca2(self, i_ca2):
        self._i_ca2 = i_ca2

    @property
    def i_alpha(self):
        return self._i_alpha

    @i_alpha.setter
    def i_alpha(self, i_alpha):
        self._i_alpha = i_alpha
