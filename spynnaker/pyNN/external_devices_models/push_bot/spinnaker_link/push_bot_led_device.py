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
    PushBotEthernetLEDDevice)


class PushBotSpiNNakerLinkLEDDevice(
        PushBotEthernetLEDDevice, ApplicationSpiNNakerLinkVertex):
    """ The LED of a PushBot
    """
    __slots__ = []

    default_parameters = {
        'n_neurons': 1, 'label': None, 'board_address': None,
        'start_active_time_front': None, 'start_active_time_back': None,
        'start_total_period': None, 'start_frequency': None}

    def __init__(
            self, led, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address'],
            start_active_time_front=default_parameters[
                'start_active_time_front'],
            start_active_time_back=default_parameters[
                'start_active_time_back'],
            start_total_period=default_parameters['start_total_period'],
            start_frequency=default_parameters['start_frequency']):
        """
        :param led: The LED device to control
        :type led:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotLED
        :param protocol: The protocol instance to get commands from
        :type protocol: ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        :param int spinnaker_link_id: The SpiNNakerLink connected to
        :param int n_neurons: The number of neurons in the device
        :param str label: The label of the device
        :param board_address:
            The IP address of the board that the device is connected to
        :type board_address: str or None
        :param start_active_time_front:
            The "active time" to set for the front LED at the start
        :type start_active_time_front: int or None
        :param start_active_time_back:
            The "active time" to set for the back LED at the start
        :type start_active_time_back: int or None
        :param start_total_period: The "total period" to set at the start
        :type start_total_period: int or None
        :param start_frequency: The "frequency" to set at the start
        :type start_frequency: int or None
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            led, protocol, start_active_time_front, start_active_time_back,
            start_total_period, start_frequency)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
