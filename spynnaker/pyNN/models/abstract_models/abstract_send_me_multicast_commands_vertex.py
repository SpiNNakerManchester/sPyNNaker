from six import add_metaclass
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractSendMeMulticastCommandsVertex(object):
    """ A vertex which wants to commands to be sent to it as multicast packets
        at fixed points in the simulation

        :param commands: The commands that the vertex expects to be transmitted

            iterable of\
                    py:class:`spinn_front_end_common.utility_models.\
                    multi_cast_command.MultiCastCommand`
    """

    def __init__(self, commands):
        self._commands = commands

    @property
    def commands(self):
        return self._commands
