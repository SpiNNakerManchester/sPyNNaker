import numpy
from spynnaker.pyNN.models.components.model_components.\
    abstract_model_component import AbstractModelComponent
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.components.model_components.\
    leaky_integrate_component.LeakyIntegrateComponent
from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class IntegrateAndFireComponent(
        AbstractModelComponent, LeakyIntegrateComponent):
    """
    model component with intergrate and fire properties
    """

    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest, v_reset,
                 v_thresh, tau_refrac, t_refract_scale=10):
        AbstractModelComponent.__init__(self)
        LeakyIntegrateComponent.__init__(self, v_init, tau_m, cm, i_offset, 
                                         atoms, v_rest)
        self._v_reset = utility_calls.convert_param_to_numpy(v_reset, atoms)
        self._v_thresh = utility_calls.convert_param_to_numpy(v_thresh, atoms)
        self._tau_refrac = utility_calls.convert_param_to_numpy(
            tau_refrac, atoms)
        self._t_refract_scale = t_refract_scale

    def _scaled_t_refract(self):
        return self._tau_refrac * self._t_refract_scale

    @property
    def v_thresh(self):
        """
        property
        :return:
        """
        return self._v_thresh

    @property
    def _refract_timer(self):
        """
        property
        :return:
        """
        return 0

    @property
    def tau_refract(self):
        """
        property
        :return:
        """
        return self._tau_refrac

    @tau_refract.setter
    def tau_refract(self, new_value):
        """
        setter for the tau_refact property
        :param new_value:
        :return:
        """
        self._tau_refrac = new_value

    @v_thresh.setter
    def v_thresh(self, new_value):
        """
        setter for the v_thresh property
        :param new_value:
        :return:
        """
        self._v_thresh = new_value

    def is_leaky_integrate_vertex(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    @abstractmethod
    def is_integrate_and_fire_vertex(self):
        """ helper emthod for is_instance
        :return:
        """

    def get_model_magic_number(self):
        """
        override from AbstractModelComponent
        :return:
        """
        return constants.MODEL_COMPONENT_INTEGRATE_AND_FIRE_MAGIC_NUMBER