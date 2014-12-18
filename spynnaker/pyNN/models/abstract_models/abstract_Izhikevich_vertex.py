from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

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

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, new_value):
        self._a = new_value

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, new_value):
        self._b = new_value

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, new_value):
        self._c = new_value

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, new_value):
        self._d = new_value

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, new_value):
        self._i_offset = new_value

    @property
    def u_init(self):
        return self._u_init

    @u_init.setter
    def u_init(self, new_value):
        self._u_init = new_value

    @property
    def v_init(self):
        return self._v_init

    @v_init.setter
    def v_init(self, new_value):
        self._v_init = new_value

    @abstractmethod
    def is_izhikevich_vertex(self):
        """ helper method for is_instance

        :return:
        """
