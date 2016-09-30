from six import add_metaclass
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractSendMeMulticastCommandsVertex(object):
    """ A vertex which wants to commands to be sent to it as multicast packets
        at fixed points in the simulation
    """

    def __init__(self, start_resume_commands, pause_stop_commands,
                 timed_commands):
        """

        :param start_resume_commands: The commands that the vertex expects
        to be transmitted at the start or during a resume
        :param pause_stop_commands: The commands that the vertex expects
        to be transmitted at the pause or stop of a simulation
        :param timed_commands: The commands that the vertex expects
        to be transmitted at times other than start/stop/pause/resume
        :type start_resume_commands: iterable of \
                    py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        :type pause_stop_commands: iterable of \
                    py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        :type timed_commands: iterable of \
                    py:class:`spinn_front_end_common.utility_models.multi_cast_command.MultiCastCommand`
        :raise None: does not raise any known exceptions
        """
        self._start_resume_commands = start_resume_commands
        self._pause_stop_commands = pause_stop_commands
        self._timed_commands = timed_commands

    @property
    def start_resume_commands(self):
        return self._start_resume_commands

    @property
    def pause_stop_commands(self):
        return self._pause_stop_commands

    @property
    def timed_commands(self):
        return self._timed_commands
