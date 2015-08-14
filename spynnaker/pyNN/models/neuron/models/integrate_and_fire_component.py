from spynnaker.pyNN.models.components.model_components.\
    abstract_model_component import AbstractModelComponent
from spynnaker.pyNN.models.components.model_components.\
    leaky_integrate_component import LeakyIntegrateComponent
from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import hashlib


@add_metaclass(ABCMeta)
class IntegrateAndFireComponent(
        AbstractModelComponent, LeakyIntegrateComponent):
    """ Model component with intergrate and fire properties
    """

    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest, v_reset,
                 v_thresh, tau_refrac):
        AbstractModelComponent.__init__(self)
        LeakyIntegrateComponent.__init__(self, v_init, tau_m, cm, i_offset, 
                                         atoms, v_rest)
        self._v_reset = utility_calls.convert_param_to_numpy(v_reset, atoms)
        self._v_thresh = utility_calls.convert_param_to_numpy(v_thresh, atoms)
        self._tau_refrac = utility_calls.convert_param_to_numpy(
            tau_refrac, atoms)

    @property
    def v_thresh(self):
        return self._v_thresh

    @property
    def tau_refract(self):
        return self._tau_refrac

    @tau_refract.setter
    def tau_refract(self, new_value):
        self._tau_refrac = new_value

    @v_thresh.setter
    def v_thresh(self, new_value):
        self._v_thresh = new_value

    @property
    def _refract_timer(self):
        return 0

    def _tau_refract_timesteps(self, machine_time_step):
        return math.ceil(self._tau_refrac / (machine_time_step / 1000.0))

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

    def get_model_magic_number(self):
        """
        override from AbstractModelComponent
        :return:
        """
        return [hashlib.md5("0").hexdigest()[:8]]