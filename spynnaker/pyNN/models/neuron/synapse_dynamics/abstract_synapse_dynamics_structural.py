from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase
from enum import Enum

@add_metaclass(AbstractBase)
class AbstractSynapseDynamicsStructural(object):
    class param(Enum):
        weight = 1
        delay = 2
    __slots__ = []
