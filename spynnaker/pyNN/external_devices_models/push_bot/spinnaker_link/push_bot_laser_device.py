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

from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    PushBotEthernetLaserDevice)
from spynnaker.pyNN.models.common import PopulationApplicationVertex


class PushBotSpiNNakerLinkLaserDevice(
        PushBotEthernetLaserDevice, ApplicationSpiNNakerLinkVertex,
        PopulationApplicationVertex):
    """
    The Laser of a PushBot.
    """
    __slots__ = []

    default_parameters = {
        'n_neurons': 1, 'label': None, 'board_address': None,
        'start_active_time': 0, 'start_total_period': 0, 'start_frequency': 0}

    def __init__(
            self, laser, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address'],
            start_active_time=default_parameters['start_active_time'],
            start_total_period=default_parameters['start_total_period'],
            start_frequency=default_parameters['start_frequency']):
        """
        :param laser: Which laser device to control
        :type laser:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotLaser
        :param protocol: The protocol instance to get commands from
        :type protocol: ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        :param int spinnaker_link_id:
            The SpiNNakerLink that the PushBot is connected to
        :param int n_neurons: The number of neurons in the device
        :param str label: A label for the device
        :param board_address:
            The IP address of the board that the device is connected to
        :type board_address: str or None
        :param int start_active_time:
            The "active time" value to send at the start
        :param int start_total_period:
            The "total period" value to send at the start
        :param int start_frequency: The "frequency" to send at the start
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            laser, protocol, start_active_time,
            start_total_period, start_frequency)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
