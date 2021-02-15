# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from .push_bot_device import PushBotEthernetDevice
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotLED)


class PushBotEthernetLEDDevice(
        PushBotEthernetDevice, AbstractSendMeMulticastCommandsVertex,
        ProvidesKeyToAtomMappingImpl):
    """ The LED of a PushBot
    """

    def __init__(
            self, led, protocol,
            start_active_time_front=None, start_active_time_back=None,
            start_total_period=None, start_frequency=None,
            timesteps_between_send=None):
        """
        :param led: The PushBotLED parameter to control
        :type led:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotLED
        :param protocol: The protocol instance to get commands from
        :type protocol: MunichIoEthernetProtocol
        :param start_active_time_front:
            The "active time" to set for the front LED at the start
        :param start_active_time_back:
            The "active time" to set for the back LED at the start
        :param start_total_period: The "total period" to set at the start
        :param start_frequency: The "frequency" to set at the start
        :param timesteps_between_send:
            The number of timesteps between sending commands to the device,\
            or None to use the default
        """
        # pylint: disable=too-many-arguments
        if not isinstance(led, PushBotLED):
            raise ConfigurationException(
                "led parameter must be a PushBotLED value")

        super().__init__(protocol, led, True, timesteps_between_send)

        # protocol specific data items
        self.__command_protocol = protocol
        self.__start_active_time_front = start_active_time_front
        self.__start_active_time_back = start_active_time_back
        self.__start_total_period = start_total_period
        self.__start_frequency = start_frequency

    @overrides(PushBotEthernetDevice.set_command_protocol)
    def set_command_protocol(self, command_protocol):
        self.__command_protocol = command_protocol

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        commands = list()

        # add mode command if not done already
        if not self.protocol.sent_mode_command():
            commands.append(self.protocol.set_mode())

        # device specific commands
        if self.__start_total_period is not None:
            commands.append(self.__command_protocol.push_bot_led_total_period(
                self.__start_total_period))
        if self.__start_active_time_front is not None:
            commands.append(
                self.__command_protocol.push_bot_led_front_active_time(
                    self.__start_active_time_front))
        if self.__start_active_time_back is not None:
            commands.append(
                self.__command_protocol.push_bot_led_back_active_time(
                    self.__start_active_time_back))
        if self.__start_frequency is not None:
            commands.append(self.__command_protocol.push_bot_led_set_frequency(
                self.__start_frequency))
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        return [
            self.__command_protocol.push_bot_led_front_active_time(0),
            self.__command_protocol.push_bot_led_back_active_time(0),
            self.__command_protocol.push_bot_led_total_period(0),
            self.__command_protocol.push_bot_led_set_frequency(0)]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
