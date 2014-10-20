from spynnaker.pyNN.utilities import utility_calls
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractConductiveVertex(object):

    def __init__(self, n_neurons, e_rev_e, e_rev_i):

        self._e_rev_e = utility_calls.convert_param_to_numpy(e_rev_e, n_neurons)
        self._e_rev_i = utility_calls.convert_param_to_numpy(e_rev_i, n_neurons)

    @property
    def e_rev_e(self):
        return self._e_rev_e

    @e_rev_e.setter
    def e_rev_e(self, new_value):
        self._e_rev_e = new_value

    @property
    def e_rev_i(self):
        return self._e_rev_i

    @e_rev_i.setter
    def e_rev_i(self, new_value):
        self._e_rev_i = new_value