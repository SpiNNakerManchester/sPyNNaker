from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSendMeMulticastCommandsVertex(object):
    """ A vertex which wants to commands to be sent to it as multicast packets
        at fixed points in the simulation
    """

    def __init__(self, commands, commands_key, commands_mask):
        """

        :param commands: The commands that the vertex expects to be transmitted
        :type commands: iterable of \
                    py:class:`pacman.utility.multicastcommand.MultiCastCommand`
        :param commands_key: A suitable key common between the commands to be\
                    sent
        :type commands_key: int
        :param commands_mask: A suitable mask for the commands, such that\
                    the 1s in the mask that are fixed cover the bits that\
                    are common to all the commands
        :type commands_mask: int
        :raise None: does not raise any known exceptions
        """
        self._commands = commands
        self._commands_key = commands_key
        self._commands_mask = commands_mask

    @property
    def commands(self):
        return self._commands

    @property
    def commands_key(self):
        return self._commands_key

    @property
    def commands_mask(self):
        return self._commands_mask

    @abstractmethod
    def recieves_multicast_commands(self):
        pass
