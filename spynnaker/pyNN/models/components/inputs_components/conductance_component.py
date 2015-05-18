"""
AbstractConductanceVertex
"""

from spynnaker.pyNN.models.components.inputs_components.\
    abstract_input_type_component import AbstractInputTypeComponent
from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import hashlib

@add_metaclass(ABCMeta)
class ConductanceComponent(AbstractInputTypeComponent):
    """
    ConductanceComponent the input conductance component
    """

    # Amount by which to scale the weights to maintain accuracy.
    # The weights will be divided by this amount when leaving
    # the current buffer (power of 2 advised)
    WEIGHT_SCALE = 1024.0

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, e_rev_E, e_rev_I):
        AbstractInputTypeComponent.__init__(self)

        self._e_rev_E = utility_calls.convert_param_to_numpy(e_rev_E,
                                                             n_neurons)
        self._e_rev_I = utility_calls.convert_param_to_numpy(e_rev_I,
                                                             n_neurons)

    # noinspection PyPep8Naming
    @property
    def e_rev_E(self):
        """
        property for the e_rev_e
        :return:
        """
        return self._e_rev_E

    # noinspection PyPep8Naming
    @e_rev_E.setter
    def e_rev_E(self, new_value):
        """
        setter for the e_rev_E property
        :param new_value:
        :return:
        """
        self._e_rev_E = new_value

    # noinspection PyPep8Naming
    @property
    def e_rev_I(self):
        """
        e_rev_i property
        :return:
        """
        return self._e_rev_I

    # noinspection PyPep8Naming
    @e_rev_I.setter
    def e_rev_I(self, new_value):
        """
        setter for the e_rev_i property
        :param new_value:
        :return:
        """
        self._e_rev_I = new_value

    def get_input_magic_number(self):
        """
        over loaded from AbstractInputTypeComponent
        :return:
        """
        return [hashlib.md5("0").hexdigest()[:8]]

    @abstractmethod
    def is_conductance(self):
        """helper method for is_instance
        """