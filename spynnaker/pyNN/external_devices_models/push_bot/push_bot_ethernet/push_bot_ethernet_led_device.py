from pacman.model.decorators import overrides
from spinn_front_end_common.abstract_models \
    import AbstractSendMeMulticastCommandsVertex
from spinn_front_end_common.abstract_models.impl import \
    ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from .push_bot_ethernet_device import PushBotEthernetDevice
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotLED


class PushBotEthernetLEDDevice(
        AbstractSendMeMulticastCommandsVertex, ProvidesKeyToAtomMappingImpl,
        PushBotEthernetDevice):
    """ The LED of a PushBot
    """

    def __init__(
            self, led, protocol,
            start_active_time_front=None, start_active_time_back=None,
            start_total_period=None, start_frequency=None,
            timesteps_between_send=None):
        """

        :param led: The PushBotLED parameter to control
        :param protocol: The protocol instance to get commands from
        :param start_active_time_front:\
            The "active time" to set for the front LED at the start
        :param start_active_time_back:\
            The "active time" to set for the back LED at the start
        :param start_total_period: The "total period" to set at the start
        :param start_frequency: The "frequency" to set at the start
        :param timesteps_between_send:\
            The number of timesteps between sending commands to the device,\
            or None to use the default
        """
        # pylint: disable=too-many-arguments
        if not isinstance(led, PushBotLED):
            raise ConfigurationException(
                "led parameter must be a PushBotLED value")

        ProvidesKeyToAtomMappingImpl.__init__(self)
        PushBotEthernetDevice.__init__(
            self, protocol, led, True, timesteps_between_send)

        # protocol specific data items
        self._command_protocol = protocol
        self._start_active_time_front = start_active_time_front
        self._start_active_time_back = start_active_time_back
        self._start_total_period = start_total_period
        self._start_frequency = start_frequency

    def set_command_protocol(self, command_protocol):
        self._command_protocol = command_protocol

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        commands = list()

        # add mode command if not done already
        if not self.protocol.sent_mode_command():
            commands.append(self.protocol.set_mode())

        # device specific commands
        if self._start_total_period is not None:
            commands.append(self._command_protocol.push_bot_led_total_period(
                total_period=self._start_total_period))
        if self._start_active_time_front is not None:
            commands.append(
                self._command_protocol.push_bot_led_front_active_time(
                    active_time=self._start_active_time_front))
        if self._start_active_time_back is not None:
            commands.append(
                self._command_protocol.push_bot_led_back_active_time(
                    active_time=self._start_active_time_back))
        if self._start_frequency is not None:
            commands.append(self._command_protocol.push_bot_led_set_frequency(
                frequency=self._start_frequency))
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        commands = list()
        commands.append(self._command_protocol.push_bot_led_front_active_time(
            active_time=0))
        commands.append(self._command_protocol.push_bot_led_back_active_time(
            active_time=0))
        commands.append(self._command_protocol.push_bot_led_total_period(
            total_period=0))
        commands.append(self._command_protocol.push_bot_led_set_frequency(
            frequency=0))
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
