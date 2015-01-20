import numpy

from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractIntegrateAndFireProperties(object):

    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest, v_reset,
                 v_thresh, tau_refrac, t_refract_scale=10):
        self._tau_m = utility_calls.convert_param_to_numpy(tau_m, atoms)
        self._cm = utility_calls.convert_param_to_numpy(cm, atoms)
        self._i_offset = utility_calls.convert_param_to_numpy(i_offset, atoms)
        self._atoms = atoms
        self._v_rest = utility_calls.convert_param_to_numpy(v_rest, atoms)
        self._v_reset = utility_calls.convert_param_to_numpy(v_reset, atoms)
        self._v_thresh = \
            utility_calls.convert_param_to_numpy(v_thresh, atoms)
        self._tau_refrac = \
            utility_calls.convert_param_to_numpy(tau_refrac, atoms)

        # if v_init is not set to v_rest then set to v_init
        self._v_init = v_rest
        if v_init is not None:
            self._v_init = \
                utility_calls.convert_param_to_numpy(v_init, atoms)
        self._t_refract_scale = t_refract_scale

    def initialize_v(self, value):
        self._v_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    def r_membrane(self, machine_time_step):
        return self._tau_m / self._cm

    def exp_tc(self, machine_time_step):
        return numpy.exp(float(-machine_time_step) / (1000.0 * self._tau_m))

    def ioffset(self, machine_time_step):
        return self._i_offset

    def _scaled_t_refract(self):
        return self._tau_refrac * self._t_refract_scale

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

    @property
    def v_thresh(self):
        return self._v_thresh

    @property
    def _one_over_tau_rc(self):
        return 1.0 / self._tau_m

    @property
    def _refract_timer(self):
        return 0

    @property
    def tau_refract(self):
        return self._tau_refrac

    @i_offset.setter
    def i_offset(self, new_value):
        self._i_offset = new_value

    @v_rest.setter
    def v_rest(self, new_value):
        self._v_rest = new_value

    @tau_refract.setter
    def tau_refract(self, new_value):
        self._tau_refrac = new_value

    @tau_m.setter
    def tau_m(self, new_value):
        self._tau_m = new_value

    @v_thresh.setter
    def v_thresh(self, new_value):
        self._v_thresh = new_value

    @v_init.setter
    def v_init(self, new_value):
        self._v_init = new_value

    @cm.setter
    def cm(self, new_value):
        self._cm = new_value

    @abstractmethod
    def is_integrate_and_fire_vertex(self):
        """ helper emthod for is_instance
        :return:
        """
