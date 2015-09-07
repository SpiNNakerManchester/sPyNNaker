from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel

from data_specification.enums.data_type import DataType


class NeuronModelIzh(AbstractNeuronModel):

    def __init__(self, machine_time_step, a, b, c, d, v_init, u_init,
                 i_offset):
        AbstractNeuronModel.__init__(self)
        self._machine_time_step = machine_time_step
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._v_init = v_init
        self._u_init = u_init
        self._i_offset = i_offset

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
        return self.c

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

    def initialize_v(self, v_init):
        self._v_init = v_init

    def initialize_u(self, u_init):
        self._u_init = u_init

    def get_n_neural_parameters(self):
        return 8

    def get_neural_parameters(self):
        return [

            # REAL A
            NeuronParameter(self._a, DataType.S1615),

            # REAL B
            NeuronParameter(self._b, DataType.S1615),

            # REAL C
            NeuronParameter(self._c, DataType.S1615),

            # REAL D
            NeuronParameter(self._d, DataType.S1615),

            # REAL V
            NeuronParameter(self._v_init, DataType.S1615),

            # REAL U
            NeuronParameter(self._u_init, DataType.S1615),

            # offset current [nA]
            # REAL I_offset;
            NeuronParameter(self._i_offset, DataType.S1615),

            # current timestep - simple correction for threshold
            # REAL this_h;
            NeuronParameter(self._machine_time_step / 1000.0, DataType.S1615)
        ]

    def get_n_global_parameters(self):
        return 1

    def get_global_parameters(self):
        return [
            NeuronParameter(self._machine_time_step / 1000.0, DataType.S1615)
        ]

    def get_n_cpu_cycles_per_neuron(self):

        # A bit of a guess
        return 150
