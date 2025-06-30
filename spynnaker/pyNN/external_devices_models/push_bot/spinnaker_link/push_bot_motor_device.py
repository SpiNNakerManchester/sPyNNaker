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

from typing import Optional

from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotMotor)
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    PushBotEthernetMotorDevice)
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol


class PushBotSpiNNakerLinkMotorDevice(
        PushBotEthernetMotorDevice, ApplicationSpiNNakerLinkVertex,
        PopulationApplicationVertex):
    """
    The motor of a PushBot.
    """
    __slots__ = ()

    def __init__(
            self, motor: PushBotMotor, protocol: MunichIoSpiNNakerLinkProtocol,
            spinnaker_link_id: int,  n_neurons: int = 1,
            label: Optional[str] = None,  board_address: Optional[str] = None):
        """
        :param motor: the motor to control
        :param protocol: The protocol used to control the device
        :param spinnaker_link_id: The SpiNNakerLink connected to
        :param n_neurons: The number of neurons in the device
        :param label: The label of the device
        :param board_address:
            The IP address of the board that the device is connected to
        """
        super().__init__(motor, protocol)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
