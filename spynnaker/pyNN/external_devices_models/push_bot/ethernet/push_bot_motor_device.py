# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from .push_bot_device import PushBotEthernetDevice
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotMotor)


class PushBotEthernetMotorDevice(
        PushBotEthernetDevice, AbstractSendMeMulticastCommandsVertex):
    """ The motor of a PushBot
    """

    def __init__(self, motor, protocol, timesteps_between_send=None):
        """
        :param motor: a PushBotMotor value to indicate the motor to control
        :type motor:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotMotor
        :param protocol: The protocol used to control the device
        :type protocol: MunichIoEthernetProtocol
        :param timesteps_between_send:
            The number of timesteps between sending commands to the device,
            or None to use the default
        """

        if not isinstance(motor, PushBotMotor):
            raise ConfigurationException(
                "motor parameter must be a PushBotMotor value")

        super().__init__(protocol, motor, True, timesteps_between_send)
        self.__command_protocol = protocol

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
        commands.append(self.__command_protocol.generic_motor_enable())
        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        return [self.__command_protocol.generic_motor_disable()]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
