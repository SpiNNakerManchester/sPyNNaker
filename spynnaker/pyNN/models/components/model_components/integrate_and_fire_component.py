import numpy
from spynnaker.pyNN.models.components.model_components.\
    abstract_model_component import AbstractModelComponent
from spynnaker.pyNN.utilities import constants

from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class IntegrateAndFireComponent(AbstractModelComponent):
    """
    model component with intergrate and fire properties
    """

    def __init__(self, v_init, tau_m, cm, i_offset, atoms, v_rest, v_reset,
                 v_thresh, tau_refrac, t_refract_scale=10):
        AbstractModelComponent.__init__(self)
        self._tau_m = utility_calls.convert_param_to_numpy(tau_m, atoms)
        self._cm = utility_calls.convert_param_to_numpy(cm, atoms)
        self._i_offset = utility_calls.convert_param_to_numpy(i_offset, atoms)
        self._atoms = atoms
        self._v_rest = utility_calls.convert_param_to_numpy(v_rest, atoms)
        self._v_reset = utility_calls.convert_param_to_numpy(v_reset, atoms)
        self._v_thresh = utility_calls.convert_param_to_numpy(v_thresh, atoms)
        self._tau_refrac = utility_calls.convert_param_to_numpy(
            tau_refrac, atoms)

        # if v_init is not set to v_rest then set to v_init
        self._v_init = v_rest
        if v_init is not None:
            self._v_init = \
                utility_calls.convert_param_to_numpy(v_init, atoms)
        self._t_refract_scale = t_refract_scale

    def _scaled_t_refract(self):
        return self._tau_refrac * self._t_refract_scale

    def initialize_v(self, value):
        """
        function to set up v
        :param value: new value of v
        :return:
        """
        self._v_init = utility_calls.convert_param_to_numpy(value, self._atoms)

    def r_membrane(self, machine_time_step):
        """
        property for the r_membrane
        :param machine_time_step:
        :return:
        """
        utility_calls.unused(machine_time_step)
        return self._tau_m / self._cm

    def exp_tc(self, machine_time_step):
        """
        property for exp_tc
        :param machine_time_step:
        :return:
        """
        return numpy.exp(float(-machine_time_step) / (1000.0 * self._tau_m))

    def ioffset(self, machine_time_step):
        """
        property
        :param machine_time_step:
        :return:
        """
        utility_calls.unused(machine_time_step)
        return self._i_offset

    @property
    def cm(self):
        """
        property
        :return:
        """
        return self._cm

    @property
    def v_init(self):
        """
        property
        :return:
        """
        return self._v_init

    @property
    def tau_m(self):
        """
        property
        :return:
        """
        return self._tau_m

    @property
    def i_offset(self):
        """
        property
        :return:
        """
        return self._i_offset

    @property
    def v_rest(self):
        """
        property
        :return:
        """
        return self._v_reset

    @property
    def v_thresh(self):
        """
        property
        :return:
        """
        return self._v_thresh

    @property
    def _one_over_tau_rc(self):
        """
        property
        :return:
        """
        return 1.0 / self._tau_m

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

    @i_offset.setter
    def i_offset(self, new_value):
        """
        setter for the i_ofsert propwerty
        :param new_value:
        :return:
        """
        self._i_offset = new_value

    @v_rest.setter
    def v_rest(self, new_value):
        """
        setter for the v_rest property
        :param new_value:
        :return:
        """
        self._v_rest = new_value

    @tau_refract.setter
    def tau_refract(self, new_value):
        """
        setter for the tau_refact property
        :param new_value:
        :return:
        """
        self._tau_refrac = new_value

    @tau_m.setter
    def tau_m(self, new_value):
        """
        the setter for the tau_m property
        :param new_value:
        :return:
        """
        self._tau_m = new_value

    @v_thresh.setter
    def v_thresh(self, new_value):
        """
        setter for the v_thresh property
        :param new_value:
        :return:
        """
        self._v_thresh = new_value

    @v_init.setter
    def v_init(self, new_value):
        """
        setter for the v_init property
        :param new_value:
        :return:
        """
        self._v_init = new_value

    @cm.setter
    def cm(self, new_value):
        """
        setter for the cm property
        :param new_value:
        :return:
        """
        self._cm = new_value

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