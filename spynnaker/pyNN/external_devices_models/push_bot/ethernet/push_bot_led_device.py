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

from typing import Iterable, List, Optional

from spinn_utilities.overrides import overrides

from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utility_models import MultiCastCommand

from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotLED)
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol

from .push_bot_device import PushBotEthernetDevice


class PushBotEthernetLEDDevice(
        PushBotEthernetDevice, AbstractSendMeMulticastCommandsVertex):
    """
    The LED of a PushBot.
    """

    def __init__(
            self, led: PushBotLED, protocol: MunichIoSpiNNakerLinkProtocol,
            start_active_time_front: Optional[int] = None,
            start_active_time_back: Optional[int] = None,
            start_total_period: Optional[int] = None,
            start_frequency: Optional[int] = None,
            timesteps_between_send: Optional[int] = None):
        """
        :param led: The LED to control
        :param protocol:
            The protocol instance to get commands from
        :param start_active_time_front:
            The "active time" to set for the front LED at the start
        :param start_active_time_back:
            The "active time" to set for the back LED at the start
        :param start_total_period: The "total period" to set at the start
        :param start_frequency: The "frequency" to set at the start
        :param timesteps_between_send:
            The number of timesteps between sending commands to the device,
            or `None` to use the default
        """
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
    def set_command_protocol(
            self, command_protocol: MunichIoSpiNNakerLinkProtocol) -> None:
        self.__command_protocol = command_protocol

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self) -> Iterable[MultiCastCommand]:
        # add mode command if not done already
        if not self.protocol.sent_mode_command():
            yield self.protocol.set_mode()

        # device specific commands
        if self.__start_total_period is not None:
            yield self.__command_protocol.push_bot_led_total_period(
                self.__start_total_period)
        if self.__start_active_time_front is not None:
            yield self.__command_protocol.push_bot_led_front_active_time(
                self.__start_active_time_front)
        if self.__start_active_time_back is not None:
            yield self.__command_protocol.push_bot_led_back_active_time(
                self.__start_active_time_back)
        if self.__start_frequency is not None:
            yield self.__command_protocol.push_bot_led_set_frequency(
                self.__start_frequency)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        yield self.__command_protocol.push_bot_led_front_active_time(0)
        yield self.__command_protocol.push_bot_led_back_active_time(0)
        yield self.__command_protocol.push_bot_led_total_period(0)
        yield self.__command_protocol.push_bot_led_set_frequency(0)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        return []
