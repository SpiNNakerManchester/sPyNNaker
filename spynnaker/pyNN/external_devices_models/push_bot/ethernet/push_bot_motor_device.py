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
    PushBotMotor)
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from .push_bot_device import PushBotEthernetDevice


class PushBotEthernetMotorDevice(
        PushBotEthernetDevice, AbstractSendMeMulticastCommandsVertex):
    """
    The motor of a PushBot.
    """

    def __init__(self, motor: PushBotMotor,
                 protocol: MunichIoSpiNNakerLinkProtocol,
                 timesteps_between_send: Optional[int] = None):
        """
        :param motor: indicates which motor to control
        :param protocol:
            The protocol used to control the device
        :param timesteps_between_send:
            The number of timesteps between sending commands to the device,
            or `None` to use the default
        """
        if not isinstance(motor, PushBotMotor):
            raise ConfigurationException(
                "motor parameter must be a PushBotMotor value")

        super().__init__(protocol, motor, True, timesteps_between_send)
        self.__command_protocol = protocol

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
        yield self.__command_protocol.generic_motor_enable()

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        yield self.__command_protocol.generic_motor_disable()

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        return []
