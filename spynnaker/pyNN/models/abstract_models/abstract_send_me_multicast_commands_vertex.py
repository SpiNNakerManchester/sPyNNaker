from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty


@add_metaclass(AbstractBase)
class AbstractSendMeMulticastCommandsVertex(object):
    """ A vertex which wants to commands to be sent to it as multicast packets
        at fixed points in the simulation
    """

    __slots__ = ()

    @abstractproperty
    def commands(self):
        """ The commands to be sent
        """
        pass
