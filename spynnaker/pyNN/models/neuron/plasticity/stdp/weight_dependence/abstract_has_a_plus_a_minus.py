from six import with_metaclass
from spinn_utilities.abstract_base import AbstractBase


class AbstractHasAPlusAMinus(with_metaclass(AbstractBase, object)):
    __slots__ = [
        # things
        '__a_plus',
        # more things
        '__a_minus'
    ]

    def __init__(self):
        self.__a_plus = None
        self.__a_minus = None

    def set_a_plus_a_minus(self, a_plus, a_minus):
        self.__a_plus = a_plus
        self.__a_minus = a_minus

    @property
    def A_plus(self):
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value):
        self.__a_plus = new_value

    @property
    def A_minus(self):
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value):
        self.__a_minus = new_value
