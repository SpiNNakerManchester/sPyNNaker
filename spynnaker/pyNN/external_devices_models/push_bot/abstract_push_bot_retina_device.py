from spinn_front_end_common.abstract_models.impl \
    import ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.abstract_models \
    import AbstractSendMeMulticastCommandsVertex

from pacman.model.decorators import overrides


class AbstractPushBotRetinaDevice(
        AbstractSendMeMulticastCommandsVertex, ProvidesKeyToAtomMappingImpl):

    def __init__(self, protocol, resolution):
        ProvidesKeyToAtomMappingImpl.__init__(self)
        self._protocol = protocol
        self._resolution = resolution

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):

        commands = list()

        # add mode command if not done already
        if not self._protocol.sent_mode_command():
            commands.append(self._protocol.set_mode())

        # device specific commands
        commands.append(self._protocol.disable_retina())
        commands.append(self._protocol.set_retina_transmission(
            retina_key=self._resolution.value))

        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        commands = list()
        commands.append(self._protocol.disable_retina())
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
