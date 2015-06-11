"""
LeakyIntegrateComponent
"""
import numpy

from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class LeakyIntegrateComponent(object):
    """
    LeakyIntegrateComponent. base class for all leaky intergrators.
    """

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
        """
        setter for v_init
        :param value: the new value for v_init
        :return: a v_init
        """
        self._v_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    def r_membrane(self, machine_time_step):
        """
        calcualtes the r_membrane for this model given a machine time step
        :param machine_time_step:
        :return: a r_membrane
        """
        utility_calls.unused(machine_time_step)
        return self._tau_m / self._cm

    def exp_tc(self, machine_time_step):
        """
        calculates the exp_tc for this model given a machine time step
        :param machine_time_step:
        :return: a exp_tc
        """
        return numpy.exp(float(-machine_time_step) / (1000.0 * self._tau_m))

    def ioffset(self, machine_time_step):
        """
        returns this models ioffset given a machine time step
        :param machine_time_step:
        :return: a ioffset
        """
        utility_calls.unused(machine_time_step)
        return self._i_offset

    @property
    def cm(self):
        """
        property for cm
        :return: cm
        """
        return self._cm

    @property
    def v_init(self):
        """
        property for v_init
        :return: v_init
        """
        return self._v_init

    @property
    def tau_m(self):
        """
        property for tau_m
        :return: tau_m
        """
        return self._tau_m

    @property
    def i_offset(self):
        """
        property for i_offset
        :return: i_offset
        """
        return self._i_offset

    @property
    def v_rest(self):
        """
        property for v_rest
        :return: v_rest
        """
        return self._v_reset

    @property
    def _one_over_tau_rc(self):
        return 1.0 / self._tau_m
    
    @i_offset.setter
    def i_offset(self, new_value):
        """
        setter for i_offsert
        :param new_value:  the new value of i_offset
        :return: none
        """
        self._i_offset = new_value

    @v_rest.setter
    def v_rest(self, new_value):
        """
        setter for v-rest
        :param new_value: the new value of V-rest
        :return: None
        """
        self._v_rest = new_value

    @tau_m.setter
    def tau_m(self, new_value):
        """
        setter for tau_m
        :param new_value: the new value of tau_m
        :return: none
        """
        self._tau_m = new_value

    @v_init.setter
    def v_init(self, new_value):
        """
        setter for v_init
        :param new_value: the new value of v_init
        :return: none
        """
        self._v_init = new_value

    @cm.setter
    def cm(self, new_value):
        """
        setter for cm
        :param new_value: new value for cm
        :return: None
        """
        self._cm = new_value

    @abstractmethod
    def is_leaky_integrate_vertex(self):
        """ helper emthod for is_instance
        :return:
        """
