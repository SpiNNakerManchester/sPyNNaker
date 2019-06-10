import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items
from .abstract_neuron_model import AbstractNeuronModel

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
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac"]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac):
        super(NeuronModelLeakyIntegrateAndFire, self).__init__(
            [DataType.S1615,   # v
             DataType.S1615,   # v_rest
             DataType.S1615,   # r_membrane (= tau_m / cm)
             DataType.S1615,   # exp_tc (= e^(-ts / tau_m))
             DataType.S1615,   # i_offset
             DataType.INT32,   # count_refrac
             DataType.S1615,   # v_reset
             DataType.INT32])  # tau_refrac

        if v_init is None:
            v_init = v_rest
        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[COUNT_REFRAC] = 0

    @overrides(AbstractNeuronModel.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractNeuronModel.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [state_variables[V], parameters[V_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET], state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0))))]

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac) = values

        # Copy the changed data only
        state_variables[V] = v
        state_variables[COUNT_REFRAC] = count_refrac

    @property
    def v_init(self):
        return self.__v_init

    @v_init.setter
    def v_init(self, v_init):
        self.__v_init = v_init

    @property
    def v_rest(self):
        return self.__v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self.__v_rest = v_rest

    @property
    def tau_m(self):
        return self.__tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self.__tau_m = tau_m

    @property
    def cm(self):
        return self.__cm

    @cm.setter
    def cm(self, cm):
        self.__cm = cm

    @property
    def i_offset(self):
        return self.__i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self.__i_offset = i_offset

    @property
    def v_reset(self):
        return self.__v_reset

    @v_reset.setter
    def v_reset(self, v_reset):
        self.__v_reset = v_reset

    @property
    def tau_refrac(self):
        return self.__tau_refrac

    @tau_refrac.setter
    def tau_refrac(self, tau_refrac):
        self.__tau_refrac = tau_refrac
