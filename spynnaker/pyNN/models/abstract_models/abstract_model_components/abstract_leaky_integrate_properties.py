import numpy

from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractLeakyIntegrateProperties(object):

    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest):
        self._tau_m = utility_calls.convert_param_to_numpy(tau_m, atoms)
        self._cm = utility_calls.convert_param_to_numpy(cm, atoms)
        self._i_offset = utility_calls.convert_param_to_numpy(i_offset, atoms)
        self._atoms = atoms
        self._v_rest = utility_calls.convert_param_to_numpy(v_rest, atoms)

        # if v_init is not set to v_rest then set to v_init
        self._v_init = v_rest
        if v_init is not None:
            self._v_init = \
                utility_calls.convert_param_to_numpy(v_init, atoms)

    def initialize_v(self, value):
        self._v_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    @property
    def ioffset(self):
        return self._i_offset

    @property
    def cm(self):
        return self._cm

    @property
    def v_init(self):
        return self._v_init

    @property
    def tau_m(self):
        return self._tau_m

    @property
    def i_offset(self):
        return self._i_offset

    @property
    def v_rest(self):
        return self._v_reset

    @i_offset.setter
    def i_offset(self, new_value):
        self._i_offset = new_value

    @v_rest.setter
    def v_rest(self, new_value):
        self._v_rest = new_value

    @tau_m.setter
    def tau_m(self, new_value):
        self._tau_m = new_value

    @v_init.setter
    def v_init(self, new_value):
        self._v_init = new_value

    @cm.setter
    def cm(self, new_value):
        self._cm = new_value

    @property
    def _r_membrane(self):
        return self._tau_m / self._cm

    def _exp_tc(self, machine_time_step):
        return numpy.exp(float(-machine_time_step) / (1000.0 * self._tau_m))

    @property
    def _one_over_tau_rc(self):
        return 1.0 / self._tau_m

    @abstractmethod
    def is_leaky_integrate_vertex(self):
        """ helper emthod for is_instance
        :return:
        """
