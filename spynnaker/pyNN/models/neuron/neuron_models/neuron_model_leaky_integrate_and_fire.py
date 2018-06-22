from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from .abstract_neuron_model import AbstractNeuronModel
from spynnaker.pyNN.utilities import utility_calls

from data_specification.enums import DataType

import numpy

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms'
}


class NeuronModelLeakyIntegrateAndFire(AbstractNeuronModel):
    __slots__ = [
        "_v_init",
        "_v_rest",
        "_tau_m",
        "_cm",
        "_i_offset",
        "_v_reset",
        "_tau_refrac"]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac):
        if v_init is None:
            v_init = v_rest
        self._v_init = v_init
        self._v_rest = v_rest
        self._tau_m = tau_m
        self._cm = cm
        self._i_offset = i_offset
        self._v_reset = v_reset
        self._tau_refrac = tau_refrac

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 8 items per neuron (4 bytes each)
        return 8 * 4 * n_neurons

    @overrides(AbstractNeuronModel.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 8 items per neuron (4 bytes each)
        return 8 * 4 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(V_REST, self._v_rest)
        parameters.set_value(TAU_M, self._tau_m)
        parameters.set_value(CM, self._cm)
        parameters.set_value(I_OFFSET, self._i_offset)
        parameters.set_value(V_RESET, self._v_reset)
        parameters.set_value(TAU_REFRAC, self._tau_refrac)

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables.set_value(V, self._v_init)
        state_variables.set_value(COUNT_REFRAC, 0)

    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_data,
               additional_arguments={'machine_time_step'})
    def get_data(
            self, parameters, state_variables, vertex_slice,
            machine_time_step):

        # Add the rest of the data
        items = [
            (state_variables[V], DataType.S1615),
            (parameters[V_REST], DataType.S1615),
            (parameters[TAU_M] / parameters[CM], DataType.S1615),
            (parameters[TAU_M].apply_operation(
                operation=lambda x:
                    numpy.exp(float(-machine_time_step) / (1000.0 * x))),
                DataType.S1615),
            (parameters[I_OFFSET], DataType.S1615),
            (state_variables[COUNT_REFRAC], DataType.INT32),
            (parameters[V_RESET], DataType.S1615),
            (parameters[TAU_REFRAC].apply_operation(
                operation=lambda x:
                    numpy.ceil(x / (machine_time_step / 1000.0)),
                DataType.INT32))
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractNeuronModel.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.S1615 * 8]
        offset, (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
                 _v_reset, _tau_refrac) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        # Copy the changed data only
        utility_calls.copy_values(v, state_variables[V], vertex_slice)
        utility_calls.copy_values(
            count_refrac, state_variables[COUNT_REFRAC], vertex_slice)
        return offset

    @property
    def v_init(self):
        return self._v

    @v_init.setter
    def v_init(self, v_init):
        self._v = v_init

    @property
    def v_rest(self):
        return self._data[V_REST]

    @v_rest.setter
    def v_rest(self, v_rest):
        self._data.set_value(key=V_REST, value=v_rest)

    @property
    def tau_m(self):
        return self._data[TAU_M]

    @tau_m.setter
    def tau_m(self, tau_m):
        self._data.set_value(key=TAU_M, value=tau_m)

    @property
    def cm(self):
        return self._data[CM]

    @cm.setter
    def cm(self, cm):
        self._data.set_value(key=CM, value=cm)

    @property
    def i_offset(self):
        return self._data[I_OFFSET]

    @i_offset.setter
    def i_offset(self, i_offset):
        self._data.set_value(key=I_OFFSET, value=i_offset)

    @property
    def v_reset(self):
        return self._data[V_RESET]

    @v_reset.setter
    def v_reset(self, v_reset):
        self._data.set_value(key=V_RESET, value=v_reset)

    @property
    def tau_refrac(self):
        return self._data[TAU_REFRAC]

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self._data.set_value(key=TAU_REFRAC, value=tau_refrac)
