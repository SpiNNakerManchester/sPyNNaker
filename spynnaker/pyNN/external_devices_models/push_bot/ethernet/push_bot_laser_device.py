# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Iterable, List

from spinn_utilities.overrides import overrides

from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utility_models import MultiCastCommand

from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotLaser)
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol

from .push_bot_device import PushBotEthernetDevice


class PushBotEthernetLaserDevice(
        PushBotEthernetDevice, AbstractSendMeMulticastCommandsVertex):
    """
    The Laser of a PushBot.
    """

    def __init__(
            self, laser, protocol: MunichIoSpiNNakerLinkProtocol,
            start_active_time=None, start_total_period=None,
            start_frequency=None, timesteps_between_send=None):
        """
        :param PushBotLaser laser: The PushBotLaser value to control
        :param MunichIoEthernetProtocol protocol:
            The protocol instance to get commands from
        :param int start_active_time:
            The "active time" value to send at the start
        :param int start_total_period:
            The "total period" value to send at the start
        :param int start_frequency: The "frequency" to send at the start
        :param int timesteps_between_send:
            The number of timesteps between sending commands to the device,
            or `None` to use the default
        """
        # pylint: disable=too-many-arguments
        if not isinstance(laser, PushBotLaser):
            raise ConfigurationException(
                "laser parameter must be a PushBotLaser value")

        super().__init__(protocol, laser, True, timesteps_between_send)

        # protocol specific data items
        self.__command_protocol = protocol
        self.__start_active_time = start_active_time
        self.__start_total_period = start_total_period
        self.__start_frequency = start_frequency

    @overrides(PushBotEthernetDevice.set_command_protocol)
    def set_command_protocol(
            self, command_protocol: MunichIoSpiNNakerLinkProtocol):
        self.__command_protocol = command_protocol

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self) -> Iterable[MultiCastCommand]:
        # add mode command if not done already
        if not self.protocol.sent_mode_command():
            yield self.protocol.set_mode()

        # device specific commands
        if self.__start_total_period is not None:
            yield self.__command_protocol.push_bot_laser_config_total_period(
                total_period=self.__start_total_period)
        if self.__start_active_time is not None:
            yield self.__command_protocol.push_bot_laser_config_active_time(
                active_time=self.__start_active_time)
        if self.__start_frequency is not None:
            yield self.__command_protocol.push_bot_laser_set_frequency(
                frequency=self.__start_frequency)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        yield self.__command_protocol.push_bot_laser_config_total_period(0)
        yield self.__command_protocol.push_bot_laser_config_active_time(0)
        yield self.__command_protocol.push_bot_laser_set_frequency(0)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        return []
