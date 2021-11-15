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
    PushBotEthernetMotorDevice)


class PushBotSpiNNakerLinkMotorDevice(
        PushBotEthernetMotorDevice, ApplicationSpiNNakerLinkVertex):
    """ The motor of a PushBot
    """
    __slots__ = []

    default_parameters = {
        'n_neurons': 1,
        'label': None,
        'board_address': None}

    def __init__(
            self, motor, protocol, spinnaker_link_id,
            n_neurons=default_parameters['n_neurons'],
            label=default_parameters['label'],
            board_address=default_parameters['board_address']):
        """
        :param motor: the motor to control
        :type motor:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotMotor
        :param protocol: The protocol used to control the device
        :type protocol: ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        :param int spinnaker_link_id: The SpiNNakerLink connected to
        :param int n_neurons: The number of neurons in the device
        :param str label: The label of the device
        :param board_address:
            The IP address of the board that the device is connected to
        :type board_address: str or None
        """
        # pylint: disable=too-many-arguments
        super().__init__(motor, protocol)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id, n_atoms=n_neurons,
            board_address=board_address, label=label)
