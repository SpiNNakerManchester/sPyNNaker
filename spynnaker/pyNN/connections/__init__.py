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

from .ethernet_command_connection import EthernetCommandConnection
from .ethernet_control_connection import EthernetControlConnection
from .spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
from .spynnaker_poisson_control_connection import (
    SpynnakerPoissonControlConnection)
from .spif_live_spikes_connection import SPIFLiveSpikesConnection

__all__ = [
    "EthernetCommandConnection", "EthernetControlConnection",
    "SpynnakerLiveSpikesConnection", "SpynnakerPoissonControlConnection",
    "SPIFLiveSpikesConnection"
]
