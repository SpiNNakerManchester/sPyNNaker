from .abstract_synapse_dynamics import AbstractSynapseDynamics
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase


@add_metaclass(AbstractBase)
class AbstractSynapseDynamicsStructural(AbstractSynapseDynamics):

    __slots__ = ()

