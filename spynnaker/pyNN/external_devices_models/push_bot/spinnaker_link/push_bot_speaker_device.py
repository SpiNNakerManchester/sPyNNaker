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
    PushBotEthernetSpeakerDevice)
from spynnaker.pyNN.models.common import PopulationApplicationVertex


class PushBotSpiNNakerLinkSpeakerDevice(
        PushBotEthernetSpeakerDevice, ApplicationSpiNNakerLinkVertex,
        PopulationApplicationVertex):
    """
    The speaker of a PushBot.
    """
    __slots__ = []

    default_parameters = {
        'n_neurons': 1, 'label': None,
        'board_address': None,
        'start_active_time': 50,
        'start_total_period': 100,
        'start_frequency': None,
        'start_melody': None}

    def __init__(
            self, speaker, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address'],
            start_active_time=default_parameters['start_active_time'],
            start_total_period=default_parameters['start_total_period'],
            start_frequency=default_parameters['start_frequency'],
            start_melody=default_parameters['start_melody']):
        """
        :param speaker: Which speaker device to control
        :type speaker:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotSpeaker
        :param protocol: The protocol instance to get commands from
        :type protocol: ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        :param int spinnaker_link_id: The SpiNNakerLink connected to
        :param int n_neurons: The number of neurons in the device
        :param str label: The label of the device
        :param board_address:
            The IP address of the board that the device is connected to
        :type board_address: str or None
        :param start_active_time: The "active time" to set at the start
        :param start_total_period: The "total period" to set at the start
        :param start_frequency: The "frequency" to set at the start
        :param start_melody: The "melody" to set at the start
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            speaker, protocol, start_active_time, start_total_period,
            start_frequency, start_melody)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
