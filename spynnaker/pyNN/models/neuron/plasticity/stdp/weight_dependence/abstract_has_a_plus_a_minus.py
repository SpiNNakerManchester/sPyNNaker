from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase


@add_metaclass(AbstractBase)
class AbstractHasAPlusAMinus(object):

    __slots__ = [

        # things
        '_a_plus',

        # more things
        '_a_minus'
    ]

    def __init__(self):
        self._a_plus = None
        self._a_minus = None

    def set_a_plus_a_minus(self, a_plus, a_minus):
        self._a_plus = a_plus
        self._a_minus = a_minus

    @property
    def A_plus(self):
        return self._A_plus

    @A_plus.setter
    def A_plus(self, new_value):
        self._a_plus = new_value

    @property
    def A_minus(self):
        return self._A_minus

    @A_minus.setter
    def A_minus(self, new_value):
        self._a_minus = new_value
