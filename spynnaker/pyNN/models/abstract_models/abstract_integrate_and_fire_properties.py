import numpy

from spynnaker.pyNN.utilities import utility_calls


class AbstractIntegrateAndFireProperties(object):
    
    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest, v_reset,
                 v_thresh, tau_refrac, t_refract_scale=10):
        self._tau_m = tau_m
        self._cm = cm
        self._i_offset = i_offset
        self._atoms = atoms
        self._v_rest = utility_calls.convert_param_to_numpy(v_rest, atoms)
        self._v_reset = utility_calls.convert_param_to_numpy(v_reset, atoms)
        self._v_thresh = \
            utility_calls.convert_param_to_numpy(v_thresh, atoms)
        self._tau_refrac = \
            utility_calls.convert_param_to_numpy(tau_refrac, atoms)
        #if v_init is not set to v_rest then set to v_init
        self._v_init = v_rest
        if v_init is not None:
            self._v_init = \
                utility_calls.convert_param_to_numpy(v_init, atoms)
        self._t_refract_scale = t_refract_scale

    def initialize_v(self, value):
        self._v_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    def r_membrane(self, machine_time_step):
        return ((1000.0 * self._tau_m) 
                / (self._cm * float(machine_time_step)))

    def exp_tc(self, machine_time_step):
        return numpy.exp(float(-machine_time_step) / (1000.0 * self._tau_m))
        
    def ioffset(self, machine_time_step):
        return self._i_offset / (1000.0 / float(machine_time_step))

    def scaled_t_refract(self):
        return self._tau_refrac * self._t_refract_scale

    @property
    def cm(self):
        return self._cm

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
    def one_over_tau_rc(self):
        return 1.0 / self._tau_m

    @property
    def refract_timer(self):
        return 0

    @property
    def t_refract(self):
        return self._tau_refrac
