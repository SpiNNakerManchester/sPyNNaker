from spinn_utilities import overrides
from .abstract_neuron_model import AbstractNeuronModel
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items

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
        super(NeuronModelIzh, self).__init__(
            [DataType.S1615,   # a
             DataType.S1615,   # b
             DataType.S1615,   # c
             DataType.S1615,   # d
             DataType.S1615,   # v
             DataType.S1615,   # u
             DataType.S1615,   # i_offset
             DataType.S1615]   # this_h (= machine_time_step)
            [DataType.S1615])  # machine_time_step

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
    @overrides(AbstractNeuronModel.get_global_values,
               additional_arguments={'machine_time_step'})
    def get_global_values(self, machine_time_step):
        return [machine_time_step]

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [
            parameters[A], parameters[B], parameters[C], parameters[D],
            state_variables[V], state_variables[U], parameters[I_OFFSET],
            float(ts) / 1000.0
        ]

    @overrides(AbstractNeuronModel.update_values)
    def update_values(self, values, parameters, state_variables):

        # Decode the values
        _a, _b, _c, _d, v, u, _i_offset = values

        # Copy the changed data only
        state_variables[V] = v
        state_variables[U] = u

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
