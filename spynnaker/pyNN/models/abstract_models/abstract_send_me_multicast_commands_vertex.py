from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSendMeMulticastCommandsVertex(object):
    """ A vertex which wants to commands to be sent to it as multicast packets
        at fixed points in the simulation
    """

    def __init__(self, commands):
        """

        :param commands: The commands that the vertex expects to be transmitted
        :type commands: iterable of \
                    py:class:`pacman.utility.multicastcommand.MultiCastCommand`
        :raise None: does not raise any known exceptions
        """
        self._commands = commands

    @property
    def commands(self):
        return self._commands

    @abstractmethod
    def recieves_multicast_commands(self):
        pass
