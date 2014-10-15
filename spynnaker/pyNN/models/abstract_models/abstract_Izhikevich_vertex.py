from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractIzhikevichVertex(object):

    def __init__(self, n_neurons, a=0.02, c=-65.0, b=0.2, d=2.0, i_offset=0,
                 u_init=-14.0, v_init=-70.0):

        self._a = utility_calls.convert_param_to_numpy(a, n_neurons)
        self._b = utility_calls.convert_param_to_numpy(b, n_neurons)
        self._c = utility_calls.convert_param_to_numpy(c, n_neurons)
        self._d = utility_calls.convert_param_to_numpy(d, n_neurons)
        self._i_offset = utility_calls.convert_param_to_numpy(i_offset,
                                                              n_neurons)
        self._u_init = utility_calls.convert_param_to_numpy(u_init,
                                                            n_neurons)
        self._v_init = utility_calls.convert_param_to_numpy(v_init,
                                                            n_neurons)
        self._atoms = n_neurons

    def initialize_v(self, value):
        self._v_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    def initialize_u(self, value):
        self._u_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    def ioffset(self, machine_time_step):
        return self._i_offset
