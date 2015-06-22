import numpy

from spynnaker.pyNN.utilities import utility_calls
from abstract_leaky_integrate_properties import AbstractLeakyIntegrateProperties
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractIntegrateAndFireProperties(AbstractLeakyIntegrateProperties):

    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest, v_reset,
                 v_thresh, tau_refrac, t_refract_scale=10):
        super(AbstractIntegrateAndFireProperties, self).__init__(v_init, tau_m, cm, i_offset, atoms, v_rest)
        
        self._v_reset = utility_calls.convert_param_to_numpy(v_reset, atoms)
        self._v_thresh = utility_calls.convert_param_to_numpy(v_thresh, atoms)
        self._tau_refrac = utility_calls.convert_param_to_numpy(
            tau_refrac, atoms)
        self._t_refract_scale = t_refract_scale

    def _scaled_t_refract(self):
        return self._tau_refrac * self._t_refract_scale

    @property
    def v_thresh(self):
        return self._v_thresh

    @property
    def _refract_timer(self):
        return 0

    @property
    def tau_refract(self):
        return self._tau_refrac

    @tau_refract.setter
    def tau_refract(self, new_value):
        self._tau_refrac = new_value

    @v_thresh.setter
    def v_thresh(self, new_value):
        self._v_thresh = new_value

    def is_leaky_integrate_vertex(self):
        """

        :return:
        """
        return True

    @abstractmethod
    def is_integrate_and_fire_vertex(self):
        """ helper emthod for is_instance
        :return:
        """
