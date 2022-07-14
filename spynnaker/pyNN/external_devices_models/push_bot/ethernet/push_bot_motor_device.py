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
