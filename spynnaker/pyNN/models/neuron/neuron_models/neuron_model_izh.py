from spinn_utilities.overrides import overrides
from .abstract_neuron_model import AbstractNeuronModel
from data_specification.enums import DataType

from spynnaker.pyNN.utilities import utility_calls
from pacman.executor.injection_decorator import inject_items
import numpy

A = 'a'
B = 'b'
C = 'c'
D = 'd'
V = 'v'
U = 'u'
I_OFFSET = 'i_offset'

UNITS = {
    A: "ms",
    B: "ms",
    C: "mV",
    D: "mV/ms",
    V: "mV",
    U: "mV/ms",
    I_OFFSET: "nA"
}


class NeuronModelIzh(AbstractNeuronModel):

    __slots__ = [
        "_a", "_b", "_c", "_d", "_i_offset", "_v_init", "_u_init"
    ]

    def __init__(self, a, b, c, d,  i_offset, v_init, u_init):
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._i_offset = i_offset
        self._v_init = v_init
        self._u_init = u_init

    @overrides(AbstractNeuronModel.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractNeuronModel.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # Timestep is global word (4 bytes)
        # + 7 parameters per neuron (4 bytes each)
        return 4 + (7 * 4 * n_neurons)

    @overrides(AbstractNeuronModel.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # Timestep is global word (4 bytes)
        # + 7 parameters per neuron (4 bytes each)
        return 4 + (7 * 4 * n_neurons)

    @overrides(AbstractNeuronModel.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(A, self._a)
        parameters.set_value(B, self._b)
        parameters.set_value(C, self._c)
        parameters.set_value(D, self._d)
        parameters.set_value(I_OFFSET, self._i_offset)

    @overrides(AbstractNeuronModel.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables.set_value(V, self._v_init)
        state_variables.set_value(U, self._u_init)

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

        # Add the "global parameter" of the machine time step
        data = list()
        data.append(utility_calls.get_struct_as_array(
            [(machine_time_step, DataType.S1615)]))

        # Add the rest of the data
        items = [
            (parameters[A], DataType.S1615),
            (parameters[B], DataType.S1615),
            (parameters[C], DataType.S1615),
            (parameters[D], DataType.S1615),
            (state_variables[V], DataType.S1615),
            (state_variables[U], DataType.S1615),
            (parameters[I_OFFSET], DataType.S1615)
        ]
        data.append(utility_calls.get_parameter_data(items, vertex_slice))
        return numpy.concatenate(data)

    @overrides(AbstractNeuronModel.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data, skipping the machine time step
        # (4 bytes which won't have changed)
        types = [DataType.S1615 * 7]
        offset, (_a, _b, _c, _d, v, u, _i_offset) = \
            utility_calls.read_parameter_data(
                types, data, offset + 4, vertex_slice.n_atoms)

        # Copy the changed data only
        utility_calls.copy_values(v, state_variables[V], vertex_slice)
        utility_calls.copy_values(u, state_variables[U], vertex_slice)
        return offset

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, a):
        self._a = a

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, b):
        self._b = b

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c):
        self._c = c

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, d):
        self._d = d

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self._i_offset = i_offset

    @property
    def v_init(self):
        return self._v_init

    @v_init.setter
    def v_init(self, v_init):
        self._v_init = v_init

    @property
    def u_init(self):
        return self._u_init

    @u_init.setter
    def u_init(self, u_init):
        self._u_init = u_init
