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

from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    PushBotEthernetSpeakerDevice)


class PushBotSpiNNakerLinkSpeakerDevice(
        PushBotEthernetSpeakerDevice, ApplicationSpiNNakerLinkVertex):
    """ The speaker of a PushBot
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
