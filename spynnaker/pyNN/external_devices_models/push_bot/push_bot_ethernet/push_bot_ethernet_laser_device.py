from pacman.model.decorators import overrides
from spinn_front_end_common.abstract_models \
    import AbstractSendMeMulticastCommandsVertex
from spinn_front_end_common.abstract_models.impl import \
    ProvidesKeyToAtomMappingImpl
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from .push_bot_ethernet_device import PushBotEthernetDevice
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotLaser


class PushBotEthernetLaserDevice(
        AbstractSendMeMulticastCommandsVertex, ProvidesKeyToAtomMappingImpl,
        PushBotEthernetDevice):
    """ The Laser of a PushBot
    """

    def __init__(
            self, laser, protocol,
            start_active_time=None, start_total_period=None,
            start_frequency=None, timesteps_between_send=None):
        """

        :param laser: The PushBotLaser value to control
        :param protocol: The protocol instance to get commands from
        :param start_active_time: The "active time" value to send at the start
        :param start_total_period:\
            The "total period" value to send at the start
        :param start_frequency: The "frequency" to send at the start
        :param timesteps_between_send:\
            The number of timesteps between sending commands to the device,\
            or None to use the default
        """
        if not isinstance(laser, PushBotLaser):
            raise ConfigurationException(
                "laser parameter must be a PushBotLaser value")

        ProvidesKeyToAtomMappingImpl.__init__(self)
        PushBotEthernetDevice.__init__(
            self, protocol, laser, True, timesteps_between_send)

        # protocol specific data items
        self._command_protocol = protocol
        self._start_active_time = start_active_time
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
            commands.append(
                self._command_protocol.push_bot_laser_config_total_period(
                    total_period=self._start_total_period))
        if self._start_active_time is not None:
            commands.append(
                self._command_protocol.push_bot_laser_config_active_time(
                    active_time=self._start_active_time))
        if self._start_frequency is not None:
            commands.append(
                self._command_protocol.push_bot_laser_set_frequency(
                    frequency=self._start_frequency))
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        commands = list()
        commands.append(
            self._command_protocol.push_bot_laser_config_total_period(
                total_period=0))
        commands.append(
            self._command_protocol.push_bot_laser_config_active_time(
                active_time=0))
        commands.append(
            self._command_protocol.push_bot_laser_set_frequency(
                frequency=0))
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
