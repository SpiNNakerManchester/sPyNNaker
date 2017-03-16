from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

@add_metaclass(AbstractBase)
class AbstractSendMeMulticastCommandsVertex(object):
    """ A vertex which wants to commands to be sent to it as multicast packets
        at fixed points in the simulation
    """

    def __init__(self, commands):
        """

        :param commands: The commands that the vertex expects to be transmitted
        :type commands: iterable of \
                    py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        """
        self._commands = commands

    @property
    def commands(self):
        return self._commands
