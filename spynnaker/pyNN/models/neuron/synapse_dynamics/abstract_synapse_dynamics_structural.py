from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from enum import Enum


@add_metaclass(AbstractBase)
class AbstractSynapseDynamicsStructural(object):
    class connectivity_exception_param(Enum):
        weight = 1
        delay = 2
    __slots__ = []

    @abstractproperty
    def partner_selection(self):
        """ The partner selection rule
        """

    @abstractproperty
    def formation(self):
        """ The formation rule
        """

    def elimination(self):
        """ The elimination rule
        """
