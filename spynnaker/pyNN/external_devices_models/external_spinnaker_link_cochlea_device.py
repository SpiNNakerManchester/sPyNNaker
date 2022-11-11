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
from spynnaker.pyNN.models.common import PopulationApplicationVertex


class ExternalCochleaDevice(
        ApplicationSpiNNakerLinkVertex, PopulationApplicationVertex):
    __slots__ = []

    def __init__(
            self, n_neurons, spinnaker_link, label=None, board_address=None):
        """
        :param int n_neurons: Number of neurons
        :param int spinnaker_link:
            The SpiNNaker link to which the cochlea is connected
        :param str label:
        :param str board_address:
        """
        super().__init__(
            n_atoms=n_neurons, spinnaker_link_id=spinnaker_link,
            label=label, board_address=board_address)
