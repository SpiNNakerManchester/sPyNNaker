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

from .ethernet_command_connection import EthernetCommandConnection
from .ethernet_control_connection import EthernetControlConnection
from .spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
from .spynnaker_poisson_control_connection import (
    SpynnakerPoissonControlConnection)
from .spif_live_spikes_connection import SPIFLiveSpikesConnection
from .spynnaker_convolution_control_connection import (
    SpynnakerConvolutionControlConnection)

__all__ = [
    "EthernetCommandConnection", "EthernetControlConnection",
    "SpynnakerLiveSpikesConnection", "SpynnakerPoissonControlConnection",
    "SPIFLiveSpikesConnection", "SpynnakerConvolutionControlConnection"
]
