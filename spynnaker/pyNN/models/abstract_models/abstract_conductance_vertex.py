from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractConductanceVertex(object):

    # Amount by which to scale the weights to maintain accuracy.
    # The weights will be divided by this amount when leaving
    # the current buffer (power of 2 advised)
    WEIGHT_SCALE = 1024.0

    # noinspection PyPep8Naming
    def __init__(self, n_neurons, e_rev_E, e_rev_I):

        self._e_rev_E = utility_calls.convert_param_to_numpy(e_rev_E,
                                                             n_neurons)
        self._e_rev_I = utility_calls.convert_param_to_numpy(e_rev_I,
                                                             n_neurons)

    # noinspection PyPep8Naming
    @property
    def e_rev_E(self):
        return self._e_rev_E

    # noinspection PyPep8Naming
    @e_rev_E.setter
    def e_rev_E(self, new_value):
        self._e_rev_E = new_value

    # noinspection PyPep8Naming
    @property
    def e_rev_I(self):
        return self._e_rev_I

    # noinspection PyPep8Naming
    @e_rev_I.setter
    def e_rev_I(self, new_value):
        self._e_rev_I = new_value

    @abstractmethod
    def is_conductive(self):
        """helper method for is_instance
        """